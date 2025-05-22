#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Herramienta de diagnóstico para verificar la existencia y accesibilidad
de la columna 'activo' en la tabla horario_clase.

Este script realiza las siguientes comprobaciones:
1. Verifica si la columna existe en el esquema
2. Intenta hacer una consulta usando la columna
3. Reporta el estado de la columna

Uso:
    python check_column.py

También puede ser importado desde otros scripts:
    from check_column import verificar_columna
    ok, detalles = verificar_columna('activo')
"""

import sqlite3
import sys
import os

def verificar_columna(nombre_columna, tabla="horario_clase", db_file="gimnasio.db"):
    """
    Verifica si una columna existe en una tabla de la base de datos.
    
    Args:
        nombre_columna (str): Nombre de la columna a verificar
        tabla (str): Nombre de la tabla donde se busca la columna
        db_file (str): Ruta al archivo de base de datos
        
    Returns:
        (bool, dict): Tupla con resultado (True si existe y es accesible) y diccionario con detalles
    """
    resultados = {
        "existe_esquema": False,
        "accesible_query": False,
        "tipo_columna": None,
        "valores_muestra": [],
        "errores": []
    }
    
    # Verificar que el archivo existe
    if not os.path.exists(db_file):
        resultados["errores"].append(f"No se encontró el archivo de base de datos: {db_file}")
        return False, resultados
    
    # Comprobar si la columna existe en el esquema
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
        if not cursor.fetchone():
            resultados["errores"].append(f"La tabla {tabla} no existe en la base de datos")
            conn.close()
            return False, resultados
        
        # Verificar si la columna existe
        cursor.execute(f"PRAGMA table_info({tabla})")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] == nombre_columna:
                resultados["existe_esquema"] = True
                resultados["tipo_columna"] = col[2]
                break
        
        # Intentar realizar una consulta usando la columna
        if resultados["existe_esquema"]:
            try:
                query = f"SELECT id, {nombre_columna} FROM {tabla} LIMIT 5"
                cursor.execute(query)
                resultados["valores_muestra"] = cursor.fetchall()
                resultados["accesible_query"] = True
            except sqlite3.OperationalError as e:
                resultados["errores"].append(f"Error al consultar la columna: {str(e)}")
        
        conn.close()
        
        # Resultado final
        return resultados["existe_esquema"] and resultados["accesible_query"], resultados
    except Exception as e:
        resultados["errores"].append(f"Error general: {str(e)}")
        return False, resultados

def main():
    """Función principal para ejecutar las verificaciones y mostrar resultados"""
    print("="*60)
    print("VERIFICACIÓN DE COLUMNA 'activo' EN TABLA 'horario_clase'")
    print("="*60)
    print()
    
    ok, resultados = verificar_columna('activo')
    
    # Mostrar resultados
    print(f"La columna 'activo' existe en el esquema: {'✓' if resultados['existe_esquema'] else '✗'}")
    print(f"La columna 'activo' es accesible en consultas: {'✓' if resultados['accesible_query'] else '✗'}")
    
    if resultados["tipo_columna"]:
        print(f"Tipo de columna: {resultados['tipo_columna']}")
    
    if resultados["valores_muestra"]:
        print("\nValores de muestra (primeros 5 registros):")
        for idx, valor in enumerate(resultados["valores_muestra"]):
            print(f"  {idx+1}. ID: {valor[0]}, activo: {valor[1]}")
    
    if resultados["errores"]:
        print("\nErrores encontrados:")
        for error in resultados["errores"]:
            print(f"  - {error}")
    
    print("\nDiagnóstico final:")
    if ok:
        print("✓ La columna 'activo' existe y es accesible. No se detectaron problemas.")
    else:
        print("✗ Se detectaron problemas con la columna 'activo'.")
        print("  Recomendación: Ejecute fix_activo_column.bat para solucionar el problema.")
    
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main()) 