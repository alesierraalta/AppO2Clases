"""
Módulo para exportar tablas de base de datos SQLite a archivos Excel.
Proporciona funcionalidad para exportar todas las tablas con protección configurable
de datos sensibles (teléfonos y correos electrónicos).

Autor: Sistema de Gestión de Clases O2
Fecha: 2025
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime
import re
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Definir columnas sensibles por tabla
SENSITIVE_COLUMNS = {
    'profesor': ['telefono', 'email']
}

# Niveles de protección disponibles
PROTECTION_LEVELS = ['completa', 'parcial', 'ninguna']


def mask_sensitive_data(value, protection_level, data_type='auto'):
    """
    Enmascara datos sensibles según el nivel de protección especificado.
    
    Args:
        value: Valor a enmascarar (puede ser str, None, o NaN)
        protection_level (str): Nivel de protección ('completa', 'parcial', 'ninguna')
        data_type (str): Tipo de dato ('phone', 'email', 'auto' para detectar automáticamente)
        
    Returns:
        str: Valor enmascarado o el original si no requiere protección
    """
    # Si el nivel es 'ninguna', retornar sin modificar
    if protection_level == 'ninguna':
        return value
    
    # Manejar valores None, NaN o vacíos
    if value is None or pd.isna(value) or str(value).strip() == '':
        return value
    
    # Convertir a string para procesamiento
    value_str = str(value).strip()
    
    # Detectar tipo de dato automáticamente si es necesario
    if data_type == 'auto':
        # Detectar email (contiene @)
        if '@' in value_str:
            data_type = 'email'
        # Detectar teléfono (solo números, guiones, espacios, paréntesis)
        elif re.match(r'^[\d\s\-\(\)\+]+$', value_str.replace(' ', '')):
            data_type = 'phone'
        else:
            # No reconocido, retornar sin modificar
            return value
    
    # Aplicar protección completa
    if protection_level == 'completa':
        return '***'
    
    # Aplicar protección parcial
    elif protection_level == 'parcial':
        if data_type == 'email':
            # Email parcial: mostrar primer carácter + *** + dominio
            # Ejemplo: "usuario@example.com" -> "u***@example.com"
            if '@' in value_str:
                local_part, domain = value_str.split('@', 1)
                if len(local_part) > 0:
                    masked_local = local_part[0] + '***'
                else:
                    masked_local = '***'
                return f"{masked_local}@{domain}"
            else:
                return '***'
        
        elif data_type == 'phone':
            # Teléfono parcial: mostrar últimos 4 dígitos
            # Ejemplo: "1234567890" -> "***-***-7890"
            # Limpiar el teléfono (solo números)
            digits_only = re.sub(r'\D', '', value_str)
            
            if len(digits_only) >= 4:
                last_four = digits_only[-4:]
                # Formatear como ***-***-XXXX si tiene más de 4 dígitos
                if len(digits_only) > 4:
                    return f"***-***-{last_four}"
                else:
                    return f"***{last_four}"
            else:
                # Si tiene menos de 4 dígitos, ocultar completamente
                return '***'
    
    # Nivel no reconocido, retornar sin modificar
    return value


def apply_data_protection(df, table_name, protection_level):
    """
    Aplica protección de datos sensibles a un DataFrame según el nivel especificado.
    
    Args:
        df (pandas.DataFrame): DataFrame con los datos a proteger
        table_name (str): Nombre de la tabla (para identificar columnas sensibles)
        protection_level (str): Nivel de protección ('completa', 'parcial', 'ninguna')
        
    Returns:
        pandas.DataFrame: DataFrame con datos protegidos
    """
    # Si no hay nivel de protección o no es aplicable, retornar sin modificar
    if protection_level == 'ninguna' or table_name not in SENSITIVE_COLUMNS:
        return df
    
    # Crear copia para no modificar el original
    df_protected = df.copy()
    
    # Obtener columnas sensibles para esta tabla
    sensitive_cols = SENSITIVE_COLUMNS.get(table_name, [])
    
    # Aplicar protección a cada columna sensible
    for col in sensitive_cols:
        if col in df_protected.columns:
            # Determinar tipo de dato (teléfono o email)
            if col == 'telefono':
                data_type = 'phone'
            elif col == 'email':
                data_type = 'email'
            else:
                data_type = 'auto'
            
            # Aplicar función de enmascaramiento a toda la columna
            df_protected[col] = df_protected[col].apply(
                lambda x: mask_sensitive_data(x, protection_level, data_type)
            )
    
    return df_protected


def get_table_names(db_path):
    """
    Obtiene la lista de nombres de tablas de una base de datos SQLite.
    
    Args:
        db_path (str): Ruta al archivo de base de datos SQLite
        
    Returns:
        list: Lista de nombres de tablas
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Consulta para obtener todas las tablas (excluye tablas del sistema)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return tables
    except Exception as e:
        logger.error(f"Error al obtener lista de tablas: {str(e)}")
        raise


