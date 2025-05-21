import os
import sys
from datetime import datetime, date, time
from app import app, db
from models import HorarioClase, ClaseRealizada

# Monkeypatch informe_mensual to debug the computation
from functools import wraps
from flask import render_template
import inspect
import app as app_module

# Get the original function
original_informe_mensual = app_module.informe_mensual

# Define the wrapper function
@wraps(original_informe_mensual)
def debug_informe_mensual(*args, **kwargs):
    # Call the original function
    result = original_informe_mensual(*args, **kwargs)
    
    # If it's a POST request (generating the report)
    if len(args) > 0 and args[0].method == 'POST':
        # Try to extract the variables from the render_template call
        if isinstance(result, str):
            # This means the function already returned the rendered template
            print("ERROR: Can't intercept render_template variables after rendering")
        else:
            # Intercept before the template is rendered
            print("\n============= DEBUG INFORME_MENSUAL VARIABLES =============")
            context = result.context
            
            # Check if our variables exist
            if 'conteo_tipos_manana' in context:
                print(f"conteo_tipos_manana = {context['conteo_tipos_manana']}")
            else:
                print("conteo_tipos_manana not found in template context")
                
            if 'conteo_tipos_tarde' in context:
                print(f"conteo_tipos_tarde = {context['conteo_tipos_tarde']}")
            else:
                print("conteo_tipos_tarde not found in template context")
            
            # Check division_horario
            if 'division_horario' in context:
                print(f"division_horario = {context['division_horario']}")
            else:
                print("division_horario not found in template context")
            
            # Check hora_inicio parsing for a few classes
            if 'clases_realizadas' in context:
                print("\nMuestra de 5 clases y su hora_inicio:")
                for i, clase in enumerate(context['clases_realizadas'][:5]):
                    hora_inicio_orig = clase.horario.hora_inicio
                    hora_inicio_parsed = None
                    
                    if isinstance(hora_inicio_orig, str):
                        try:
                            hora_inicio_parsed = datetime.strptime(hora_inicio_orig, '%H:%M:%S').time()
                        except Exception:
                            try:
                                hora_inicio_parsed = datetime.strptime(hora_inicio_orig, '%H:%M').time()
                            except Exception:
                                hora_inicio_parsed = time(0, 0)
                    else:
                        hora_inicio_parsed = hora_inicio_orig
                    
                    tipo_clase = clase.horario.tipo_clase if hasattr(clase.horario, 'tipo_clase') else 'DESCONOCIDO'
                    es_manana = hora_inicio_parsed < time(13, 0)
                    
                    print(f"Clase {i+1}: {clase.horario.nombre}, tipo={tipo_clase}")
                    print(f"  hora_inicio_orig={hora_inicio_orig} ({type(hora_inicio_orig)})")
                    print(f"  hora_inicio_parsed={hora_inicio_parsed} ({type(hora_inicio_parsed)})")
                    print(f"  ¿Es mañana? {'SÍ' if es_manana else 'NO'}")
                    print(f"  Debe agregarse a: {'conteo_tipos_manana' if es_manana else 'conteo_tipos_tarde'}[{tipo_clase}]")
                    print()
            
            print("============= FIN DEBUG INFORME_MENSUAL =============\n")
    
    return result

# Apply the monkeypatching
app_module.informe_mensual = debug_informe_mensual

# Just print confirmation
print("\nMonkeypatched informe_mensual for debugging")
print("Visit http://127.0.0.1:5000/informes/mensual and generate a report to see the debug output in the console")

# Get current month and year
now = datetime.now()
mes = now.month
anio = now.year
primer_dia = date(anio, mes, 1)
ultimo_dia = date(anio, mes, 28)
while True:
    try:
        ultimo_dia = date(anio, mes, ultimo_dia.day + 1)
    except ValueError:
        break

with app.app_context():
    # Unique tipo_clase in HorarioClase
    horario_tipos = set(h.tipo_clase for h in HorarioClase.query.all())
    print("Unique tipo_clase in HorarioClase:")
    for t in sorted(horario_tipos):
        print(f"- '{t}'")

    # Unique tipo_clase in ClaseRealizada for current month
    clases = ClaseRealizada.query.filter(
        ClaseRealizada.fecha >= primer_dia,
        ClaseRealizada.fecha <= ultimo_dia
    ).all()
    clase_tipos = set(c.horario.tipo_clase for c in clases if c.horario)
    print("\nUnique tipo_clase in ClaseRealizada.horario for current month:")
    for t in sorted(clase_tipos):
        print(f"- '{t}'")

    print(f"\nTotal ClaseRealizada records for current month: {len(clases)}")
    # Group by period and type
    debug_dict = {'mañana': {}, 'tarde': {}}
    for c in clases:
        tipo = c.horario.tipo_clase if c.horario else 'NO HORARIO'
        horario_id = c.horario.id if c.horario else 'NO HORARIO'
        hora_inicio = c.horario.hora_inicio if c.horario else None
        hora_inicio_str = str(hora_inicio)
        parsed = None
        if isinstance(hora_inicio, str):
            try:
                parsed = datetime.strptime(hora_inicio, '%H:%M:%S').time()
            except Exception:
                try:
                    parsed = datetime.strptime(hora_inicio, '%H:%M').time()
                except Exception:
                    parsed = time(0, 0)
        elif isinstance(hora_inicio, time):
            parsed = hora_inicio
        else:
            parsed = time(0, 0)
        periodo = 'mañana' if parsed < time(13, 0) else 'tarde'
        if tipo not in debug_dict[periodo]:
            debug_dict[periodo][tipo] = []
        debug_dict[periodo][tipo].append((horario_id, hora_inicio_str, parsed))
    print("\n================ DEBUG CLASES POR TIPO Y PERIODO ================")
    for periodo in ['mañana', 'tarde']:
        print(f"\n=== {periodo.upper()} ===")
        for tipo, clases_list in debug_dict[periodo].items():
            for horario_id, hora_inicio_str, parsed in clases_list:
                print(f"DETECTADA CLASE {tipo} en horario_id={horario_id}, hora_inicio_str={hora_inicio_str}, hora_inicio_obj={parsed}")

    manana = []
    tarde = []
    for c in clases:
        tipo = c.horario.tipo_clase if c.horario else 'NO HORARIO'
        hora_inicio = c.horario.hora_inicio if c.horario else None
        hora_inicio_str = str(hora_inicio)
        parsed = None
        if isinstance(hora_inicio, str):
            try:
                parsed = datetime.strptime(hora_inicio, '%H:%M:%S').time()
            except Exception:
                try:
                    parsed = datetime.strptime(hora_inicio, '%H:%M').time()
                except Exception:
                    parsed = time(0, 0)
        elif isinstance(hora_inicio, time):
            parsed = hora_inicio
        else:
            parsed = time(0, 0)
        periodo = 'mañana' if parsed < time(13, 0) else 'tarde'
        if periodo == 'mañana':
            manana.append((c.fecha, tipo, hora_inicio_str))
        else:
            tarde.append((c.fecha, tipo, hora_inicio_str))
        print(f"Fecha: {c.fecha}, Tipo: '{tipo}', hora_inicio: '{hora_inicio_str}', parsed: '{parsed}', periodo: {periodo}")
    print(f"\nResumen: {len(manana)} clases de mañana, {len(tarde)} clases de tarde")
    print("Clases de mañana:")
    for f, t, h in manana:
        print(f"  {f} - {t} - {h}")
    print("Clases de tarde:")
    for f, t, h in tarde:
        print(f"  {f} - {t} - {h}") 