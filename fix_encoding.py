#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para corregir problemas de codificación UTF-8 en archivos de templates.
Convierte caracteres mal codificados a su forma correcta.
"""

import os
import re

def fix_encoding_issues(content):
    """Corrige problemas comunes de codificación UTF-8"""
    
    # Diccionario de reemplazos comunes
    replacements = {
        'Ã¡': 'á',  # á mal codificado
        'Ã©': 'é',  # é mal codificado
        'Ã­': 'í',  # í mal codificado
        'Ã³': 'ó',  # ó mal codificado
        'Ãº': 'ú',  # ú mal codificado
        'Ã±': 'ñ',  # ñ mal codificado
        'Ã¼': 'ü',  # ü mal codificado
        'Ã‡': 'Ç',  # Ç mal codificado
        'Ã': 'Ñ',   # Ñ mal codificado
        'Ã€': 'À',  # À mal codificado
        'Ã': 'Á',   # Á mal codificado
        'Ã‰': 'É',  # É mal codificado
        'Ã': 'Í',   # Í mal codificado
        'Ã"': 'Ó',  # Ó mal codificado
        'Ãš': 'Ú',  # Ú mal codificado
        'Â¿': '¿',  # ¿ mal codificado
        'Â¡': '¡',  # ¡ mal codificado
        'Â«': '«',  # « mal codificado
        'Â»': '»',  # » mal codificado
        'â€œ': '"', # " mal codificado
        'â€': '"',  # " mal codificado
        'â€™': "'", # ' mal codificado
        'â€"': '–', # – mal codificado
        'â€"': '—', # — mal codificado
        'GestiÃ³n': 'Gestión',
        'secciÃ³n': 'sección',
        'SecciÃ³n': 'Sección',
        'AnÃ¡lisis': 'Análisis',
        'grÃ¡ficos': 'gráficos',
        'GrÃ¡ficos': 'Gráficos',
        'GRÃFICOS': 'GRÁFICOS',
        'MÃ©tricas': 'Métricas',
        'GuÃ­a': 'Guía',
        'CÃ¡lculos': 'Cálculos',
        'alfabÃ©ticamente': 'alfabéticamente',
        'tÃ­pica': 'típica',
        'asistiÃ³': 'asistió',
        'perÃ­odo': 'período',
        'SECCIÃ"N': 'SECCIÓN',
        'notificaciÃ³n': 'notificación',
        'AcciÃ³n': 'Acción',
        'confirmaciÃ³n': 'confirmación',
        'EstÃ¡': 'Está',
        'crearÃ¡n': 'crearán',
        'marcarÃ¡n': 'marcarán',
        'automÃ¡ticamente': 'automáticamente',
        'BotÃ³n': 'Botón',
        'estÃ©': 'esté',
        'estÃ¡': 'está',
        'cÃ³digo': 'código',
        'Ã­cono': 'ícono',
        'botÃ³n': 'botón',
        'animaciÃ³n': 'animación',
        'aÃ±adirla': 'añadirla',
        'duraciÃ³n': 'duración',
        'encontrÃ³': 'encontró',
        'proporciÃ³n': 'proporción',
        'mÃ¡ximo': 'máximo',
        'mÃ¡s': 'más',
        'subtÃ­tulos': 'subtítulos'
    }
    
    # Aplicar todos los reemplazos
    for bad, good in replacements.items():
        content = content.replace(bad, good)
    
    return content

def fix_file(file_path):
    """Corrige la codificación de un archivo específico"""
    print(f"Corrigiendo: {file_path}")
    
    try:
        # Leer el archivo con diferentes codificaciones
        content = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"  Leído con codificación: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"  ERROR: No se pudo leer el archivo con ninguna codificación")
            return False
        
        # Corregir problemas de codificación
        fixed_content = fix_encoding_issues(content)
        
        # Verificar si hubo cambios
        if content != fixed_content:
            # Crear backup
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Backup creado: {backup_path}")
            
            # Escribir archivo corregido
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  ✅ Archivo corregido exitosamente")
            return True
        else:
            print(f"  ℹ️  No se encontraron problemas de codificación")
            return False
            
    except Exception as e:
        print(f"  ❌ Error procesando archivo: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🔧 Iniciando corrección de codificación UTF-8...")
    print("=" * 50)
    
    # Archivos a corregir
    files_to_fix = [
        'templates/informes/mensual_resultado.html',
        'templates/informes/fixed.html',
        'templates/informes/mensual_resultado_orig.html',
        'templates/informes/backup/mensual_resultado.html',
        'templates/informes/metricas_profesor.html',
        'templates/informes/index.html',
        'templates/base.html'
    ]
    
    fixed_count = 0
    total_count = 0
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            total_count += 1
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  Archivo no encontrado: {file_path}")
    
    print("=" * 50)
    print(f"✅ Proceso completado:")
    print(f"   - Archivos procesados: {total_count}")
    print(f"   - Archivos corregidos: {fixed_count}")
    print(f"   - Archivos sin cambios: {total_count - fixed_count}")
    
    if fixed_count > 0:
        print("\n💡 Los archivos originales se guardaron como .backup")
        print("   Si todo funciona correctamente, puedes eliminar los archivos .backup")

if __name__ == "__main__":
    main()