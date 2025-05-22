#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sincroniza los modelos de la aplicación y verifica que la base de datos tenga la estructura correcta.
Soluciona el error "no such column: horario_clase.activo" asegurando que todos los archivos de modelos
son consistentes y que la columna existe en la base de datos.
"""

import os
import sys
import shutil
import sqlite3
import importlib
import time

def verificar_columna_activo():
    """Verifica si la columna 'activo' existe en la tabla horario_clase"""
    print("Verificando columna 'activo' en la base de datos...")
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(horario_clase)")
        columns = cursor.fetchall()
        conn.close()
        
        column_names = [col[1] for col in columns]
        if 'activo' in column_names:
            print("✓ La columna 'activo' existe en la base de datos")
            return True
        else:
            print("✗ La columna 'activo' NO existe en la base de datos")
            return False
    except Exception as e:
        print(f"Error al verificar la columna 'activo': {str(e)}")
        return False

def agregar_columna_activo():
    """Agrega la columna 'activo' a la tabla horario_clase si no existe"""
    print("Agregando columna 'activo' a la base de datos...")
    try:
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE horario_clase ADD COLUMN activo BOOLEAN DEFAULT 1")
            conn.commit()
            print("✓ Columna 'activo' agregada correctamente")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("La columna 'activo' ya existe, no es necesario agregarla")
            else:
                raise e
        
        try:
            cursor.execute("ALTER TABLE horario_clase ADD COLUMN fecha_desactivacion DATE")
            conn.commit()
            print("✓ Columna 'fecha_desactivacion' agregada correctamente")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("La columna 'fecha_desactivacion' ya existe, no es necesario agregarla")
            else:
                raise e
                
        conn.close()
        return True
    except Exception as e:
        print(f"Error al agregar la columna 'activo': {str(e)}")
        return False

def sincronizar_modelos():
    """Sincroniza el archivo models.py de la raíz con el de la carpeta app/"""
    print("Sincronizando archivos de modelos...")
    try:
        # Comprobar si ambos archivos existen
        root_models = os.path.join(os.getcwd(), 'models.py')
        app_models = os.path.join(os.getcwd(), 'app', 'models.py')
        
        if not os.path.exists(root_models):
            print(f"✗ El archivo models.py no existe en la raíz")
            return False
            
        # Crear directorio app/ si no existe
        if not os.path.exists(os.path.dirname(app_models)):
            os.makedirs(os.path.dirname(app_models))
        
        # Copiar el archivo
        shutil.copy2(root_models, app_models)
        print(f"✓ Archivo models.py copiado a app/models.py")
        return True
    except Exception as e:
        print(f"Error al sincronizar los modelos: {str(e)}")
        return False

def limpiar_cache_python():
    """Limpia los archivos de caché de Python"""
    print("Limpiando archivos de caché de Python...")
    try:
        for root, dirs, files in os.walk(os.getcwd()):
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    pycache_dir = os.path.join(root, dir_name)
                    print(f"  - Eliminando {pycache_dir}")
                    shutil.rmtree(pycache_dir)
        return True
    except Exception as e:
        print(f"Error al limpiar la caché de Python: {str(e)}")
        return False

def verificar_consistencia_modelos():
    """Verifica que los modelos en ambos archivos tengan la columna 'activo'"""
    try:
        # Importar el modelo desde la raíz (necesita reiniciar el intérprete)
        print("Verificando consistencia de modelos...")

        # Verificar manualmente con una búsqueda en el archivo
        root_models = os.path.join(os.getcwd(), 'models.py')
        app_models = os.path.join(os.getcwd(), 'app', 'models.py')
        
        def revisar_archivo(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                tiene_activo = "activo = db.Column(db.Boolean" in contenido
                tiene_fecha_desactivacion = "fecha_desactivacion = db.Column(db.Date" in contenido
                return tiene_activo and tiene_fecha_desactivacion
                
        raiz_ok = revisar_archivo(root_models)
        app_ok = revisar_archivo(app_models) if os.path.exists(app_models) else False
        
        print(f"✓ models.py (raíz) tiene las columnas requeridas: {raiz_ok}")
        print(f"✓ app/models.py tiene las columnas requeridas: {app_ok}")
        
        return raiz_ok and app_ok
    except Exception as e:
        print(f"Error al verificar la consistencia de los modelos: {str(e)}")
        return False

def main():
    """Función principal que ejecuta todas las verificaciones y correcciones"""
    print("=" * 60)
    print("SOLUCIÓN AL ERROR 'no such column: horario_clase.activo'")
    print("=" * 60)
    print()
    
    # Paso 1: Verificar si la columna existe en la base de datos
    columna_existe = verificar_columna_activo()
    if not columna_existe:
        if not agregar_columna_activo():
            print("No se pudo agregar la columna 'activo' a la base de datos.")
            return False
    
    # Paso 2: Limpiar caché de Python
    limpiar_cache_python()
    
    # Paso 3: Sincronizar archivos de modelos
    sincronizado = sincronizar_modelos()
    if not sincronizado:
        print("No se pudieron sincronizar los archivos de modelos.")
        return False
    
    # Paso 4: Verificar consistencia de modelos
    consistentes = verificar_consistencia_modelos()
    if not consistentes:
        print("Los modelos no son consistentes, es posible que el problema persista.")
        return False
    
    print("\n" + "=" * 60)
    print("SOLUCIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print("\nLa aplicación debería funcionar correctamente ahora.")
    print("Para reiniciar la aplicación, ejecute: python app.py")
    
    return True

if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1) 