def export_tables_to_excel(db_path, output_dir='backups', protection_level='completa', 
                          create_unified=True, create_individual=True):
    """
    Exporta todas las tablas de una base de datos SQLite a archivos Excel.
    
    Esta función permite exportar tablas individuales y/o un archivo unificado,
    con protección configurable de datos sensibles (teléfonos y correos electrónicos).
    
    Args:
        db_path (str): Ruta al archivo de base de datos SQLite
        output_dir (str): Directorio donde se guardarán los archivos Excel (por defecto: 'backups')
        protection_level (str): Nivel de protección de datos sensibles. Opciones:
            - 'completa': Oculta completamente los datos sensibles (***)
            - 'parcial': Muestra parcialmente los datos (ej: ***-***-1234 para teléfonos)
            - 'ninguna': No aplica protección
        create_unified (bool): Si True, crea un archivo Excel con todas las tablas en hojas separadas
        create_individual (bool): Si True, crea un archivo Excel por cada tabla
    
    Returns:
        dict: Diccionario con información de la exportación. Formato:
            {
                'tabla1': {'row_count': int, 'file_path': str},
                'tabla2': {'row_count': int, 'file_path': str},
                ...
                'completo': {'file_path': str}  # Solo si create_unified=True
            }
    
    Raises:
        FileNotFoundError: Si el archivo de base de datos no existe
        ValueError: Si el nivel de protección no es válido
        Exception: Para otros errores durante la exportación
    """
    # Validar nivel de protección
    if protection_level not in PROTECTION_LEVELS:
        raise ValueError(f"Nivel de protección inválido: {protection_level}. "
                        f"Valores permitidos: {PROTECTION_LEVELS}")
    
    # Verificar que el archivo de base de datos existe
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"El archivo de base de datos no existe: {db_path}")
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Generar timestamp para nombres de archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Obtener lista de tablas de la base de datos
    try:
        tables = get_table_names(db_path)
    except Exception as e:
        logger.error(f"Error al obtener lista de tablas: {str(e)}")
        raise
    
    if not tables:
        logger.warning("No se encontraron tablas en la base de datos")
        return {}
    
    # Crear conexión SQLite para pandas
    conn = sqlite3.connect(db_path)
    
    # Diccionario de resultados
    resultados = {}
    
    # Lista de DataFrames para archivo unificado
    unified_dataframes = []
    
    try:
        # Procesar cada tabla
        for table_name in tables:
            try:
                # Leer tabla completa desde SQLite
                query = f"SELECT * FROM {table_name}"
                df = pd.read_sql(query, conn)
                
                # Obtener conteo de filas antes de proteger
                row_count = len(df)
                
                # Aplicar protección de datos sensibles
                df_protected = apply_data_protection(df, table_name, protection_level)
                
                # Guardar DataFrame para archivo unificado
                unified_dataframes.append((table_name, df_protected))
                
                # Crear archivo individual si está habilitado
                file_path = None
                if create_individual:
                    # Nombre de archivo para tabla individual
                    filename = f"{table_name}_{timestamp}.xlsx"
                    file_path = os.path.join(output_dir, filename)
                    
                    # Exportar a Excel
                    df_protected.to_excel(
                        file_path,
                        index=False,
                        engine='openpyxl',
                        sheet_name=table_name[:31]  # Excel limita nombres de hojas a 31 caracteres
                    )
                    
                    logger.info(f"Tabla '{table_name}' exportada a {file_path} ({row_count} registros)")
                
                # Guardar información en resultados (siempre incluir row_count y file_path)
                resultados[table_name] = {
                    'row_count': row_count,
                    'file_path': file_path  # Será None si create_individual=False
                }
            
            except Exception as e:
                logger.error(f"Error al exportar tabla '{table_name}': {str(e)}")
                # Continuar con las demás tablas aunque una falle
                resultados[table_name] = {
                    'row_count': 0,
                    'file_path': None,
                    'error': str(e)
                }
        
        # Crear archivo unificado si está habilitado
        if create_unified and unified_dataframes:
            filename_unified = f"exportacion_completa_{timestamp}.xlsx"
            file_path_unified = os.path.join(output_dir, filename_unified)
            
            # Crear ExcelWriter para múltiples hojas
            with pd.ExcelWriter(file_path_unified, engine='openpyxl') as writer:
                for table_name, df in unified_dataframes:
                    # Limitar nombre de hoja a 31 caracteres (límite de Excel)
                    sheet_name = table_name[:31]
                    df.to_excel(
                        writer,
                        sheet_name=sheet_name,
                        index=False
                    )
            
            logger.info(f"Archivo unificado creado: {file_path_unified}")
            
            # Agregar información del archivo unificado a resultados
            resultados['completo'] = {
                'file_path': file_path_unified
            }
    
    finally:
        # Cerrar conexión a la base de datos
        conn.close()
    
    return resultados

