#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir el esquema de la base de datos, específicamente el problema
de la columna 'activo' faltante en la tabla horario_clase.

Este script realiza las siguientes acciones:
1. Verifica el esquema actual de la base de datos
2. Hace una copia de seguridad de la base de datos
3. Repara la tabla horario_clase asegurándose de que tiene la columna 'activo'
4. Verifica que la reparación fue exitosa
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Configuración
DB_FILE = "gimnasio.db"
BACKUP_DIR = "backups"
TABLE_NAME = "horario_clase"
REQUIRED_COLUMNS = ["activo", "fecha_desactivacion"]

def crear_backup():
    """Crea una copia de seguridad de la base de datos"""
    if not os.path.exists(DB_FILE):
        print(f"ERROR: No se encontró la base de datos {DB_FILE}")
        return False
        
    # Crear directorio de backups si no existe
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    # Nombre del archivo de backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"gimnasio_backup_{timestamp}.db")
    
    # Copiar archivo
    try:
        shutil.copy2(DB_FILE, backup_file)
        print(f"✓ Backup creado: {backup_file}")
        return True
    except Exception as e:
        print(f"ERROR al crear backup: {str(e)}")
        return False

def verificar_esquema():
    """Verifica el esquema actual de la tabla horario_clase"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,))
        if not cursor.fetchone():
            print(f"ERROR: La tabla {TABLE_NAME} no existe en la base de datos")
            conn.close()
            return False, {}
            
        # Obtener información de columnas
        cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
        columns_info = cursor.fetchall()
        column_names = [col[1] for col in columns_info]
        
        # Crear diccionario con la información completa de cada columna
        columns_data = {}
        for col in columns_info:
            # (cid, name, type, notnull, dflt_value, pk)
            columns_data[col[1]] = {
                "id": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "default": col[4],
                "primary_key": col[5]
            }
        
        conn.close()
        
        # Verificar columnas requeridas
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in column_names]
        if missing_columns:
            print(f"Columnas faltantes: {', '.join(missing_columns)}")
            return False, columns_data
        else:
            print(f"✓ Todas las columnas requeridas existen en {TABLE_NAME}")
            return True, columns_data
            
    except Exception as e:
        print(f"ERROR al verificar esquema: {str(e)}")
        return False, {}

def agregar_columnas_faltantes():
    """Agrega las columnas faltantes a la tabla horario_clase"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar qué columnas existen
        cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
        column_names = [col[1] for col in cursor.fetchall()]
        
        # Agregar columnas faltantes
        for column in REQUIRED_COLUMNS:
            if column not in column_names:
                if column == "activo":
                    # Columna activo con valor predeterminado TRUE
                    try:
                        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN activo BOOLEAN DEFAULT 1")
                        conn.commit()
                        print(f"✓ Columna 'activo' agregada a {TABLE_NAME}")
                    except sqlite3.OperationalError as e:
                        print(f"ERROR al agregar columna 'activo': {str(e)}")
                elif column == "fecha_desactivacion":
                    # Columna fecha_desactivacion puede ser NULL
                    try:
                        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN fecha_desactivacion DATE")
                        conn.commit()
                        print(f"✓ Columna 'fecha_desactivacion' agregada a {TABLE_NAME}")
                    except sqlite3.OperationalError as e:
                        print(f"ERROR al agregar columna 'fecha_desactivacion': {str(e)}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR al agregar columnas: {str(e)}")
        return False

def verificar_solucion():
    """Verifica que la solución fue aplicada correctamente"""
    schema_ok, columns = verificar_esquema()
    if not schema_ok:
        print("✗ La reparación no fue exitosa. Algunas columnas siguen faltando.")
        return False
        
    # Verificar que las columnas tienen los tipos correctos
    errores_tipo = []
    if "activo" in columns and columns["activo"]["type"].upper() != "BOOLEAN":
        errores_tipo.append(f"La columna 'activo' es de tipo {columns['activo']['type']} pero debería ser BOOLEAN")
        
    if "fecha_desactivacion" in columns and columns["fecha_desactivacion"]["type"].upper() != "DATE":
        errores_tipo.append(f"La columna 'fecha_desactivacion' es de tipo {columns['fecha_desactivacion']['type']} pero debería ser DATE")
    
    if errores_tipo:
        print("✗ Se encontraron problemas con los tipos de datos:")
        for error in errores_tipo:
            print(f"  - {error}")
        return False
        
    print("✓ Verificación exitosa: todas las columnas existen con el tipo correcto")
    return True

def main():
    """Función principal del script"""
    print("="*60)
    print("REPARACIÓN DE ESQUEMA DE BASE DE DATOS")
    print("="*60)
    print()
    
    # Paso 1: Verificar esquema actual
    print("1. Verificando esquema actual...")
    schema_ok, columns = verificar_esquema()
    if schema_ok:
        print("✓ El esquema ya es correcto. No se requieren cambios.")
        return True
        
    # Paso 2: Crear backup
    print("\n2. Creando backup de la base de datos...")
    if not crear_backup():
        print("✗ No se pudo crear el backup. Abortando para evitar pérdida de datos.")
        return False
        
    # Paso 3: Reparar esquema
    print("\n3. Reparando esquema...")
    if not agregar_columnas_faltantes():
        print("✗ No se pudo reparar el esquema.")
        return False
        
    # Paso 4: Verificar solución
    print("\n4. Verificando reparación...")
    if not verificar_solucion():
        print("✗ La verificación final falló. La base de datos podría no estar completamente reparada.")
        print("  Se recomienda restaurar desde el backup y contactar soporte técnico.")
        return False
        
    print("\n"+"="*60)
    print("REPARACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print("\nLa base de datos ha sido reparada y ahora incluye las columnas requeridas.")
    print("Ya puede iniciar la aplicación normalmente con start.bat")
    
    return True

if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1) 