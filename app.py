import os
import logging
import traceback
import re  # para expresiones regulares
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime, timedelta, date, time
from werkzeug.utils import secure_filename
import calendar
from flask_wtf.csrf import CSRFProtect, generate_csrf
import pandas as pd
import numpy as np
import io
import re
import click
import functools
import glob
import shutil

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Necesario para generar gráficos sin interfaz gráfica
import librosa
import librosa.display
import io
import base64
import time as time_module  # Renamed to avoid conflict with datetime.time

# Definir constantes utilizadas en la aplicación
DIAS_SEMANA = [
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
    (5, 'Sábado'),
    (6, 'Domingo')
]

TIPOS_CLASE = [
    ('MOVE', 'MOVE'),
    ('RIDE', 'RIDE'),
    ('BOX', 'BOX'),
    ('OTRO', 'OTRO')
]

# Inicializar la aplicación Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
# Configurar Flask para aceptar URLs con o sin barra final
app.url_map.strict_slashes = False
app.config['SECRET_KEY'] = 'tu-clave-secreta'
csrf = CSRFProtect(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Inicializar la base de datos
db = SQLAlchemy(app)

# Importar modelos después de inicializar db y app
from models import Profesor, HorarioClase, ClaseRealizada, EventoHorario, TipoEventoHorario, setup_date_handling

# Configurar el manejo de fechas para la aplicación
setup_date_handling(app)

# Importar el blueprint de API
from api_routes import api

# Importar el blueprint de audio
from audio_routes import audio_bp

# Importar módulo de notificaciones
from notifications import setup_notification_scheduler, check_and_notify_unregistered_classes, send_whatsapp_notification, is_notification_locked
from notifications import update_notification_schedule, DEFAULT_NOTIFICATION_HOUR_1, DEFAULT_NOTIFICATION_HOUR_2

# Definir extensiones permitidas para archivos Excel
ALLOWED_EXTENSIONS_EXCEL = {'xlsx', 'xls'}

# Definir extensiones permitidas para archivos de audio
ALLOWED_EXTENSIONS_AUDIO = {'mp3', 'wav', 'ogg', 'webm', 'm4a'}

# Función para verificar si un archivo tiene una extensión permitida
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Añade esto después de crear tu aplicación Flask en app.py
# Nota: SOLO PARA DESARROLLO, no usar en producción
app.config['WTF_CSRF_ENABLED'] = False

# Configuración para notificaciones WhatsApp
app.config['NOTIFICATION_PHONE_NUMBER'] = os.environ.get('NOTIFICATION_PHONE_NUMBER')

# Configuración para PyWhatKit
app.config['WHATSAPP_NUMBER'] = os.environ.get('WHATSAPP_NUMBER')
app.config['WHATSAPP_MESSAGE'] = os.environ.get('WHATSAPP_MESSAGE')

# Exempt certain routes from CSRF
csrf.exempt('/import/asistencia')
csrf.exempt('/import/clases')
csrf.exempt('/import/horarios')
csrf.exempt('/import/profesores')
# Añadir esta línea para eximir la ruta de carga de audio
csrf.exempt('/asistencia/upload_audio/<int:horario_id>')

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Configurar logging para depuración
try:
    logger = logging.getLogger('import_debug')
    if not logger.handlers:
        # Crear handler de archivo
        log_file = logging.FileHandler('import_debug.log', 'w', encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        log_file.setFormatter(formatter)
        logger.addHandler(log_file)
        logger.setLevel(logging.DEBUG)
        
        # Crear archivo de errores
        with open('import_errors.log', 'w', encoding='utf-8') as f:
            f.write("Registro de errores de importación\n\n")
except Exception as e:
    print(f"Error al configurar logging: {e}")

# Decorador para rutas inaccesibles
def ruta_inaccesible(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        abort(404)  # Retornar error 404 Not Found
    return decorated_function

# Registrar filtro personalizado para divmod
@app.template_filter('divmod')
def divmod_filter(value, arg):
    return divmod(value, arg)

# Filtro para obtener el timestamp actual
@app.template_filter('now')
def now_filter(value=None):
    return datetime.now()

# Filtro para obtener valor seguro de enum
@app.template_filter('enum_value')
def enum_value_filter(value):
    """
    Obtiene el valor de un enum de forma segura, independientemente de si es un miembro del enum o un string.
    Útil para las plantillas cuando se trabaja con enum a través de SQLAlchemy.
    """
    if hasattr(value, 'value'):
        return value.value
    return str(value)

# Función para convertir un valor decimal de Excel a objeto time
def excel_time_to_time(excel_time):
    if pd.isna(excel_time):
        return None
        
    # Si ya es un objeto time, devolverlo directamente
    if isinstance(excel_time, time):
        return excel_time
    
    # Si es datetime, extraer la hora
    if isinstance(excel_time, datetime):
        return excel_time.time()
        
    # Si es string, intentar convertirlo a time
    if isinstance(excel_time, str):
        # Eliminar espacios en blanco
        excel_time = excel_time.strip()
        
        # Comprobar si ya tiene el formato de hora (contiene :)
        if ':' in excel_time:
            try:
                # Probar diferentes formatos comunes de hora
                formats_to_try = [
                    '%H:%M',
                    '%H:%M:%S',
                    '%I:%M %p',
                    '%I:%M:%S %p',
                    '%H.%M',
                    '%H.%M.%S'
                ]
                
                for fmt in formats_to_try:
                    try:
                        return datetime.strptime(excel_time, fmt).time()
                    except ValueError:
                        continue
                
                # Si no coincide con ningún formato, intentar analizar manualmente
                parts = excel_time.split(':')
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    return time(hour, minute, second)
                
                # Si todo falla, registrar un error detallado
                print(f"No se pudo convertir la hora: '{excel_time}', no coincide con formatos conocidos")
                return None
            except Exception as e:
                print(f"Error al convertir hora '{excel_time}': {str(e)}")
                return None
    
    # Para valores numéricos (decimal de Excel)
    try:
        if isinstance(excel_time, (int, float)):
            # Convertir valor decimal a horas y minutos
            total_seconds = excel_time * 86400  # 24 horas * 60 minutos * 60 segundos
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            return time(hours, minutes, seconds)
    except Exception as e:
        print(f"Error al convertir valor decimal '{excel_time}': {str(e)}")
        return None
    
    # Si llegamos aquí, no pudimos convertir el valor
    print(f"Tipo de dato no manejado para hora: {type(excel_time)}, valor: {excel_time}")
    return None

# Rutas
@app.route('/test')
def test_route():
    return "Application is working!"

@app.route('/test-template')
def test_template():
    return render_template('test.html')

@app.route('/')
def index():
    # Make sure this implementation is complete
    try:
        hoy = date.today()
        dia_semana = hoy.weekday()  # 0 for Monday, 6 for Sunday
        
        # Get classes scheduled for today - ONLY ACTIVE
        try:
            horarios_hoy = HorarioClase.query.filter_by(dia_semana=dia_semana, activo=True).all()
        except Exception as column_error:
            # Si la columna activo no existe, considerar todos los horarios como activos
            print(f"Error al filtrar por columna 'activo': {str(column_error)}")
            print("Usando consulta alternativa sin columna 'activo'")
            horarios_hoy = HorarioClase.query.filter_by(dia_semana=dia_semana).all()
        
        # Check which ones already have attendance recorded
        clases_registradas = {cr.horario_id: cr for cr in ClaseRealizada.query.filter_by(fecha=hoy).all()}
        
        return render_template('index.html', 
                              horarios=horarios_hoy, 
                              clases_registradas=clases_registradas,
                              hoy=hoy)
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return f"Error loading the homepage: {str(e)}", 500

@app.route('/simple')
def index_simple():
    try:
        # Obtener clases programadas para hoy - SOLO ACTIVAS
        hoy = datetime.now().date()
        dia_semana = hoy.weekday()  # 0 es lunes, 6 es domingo
        
        try:
            horarios_hoy = HorarioClase.query.filter_by(dia_semana=dia_semana, activo=True).order_by(HorarioClase.hora_inicio).all()
        except Exception as column_error:
            # Si la columna activo no existe, considerar todos los horarios como activos
            print(f"Error al filtrar por columna 'activo': {str(column_error)}")
            print("Usando consulta alternativa sin columna 'activo'")
            horarios_hoy = HorarioClase.query.filter_by(dia_semana=dia_semana).order_by(HorarioClase.hora_inicio).all()
        
        return render_template('index_simple.html', 
                              horarios_hoy=horarios_hoy, 
                              hoy=hoy)
    except Exception as e:
        # Log the error
        print(f"Error in simple index route: {str(e)}")
        traceback.print_exc()
        # Return a simple error page
        return f"<h1>Error</h1><p>An error occurred: {str(e)}</p><pre>{traceback.format_exc()}</pre>"

# Rutas para Profesores
@app.route('/profesores')
def listar_profesores():
    profesores = Profesor.query.all()
    return render_template('profesores/lista.html', profesores=profesores)

@app.route('/profesores/nuevo', methods=['GET', 'POST'])
def nuevo_profesor():
    if request.method == 'POST':
        profesor = Profesor(
            nombre=request.form['nombre'],
            apellido=request.form['apellido'],
            tarifa_por_clase=float(request.form['tarifa_por_clase']),
            telefono=request.form['telefono'],
            email=request.form['email']
        )
        db.session.add(profesor)
        db.session.commit()
        flash('Profesor registrado con éxito', 'success')
        return redirect(url_for('listar_profesores'))
    return render_template('profesores/nuevo.html')

@app.route('/profesores/editar/<int:id>', methods=['GET', 'POST'])
def editar_profesor(id):
    profesor = Profesor.query.get_or_404(id)
    if request.method == 'POST':
        profesor.nombre = request.form['nombre']
        profesor.apellido = request.form['apellido']
        profesor.tarifa_por_clase = float(request.form['tarifa_por_clase'])
        profesor.telefono = request.form['telefono']
        profesor.email = request.form['email']
        db.session.commit()
        flash('Profesor actualizado con éxito', 'success')
        return redirect(url_for('listar_profesores'))
    return render_template('profesores/editar.html', profesor=profesor)

@app.route('/profesores/eliminar/<int:id>')
def eliminar_profesor(id):
    profesor = Profesor.query.get_or_404(id)
    if HorarioClase.query.filter_by(profesor_id=id).first() or ClaseRealizada.query.filter_by(profesor_id=id).first():
        flash('No se puede eliminar el profesor porque tiene clases asociadas', 'danger')
    else:
        db.session.delete(profesor)
        db.session.commit()
        flash('Profesor eliminado con éxito', 'success')
    return redirect(url_for('listar_profesores'))

@app.route('/profesores/eliminar-varios', methods=['POST'])
def eliminar_varios_profesores():
    profesores_ids = request.form.getlist('profesores_ids[]')
    if not profesores_ids:
        flash('No se han seleccionado profesores para eliminar', 'warning')
        return redirect(url_for('listar_profesores'))
    
    profesores_eliminados = 0
    profesores_con_dependencias = 0
    
    for profesor_id in profesores_ids:
        profesor = Profesor.query.get(profesor_id)
        if profesor:
            # Verificar si tiene horarios o clases asociadas
            if HorarioClase.query.filter_by(profesor_id=profesor_id).first() or ClaseRealizada.query.filter_by(profesor_id=profesor_id).first():
                profesores_con_dependencias += 1
            else:
                db.session.delete(profesor)
                profesores_eliminados += 1
    
    db.session.commit()
    
    if profesores_eliminados > 0:
        flash(f'Se eliminaron {profesores_eliminados} profesores con éxito', 'success')
    
    if profesores_con_dependencias > 0:
        flash(f'No se pudieron eliminar {profesores_con_dependencias} profesores porque tienen clases asociadas', 'warning')
    
    return redirect(url_for('listar_profesores'))

# Rutas para Horarios de Clases
@app.route('/horarios')
def listar_horarios():
    # Mostrar todos los horarios
    horarios = HorarioClase.query.order_by(HorarioClase.dia_semana, HorarioClase.hora_inicio).all()
    return render_template('horarios/lista.html', horarios=horarios, dias_semana=dict(DIAS_SEMANA))

@app.route('/horarios/nuevo', methods=['GET', 'POST'])
def nuevo_horario():
    profesores = Profesor.query.order_by(Profesor.apellido).all()
    
    if request.method == 'POST':
        horario = HorarioClase(
            nombre=request.form['nombre'],
            dia_semana=int(request.form['dia_semana']),
            hora_inicio=datetime.strptime(request.form['hora_inicio'], '%H:%M').time(),
            duracion=int(request.form['duracion']),
            profesor_id=int(request.form['profesor_id']),
            capacidad_maxima=int(request.form['capacidad_maxima']),
            tipo_clase=request.form['tipo_clase']
        )
        db.session.add(horario)
        db.session.commit()
        flash('Horario creado con éxito', 'success')
        return redirect(url_for('listar_horarios'))
    
    return render_template('horarios/nuevo.html', profesores=profesores, dias_semana=DIAS_SEMANA, tipos_clase=TIPOS_CLASE)

@app.route('/horarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_horario(id):
    horario = HorarioClase.query.get_or_404(id)
    profesores = Profesor.query.order_by(Profesor.apellido).all()
    
    if request.method == 'POST':
        horario.nombre = request.form['nombre']
        horario.dia_semana = int(request.form['dia_semana'])
        horario.hora_inicio = datetime.strptime(request.form['hora_inicio'], '%H:%M').time()
        horario.duracion = int(request.form['duracion'])
        horario.profesor_id = int(request.form['profesor_id'])
        horario.capacidad_maxima = int(request.form['capacidad_maxima'])
        horario.tipo_clase = request.form['tipo_clase']
        db.session.commit()
        flash('Horario actualizado con éxito', 'success')
        return redirect(url_for('listar_horarios'))
    
    return render_template('horarios/editar.html', horario=horario, profesores=profesores, dias_semana=DIAS_SEMANA, tipos_clase=TIPOS_CLASE)

@app.route('/horarios/eliminar/<int:id>')
def eliminar_horario(id):
    horario = HorarioClase.query.get_or_404(id)
    
    # Eliminar el horario y todas sus clases asociadas
    clases_asociadas = ClaseRealizada.query.filter_by(horario_id=id).all()
    
    # Eliminar todas las clases asociadas
    for clase in clases_asociadas:
        # Si la clase tiene archivo de audio, eliminar el archivo
        if clase.audio_file:
            try:
                audio_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), clase.audio_file)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                app.logger.error(f"Error eliminando archivo de audio: {str(e)}")
        
        db.session.delete(clase)
    
    # Eliminar el horario
    db.session.delete(horario)
    db.session.commit()
    
    if clases_asociadas:
        flash(f'Horario de clase y {len(clases_asociadas)} clases asociadas eliminadas con éxito.', 'success')
    else:
        flash('Horario de clase eliminado con éxito', 'success')
    
    return redirect(url_for('listar_horarios'))

@app.route('/horarios/confirmar-eliminar/<int:id>', methods=['GET', 'POST'])
def confirmar_eliminar_horario(id):
    horario = HorarioClase.query.get_or_404(id)
    
    # Contar cuántas clases realizadas están asociadas
    clases_asociadas = ClaseRealizada.query.filter_by(horario_id=id).all()
    cantidad_clases = len(clases_asociadas)
    
    if request.method == 'POST':
        opcion = request.form.get('opcion')
        
        if opcion == 'solo_horario':
            # Opción 1: Eliminar solo el horario, pero las clases no pueden quedar huérfanas
            # ya que horario_id es NOT NULL en la tabla clase_realizada
            
            # Buscar o crear un horario especial "Horario Eliminado" para mantener la referencia
            horario_eliminado = HorarioClase.query.filter_by(nombre="Horario Eliminado (Clases Históricas)").first()
            
            if not horario_eliminado:
                # Crear un horario especial si no existe
                horario_eliminado = HorarioClase(
                    nombre="Horario Eliminado (Clases Históricas)",
                    dia_semana=0,  # Lunes
                    hora_inicio=datetime.strptime("00:00", '%H:%M').time(),
                    duracion=0,
                    profesor_id=horario.profesor_id,  # Mantener el mismo profesor
                    capacidad_maxima=0,
                    tipo_clase="OTRO"
                )
                db.session.add(horario_eliminado)
                db.session.flush()  # Para obtener el ID sin hacer commit
            
            # Mover todas las clases asociadas al horario eliminado
            for clase in clases_asociadas:
                clase.horario_id = horario_eliminado.id
            
            # Eliminar el horario original
            db.session.delete(horario)
            db.session.commit()
            flash(f'Horario de clase eliminado con éxito. {cantidad_clases} clases asociadas se mantienen en el sistema con referencia a "Horario Eliminado".', 'success')
            
        elif opcion == 'horario_y_clases':
            # Opción 2: Eliminar el horario y todas las clases asociadas
            for clase in clases_asociadas:
                # Si la clase tiene archivo de audio, eliminar el archivo
                if clase.audio_file:
                    try:
                        audio_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), clase.audio_file)
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                    except Exception as e:
                        app.logger.error(f"Error eliminando archivo de audio: {str(e)}")
                
                db.session.delete(clase)
            
            db.session.delete(horario)
            db.session.commit()
            flash(f'Horario de clase y {cantidad_clases} clases asociadas eliminadas con éxito.', 'success')
        else:
            flash('Operación cancelada', 'info')
            
        return redirect(url_for('listar_horarios'))
    
    return render_template('horarios/confirmar_eliminar.html', 
                           horario=horario, 
                           cantidad_clases=cantidad_clases)

@app.route('/horarios/eliminar-varios', methods=['POST'])
def eliminar_varios_horarios():
    horarios_ids = request.form.getlist('horarios_ids[]')
    if not horarios_ids:
        flash('No se han seleccionado horarios para eliminar', 'warning')
        return redirect(url_for('listar_horarios'))
    
    horarios_eliminados = 0
    clases_eliminadas = 0
    
    for horario_id in horarios_ids:
        horario = HorarioClase.query.get(horario_id)
        if horario:
            # Eliminar todas las clases asociadas a este horario
            clases_asociadas = ClaseRealizada.query.filter_by(horario_id=horario_id).all()
            
            # Eliminar los archivos de audio de las clases
            for clase in clases_asociadas:
                if clase.audio_file:
                    try:
                        audio_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), clase.audio_file)
                        if os.path.exists(audio_path):
                            os.remove(audio_path)
                    except Exception as e:
                        app.logger.error(f"Error eliminando archivo de audio: {str(e)}")
                
                db.session.delete(clase)
                clases_eliminadas += 1
            
            # Eliminar el horario
            db.session.delete(horario)
            horarios_eliminados += 1
    
    db.session.commit()
    
    if horarios_eliminados > 0:
        if clases_eliminadas > 0:
            flash(f'Se eliminaron {horarios_eliminados} horarios y {clases_eliminadas} clases asociadas con éxito', 'success')
        else:
            flash(f'Se eliminaron {horarios_eliminados} horarios con éxito', 'success')
    
    return redirect(url_for('listar_horarios'))

# Route removed - desactivar_horario

# Rutas para Control de Asistencia
@app.route('/asistencia')
def control_asistencia():
    # Mostrar las clases programadas para hoy que no tienen registro de asistencia
    try:
        hoy = datetime.now().date()
        # En Python, weekday() devuelve 0 (lunes) a 6 (domingo)
        dia_semana = hoy.weekday()
        
        # Obtener todos los horarios programados para hoy sin filtrar por activo
        horarios_hoy = HorarioClase.query.filter_by(dia_semana=dia_semana).order_by(HorarioClase.hora_inicio).all()
        app.logger.info(f"Obtenidos {len(horarios_hoy)} horarios para el día {dia_semana}")
        
        # Clases ya registradas hoy
        clases_realizadas_hoy = ClaseRealizada.query.filter_by(fecha=hoy).all()
        
        # IDs de horarios que ya tienen clases realizadas registradas hoy
        horarios_ya_registrados = [cr.horario_id for cr in clases_realizadas_hoy]
        
        # Horarios pendientes (que no tienen registro aún)
        horarios_pendientes = [h for h in horarios_hoy if h.id not in horarios_ya_registrados]
        
        # Verificar si hay archivos de audio temporales para clases pendientes
        temp_audio_files = {}
        for horario in horarios_pendientes:
            for ext in ['mp3', 'wav', 'ogg']:
                audio_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), f'temp_horario_{horario.id}.{ext}')
                if os.path.exists(audio_path):
                    temp_audio_files[horario.id] = True
                    break
        
        # Handle empty horarios_pendientes list safely
        horario_id = None
        if horarios_pendientes:
            horario_id = horarios_pendientes[0].id
        
        # Only retrieve clase if needed
        clase = ClaseRealizada.query.first()
        
        return render_template('asistencia/control.html', 
                            horarios_pendientes=horarios_pendientes,
                            clases_realizadas=clases_realizadas_hoy,
                            temp_audio_files=temp_audio_files,
                            hoy=hoy,
                            horarioId=horario_id,
                            clase=clase,
                            current_timestamp=int(time_module.time()))
    except Exception as e:
        app.logger.error(f"Error in control_asistencia: {str(e)}")
        app.logger.error(traceback.format_exc())
        return f"Error: {str(e)}", 500

@app.route('/asistencia/registrar/<int:horario_id>', methods=['GET', 'POST'])
def registrar_asistencia(horario_id):
    horario = HorarioClase.query.get_or_404(horario_id)
    hoy = datetime.now().date()
    
    # Verificar si ya existe una clase realizada para este horario en esta fecha
    clase_existente = ClaseRealizada.query.filter_by(
        horario_id=horario_id,
        fecha=hoy
    ).first()
    
    if clase_existente:
        flash('Ya existe un registro para este horario en la fecha actual', 'warning')
        return redirect(url_for('control_asistencia'))
    
    if request.method == 'POST':
        # Obtener fecha manual si se proporciona, de lo contrario usar la fecha actual
        fecha_registro = hoy
        if request.form.get('fecha_manual'):
            try:
                fecha_registro = datetime.strptime(request.form.get('fecha_manual'), '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de fecha inválido. Se utilizará la fecha actual.', 'warning')
        
        # Verificar si ya existe una clase realizada para este horario en la fecha seleccionada
        if fecha_registro != hoy:
            clase_existente = ClaseRealizada.query.filter_by(
                horario_id=horario_id,
                fecha=fecha_registro
            ).first()
            
            if clase_existente:
                flash(f'Ya existe un registro para este horario en la fecha {fecha_registro.strftime("%d/%m/%Y")}', 'warning')
                return redirect(url_for('control_asistencia'))
        
        # Obtener el estado de la clase (normal, suplencia, cancelada)
        estado_clase = request.form.get('estado_clase', 'normal')
        
        # Inicializar variables
        hora_llegada = None
        cantidad_alumnos = 0
        observaciones = ""
        profesor_id = horario.profesor_id  # Default to the scheduled teacher
        
        # Process form data according to class state
        if estado_clase == 'normal':
            # Normal class with the regular teacher
            hora_llegada = request.form.get('hora_llegada')
            cantidad_alumnos = request.form.get('cantidad_alumnos', 0)
            observaciones = request.form.get('observaciones', '')
            profesor_id = request.form.get('profesor_id') or profesor_id
            
        elif estado_clase == 'suplencia':
            # Class with a substitute teacher
            hora_llegada = request.form.get('hora_llegada_suplente')
            cantidad_alumnos = request.form.get('cantidad_alumnos_suplencia', 0)
            motivo_suplencia = request.form.get('motivo_suplencia', 'otro')
            profesor_id = request.form.get('profesor_suplente') or profesor_id
            observaciones = f"SUPLENCIA - Motivo: {motivo_suplencia} - " + request.form.get('observaciones', '')
            
        elif estado_clase == 'cancelada':
            # Cancelled class
            hora_llegada = None  # No arrival time for cancelled classes
            cantidad_alumnos = 0  # No students for cancelled classes
            motivo_ausencia = request.form.get('motivo_ausencia', 'otro')
            aviso_alumnos = request.form.get('aviso_alumnos', 'no')
            observaciones = f"CLASE CANCELADA - Motivo: {motivo_ausencia} - Aviso: {aviso_alumnos} - " + request.form.get('observaciones', '')
        
        # Convert cantidad_alumnos to integer
        try:
            cantidad_alumnos = int(cantidad_alumnos)
        except (ValueError, TypeError):
            cantidad_alumnos = 0
            
        # Convert profesor_id to integer if provided
        if profesor_id:
            profesor_id = int(profesor_id)
            
        try:
            # Convertir la hora de llegada a un objeto time (only for non-cancelled classes)
            hora_llegada_time = None
            if hora_llegada and estado_clase != 'cancelada':
                hora_llegada_time = datetime.strptime(hora_llegada, '%H:%M').time()
                
            # Crear un nuevo registro
            nueva_clase = ClaseRealizada(
                fecha=fecha_registro,  # Use the selected date instead of today
                horario_id=horario_id,
                profesor_id=profesor_id,
                hora_llegada_profesor=hora_llegada_time,
                cantidad_alumnos=cantidad_alumnos,
                observaciones=observaciones
            )
            
            # Verificar si hay un archivo de audio temporal para este horario
            audio_file = None
            for ext in ['mp3', 'wav', 'ogg']:
                temp_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), f'temp_horario_{horario_id}.{ext}')
                if os.path.exists(temp_path):
                    # Guardar el archivo definitivo
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    new_filename = f'clase_{horario_id}_{timestamp}.{ext}'
                    new_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), new_filename)
                    
                    # Asegurar que el directorio existe
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    
                    # Mover el archivo temporal al definitivo
                    try:
                        os.rename(temp_path, new_path)
                    except Exception as e:
                        import shutil
                        shutil.copy2(temp_path, new_path)
                        os.remove(temp_path)
                    
                    nueva_clase.audio_file = new_filename
                    break
            
            db.session.add(nueva_clase)
            db.session.commit()
            
            # Limpiar caché de métricas para este profesor
            from models import clear_metrics_cache
            clear_metrics_cache(profesor_id)
            
            # Mostrar mensaje de éxito con la fecha
            fecha_str = fecha_registro.strftime('%d/%m/%Y')
            flash(f'Registro de asistencia para el {fecha_str} guardado correctamente', 'success')
            return redirect(url_for('control_asistencia'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el registro: {str(e)}', 'error')
    
    # Obtener todos los profesores para el selector
    profesores = Profesor.query.all()
    
    return render_template('asistencia/registrar.html', horario=horario, hoy=hoy, fecha=hoy, profesores=profesores)

@app.route('/asistencia/editar/<int:id>', methods=['GET', 'POST'])
def editar_asistencia(id):
    clase_realizada = ClaseRealizada.query.get_or_404(id)
    
    if request.method == 'POST':
        # Obtener el estado de la clase del formulario
        estado_clase = request.form.get('estado_clase', 'normal')
        
        # Inicializar variables
        hora_llegada = None
        cantidad_alumnos = 0
        observaciones = ""
        profesor_id = clase_realizada.profesor_id  # Default al profesor actual
        
        # Actualizar fecha en cualquier caso
        if request.form['fecha']:
            nueva_fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            clase_realizada.fecha = nueva_fecha
        
        # Procesar según el tipo de estado seleccionado
        if estado_clase == 'normal':
            # Clase normal con profesor regular
            if request.form.get('hora_llegada'):
                hora_llegada = datetime.strptime(request.form['hora_llegada'], '%H:%M').time()
            
            cantidad_alumnos = int(request.form.get('cantidad_alumnos', 0))
            observaciones = request.form.get('observaciones', '')
            profesor_id = request.form.get('profesor_id') or profesor_id
            
        elif estado_clase == 'suplencia':
            # Clase con profesor suplente
            if request.form.get('hora_llegada_suplente'):
                hora_llegada = datetime.strptime(request.form['hora_llegada_suplente'], '%H:%M').time()
            
            cantidad_alumnos = int(request.form.get('cantidad_alumnos_suplencia', 0))
            motivo_suplencia = request.form.get('motivo_suplencia', 'otro')
            profesor_id = request.form.get('profesor_suplente') or profesor_id
            observaciones = f"SUPLENCIA - Motivo: {motivo_suplencia} - " + request.form.get('observaciones', '')
            
        elif estado_clase == 'cancelada':
            # Clase cancelada
            hora_llegada = None  # No hay llegada en clases canceladas
            cantidad_alumnos = 0  # No hay alumnos en clases canceladas
            motivo_ausencia = request.form.get('motivo_ausencia', 'otro')
            aviso_alumnos = request.form.get('aviso_alumnos', 'no')
            observaciones = f"CLASE CANCELADA - Motivo: {motivo_ausencia} - Aviso: {aviso_alumnos} - " + request.form.get('observaciones', '')
        
        # Actualizar los datos en la base de datos
        clase_realizada.hora_llegada_profesor = hora_llegada
        clase_realizada.cantidad_alumnos = cantidad_alumnos
        clase_realizada.observaciones = observaciones
        clase_realizada.profesor_id = int(profesor_id) if profesor_id else clase_realizada.profesor_id
        
        db.session.commit()
        
        # Limpiar caché de métricas para este profesor
        from models import clear_metrics_cache
        clear_metrics_cache(clase_realizada.profesor_id)
        
        flash('Registro de asistencia actualizado con éxito', 'success')
        
        # Redireccionar según la fecha de la clase actualizada
        hoy = datetime.now().date()
        if clase_realizada.fecha == hoy:
            return redirect(url_for('control_asistencia'))
        else:
            return redirect(url_for('historial_asistencia'))
    
    # Obtener todos los profesores para el selector
    profesores = Profesor.query.all()
    
    # Obtener la fecha actual para compararla en la plantilla
    hoy = datetime.now().date()
    
    return render_template('asistencia/editar.html', clase=clase_realizada, profesores=profesores, hoy=hoy)

@app.route('/asistencia/eliminar/<int:id>')
def eliminar_asistencia(id):
    try:
        # Use a fresh session to avoid "already attached to session" errors
        # First try to get the class ID without attaching it to a session
        clase_id = id
        
        # Get audio file path and profesor_id before deletion
        audio_path = None
        profesor_id = None
        try:
            clase = ClaseRealizada.query.filter_by(id=clase_id).first()
            if clase:
                if clase.audio_file:
                    audio_path = clase.audio_file
                profesor_id = clase.profesor_id
        except Exception as e:
            app.logger.warning(f"Error retrieving audio file before deletion: {str(e)}")
        
        # Use execute() with parameters to avoid SQL injection
        db.session.execute("DELETE FROM clase_realizada WHERE id = :id", {"id": clase_id})
        db.session.commit()
        
        # If there was an audio file, try to delete it
        if audio_path:
            try:
                full_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), audio_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    app.logger.info(f"Deleted audio file: {full_path}")
            except Exception as e:
                app.logger.error(f"Error deleting audio file: {str(e)}")
        
        # Limpiar caché de métricas para este profesor si tenemos su ID
        if profesor_id:
            try:
                from models import clear_metrics_cache
                clear_metrics_cache(profesor_id)
                app.logger.info(f"Cleared metrics cache for profesor_id: {profesor_id}")
            except Exception as e:
                app.logger.error(f"Error clearing metrics cache: {str(e)}")
        
        flash('Registro de asistencia eliminado con éxito', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el registro: {str(e)}', 'danger')
        app.logger.error(f"Error in eliminar_asistencia: {str(e)}")
    
    return redirect(url_for('control_asistencia'))

@app.route('/asistencia/historial')
def historial_asistencia():
    # Parámetros de filtro
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    profesor_id = request.args.get('profesor_id')
    
    # Fecha por defecto: últimos 7 días
    hoy = datetime.now().date()
    fecha_inicio = hoy - timedelta(days=7)
    fecha_fin = hoy
    
    # Aplicar filtros si existen
    if fecha_inicio_str:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    
    if fecha_fin_str:
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    
    # Construir la consulta
    query = ClaseRealizada.query.filter(
        ClaseRealizada.fecha >= fecha_inicio,
        ClaseRealizada.fecha <= fecha_fin
    ).order_by(ClaseRealizada.fecha.desc(), ClaseRealizada.id.desc())
    
    if profesor_id and profesor_id != 'todos':
        query = query.filter_by(profesor_id=int(profesor_id))
    
    clases_realizadas = query.all()
    profesores = Profesor.query.all()
    
    return render_template('asistencia/historial.html',
                           clases_realizadas=clases_realizadas,
                           profesores=profesores,
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           profesor_id=profesor_id)

@app.route('/asistencia/clases-no-registradas')
def clases_no_registradas():
    """
    Muestra un historial de clases que no fueron registradas en su día
    para facilitar su registro posterior
    """
    # Parámetros de filtro
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    profesor_id = request.args.get('profesor_id')
    refresh = request.args.get('refresh')  # Usar para forzar actualización
    clear_cache = request.args.get('clear_cache')  # Para forzar limpieza de caché
    
    # Mensaje de depuración
    timestamp_actual = int(time_module.time())
    print(f"DEBUG: Ejecutando clases_no_registradas con timestamp: {timestamp_actual}, refresh: {refresh}, clear_cache: {clear_cache}")
    
    # Si se solicita limpiar la caché, forzar una actualización de la sesión
    if clear_cache == '1':
        print("DEBUG: Limpiando caché de la sesión")
        # Forzar sincronización de la base de datos
        db.session.commit()
        # Cerrar y reabrir la sesión
        db.session.close()
        db.session = db.create_scoped_session()
        # Limpiar también la caché de SQLAlchemy
        db.session.expire_all()
    
    # Fecha por defecto: últimos 30 días
    hoy = datetime.now().date()
    fecha_inicio = hoy - timedelta(days=30)
    fecha_fin = hoy - timedelta(days=1)  # Hasta ayer
    
    # Aplicar filtros si existen
    if fecha_inicio_str:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    
    if fecha_fin_str:
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    
    # 1. Obtener todos los horarios activos utilizando una consulta más completa y directa
    # Obtener todos los horarios sin filtrar por activo
    sql_horarios = """
        SELECT h.id, h.nombre, h.hora_inicio, h.tipo_clase, h.dia_semana, h.profesor_id, h.duracion
        FROM horario_clase h 
        ORDER BY h.nombre
    """
    app.logger.info("Ejecutando consulta SQL para todos los horarios...")
    result_horarios = db.session.execute(sql_horarios)
    
    horarios_activos = []
    for row in result_horarios:
        # Procesar todos los horarios
        # (Se eliminó código de filtrado por activo/inactivo)
            
        # Extraer la hora_inicio de la base de datos
        hora_inicio_original = row.hora_inicio
        
        # Establecer valores predeterminados
        hora_inicio = None
        hora_inicio_str = None
        
        # Procesar hora_inicio según su tipo
        if hora_inicio_original:
            if isinstance(hora_inicio_original, time):
                # Si es un objeto time, formatear directamente
                hora_inicio = hora_inicio_original  # Mantener el objeto time para ordenar
                hora_inicio_str = hora_inicio_original.strftime('%H:%M')
            elif isinstance(hora_inicio_original, str):
                # Si es una cadena, intentar extraer solo la parte HH:MM
                if ':' in hora_inicio_original:
                    partes = hora_inicio_original.split(':')
                    if len(partes) >= 2:
                        try:
                            horas = int(partes[0])
                            minutos = int(partes[1])
                            # Crear objeto time para ordenamiento y cálculos
                            hora_inicio = time(hour=horas, minute=minutos)
                            hora_inicio_str = f"{horas:02d}:{minutos:02d}"
                        except (ValueError, TypeError):
                            # Si hay error, intentar convertir usando datetime
                            try:
                                dt = datetime.strptime(hora_inicio_original.split('.')[0], '%H:%M:%S')
                                hora_inicio = dt.time()
                                hora_inicio_str = dt.strftime('%H:%M')
                            except:
                                # Si no podemos convertir, usar valores predeterminados
                                hora_inicio = time(hour=0, minute=0)  # 00:00 como fallback
                                hora_inicio_str = "00:00"
                else:
                    # No contiene ":", usar valores predeterminados
                    hora_inicio = time(hour=0, minute=0)
                    hora_inicio_str = "00:00"
            else:
                # Si no hay hora_inicio, usar valores predeterminados
                hora_inicio = time(hour=0, minute=0)
                hora_inicio_str = "00:00"
        
        # Calcular la hora de finalización
        duracion = getattr(row, 'duracion', 60)
        hora_fin_str = calcular_hora_fin(hora_inicio, duracion)
        
        # Crear el objeto horario con los datos procesados
        horario = {
            'id': row.id,
            'nombre': row.nombre,
            'hora_inicio': hora_inicio_str,  # ¡Importante! Guardar siempre el string formateado
            'hora_inicio_obj': hora_inicio,  # Mantener el objeto time para ordenamiento
            'tipo_clase': row.tipo_clase,
            'dia_semana': row.dia_semana,
            'profesor_id': row.profesor_id,
            'duracion': duracion,
            'hora_fin_str': hora_fin_str
        }
        
        # Verificar si es clase POWER BIKE para depuración
        if "POWER BIKE" in row.nombre:
            print(f"DETECTADA CLASE POWER BIKE en horarios_activos: ID={row.id}, hora_inicio_str={hora_inicio_str}, hora_inicio_obj={hora_inicio}")
            
        horarios_activos.append(horario)
    
    # 2. Generar todas las fechas en el rango
    fechas = []
    fecha_actual = fecha_inicio
    while fecha_actual <= fecha_fin:
        fechas.append(fecha_actual)
        fecha_actual += timedelta(days=1)
    
    # 3. Crear un diccionario de clases ya registradas para búsqueda eficiente
    # Formato: {(fecha, horario_id): True}
    clases_registradas_dict = {}
    
    # Obtener todas las clases registradas en el período - USANDO CONSULTA FRESCA
    # Evitar usar ORM para asegurar que obtenemos los datos más recientes
    sql_clases = """
    SELECT 
        cr.id, cr.fecha, cr.horario_id, cr.profesor_id, cr.hora_llegada_profesor, 
        cr.cantidad_alumnos, cr.observaciones, cr.audio_file, cr.fecha_registro,
        hc.nombre, hc.hora_inicio, hc.tipo_clase, hc.duracion,
        p.nombre as profesor_nombre, p.apellido as profesor_apellido, p.tarifa_por_clase
    FROM clase_realizada cr
    JOIN horario_clase hc ON cr.horario_id = hc.id
    JOIN profesor p ON cr.profesor_id = p.id
    WHERE cr.fecha >= :fecha_inicio AND cr.fecha <= :fecha_fin
    ORDER BY cr.fecha, hc.hora_inicio
    """
    # Crear una conexión fresca para asegurar que no hay caché
    connection = db.engine.connect()
    result = connection.execute(sql_clases, {
        'fecha_inicio': fecha_inicio, 
        'fecha_fin': fecha_fin
    })
    
    # Procesar los resultados de la consulta directa
    clases_realizadas = []
    for row in result:
        fecha_clase = row[1]
        horario_id = row[2]
        
        # Verificar que fecha_clase sea un objeto date
        if isinstance(fecha_clase, str):
            try:
                fecha_clase = datetime.strptime(fecha_clase, '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha_clase = datetime.strptime(fecha_clase, '%d/%m/%Y').date()
                except ValueError:
                    # Si no podemos convertir, usar la fecha actual
                    fecha_clase = datetime.now().date()
        
        # Guardar la clase realizada
        clases_realizadas.append({
            'id': row[0],
            'fecha': fecha_clase,
            'horario_id': horario_id,
            'profesor_id': row[3]
        })
        
        # Agregar al diccionario para búsqueda rápida
        key = (fecha_clase, horario_id)
        clases_registradas_dict[key] = True
        
        # También añadir a clases_registradas_dict con fecha como string (YYYY-MM-DD)
        # para manejar diferentes formatos de fecha en las comparaciones
        key_str = (fecha_clase.strftime('%Y-%m-%d'), horario_id)
        clases_registradas_dict[key_str] = True
        
        print(f"DEBUG: Clase registrada encontrada - Fecha: {fecha_clase}, Horario ID: {horario_id}, ID: {row[0]}")
    
    # Cerrar la conexión después de usarla
    connection.close()
    
    # 4. Generar las clases esperadas que NO están registradas
    clases_no_registradas = []
    for horario in horarios_activos:
        # Todos los horarios son considerados activos
        for fecha in fechas:
            # Verificar que fecha sea un objeto date
            if not isinstance(fecha, date):
                try:
                    fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    continue  # Saltar esta fecha si no podemos convertirla
            
            # Si el día de la semana coincide con el día del horario
            if fecha.weekday() == horario['dia_semana']:
                # Comprobar con múltiples formatos de clave para mayor seguridad
                key = (fecha, horario['id'])
                key_str = (fecha.strftime('%Y-%m-%d'), horario['id'])
                
                # Verificar si esta clase no está registrada usando ambas claves
                if key not in clases_registradas_dict and key_str not in clases_registradas_dict:
                    # Obtener información del profesor
                    sql_profesor = "SELECT id, nombre, apellido FROM profesor WHERE id = :profesor_id"
                    result_profesor = db.session.execute(sql_profesor, {'profesor_id': horario['profesor_id']}).fetchone()
                    
                    if result_profesor:
                        profesor = {
                            'id': result_profesor.id,
                            'nombre': result_profesor.nombre,
                            'apellido': result_profesor.apellido
                        }
                    else:
                        profesor = {
                            'id': 0,
                            'nombre': 'Desconocido',
                            'apellido': ''
                        }
                    
                    # Asegurarse de que fecha sea un objeto datetime.date
                    if not isinstance(fecha, date):
                        try:
                            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            try:
                                fecha = datetime.strptime(fecha, '%d/%m/%Y').date()
                            except (ValueError, TypeError):
                                fecha = datetime.now().date()
                    
                    # No es necesario procesar más el horario, ya viene con el formato correcto
                    horario_formateado = horario.copy()
                    
                    # Creamos un objeto para representar la clase esperada
                    clase_esperada = {
                        'fecha': fecha,
                        'horario': horario_formateado,
                        'profesor': profesor,
                        'tipo_clase': horario['tipo_clase'],
                        'id_combinado': f"{fecha.strftime('%Y-%m-%d')}|{horario['id']}"
                    }
                    clases_no_registradas.append(clase_esperada)
    
    # Mensaje de depuración con el número de clases
    print(f"DEBUG: Total de clases registradas: {len(clases_realizadas)}")
    print(f"DEBUG: Total de clases no registradas: {len(clases_no_registradas)}")
    
    # Ordenar por fecha (más reciente primero) y luego por hora de inicio
    clases_no_registradas.sort(key=lambda x: (x['fecha'], x['horario'].get('hora_inicio_obj', time(0, 0))))
    
    profesores = Profesor.query.all()
    
    return render_template('asistencia/clases_no_registradas.html',
                           clases_no_registradas=clases_no_registradas,
                           profesores=profesores,
                           fecha_inicio=fecha_inicio,
                           fecha_fin=fecha_fin,
                           profesor_id=profesor_id)

# Rutas para Informes
@app.route('/informes')
def informes():
    return render_template('informes/index.html')

# Función para calcular la hora de finalización como string (definida globalmente)
def calcular_hora_fin(hora_inicio, duracion=60):
    if not hora_inicio:
        return "N/A"
    
    if isinstance(hora_inicio, str):
        try:
            hora_inicio = datetime.strptime(hora_inicio, '%H:%M:%S').time()
        except ValueError:
            try:
                hora_inicio = datetime.strptime(hora_inicio, '%H:%M').time()
            except ValueError:
                return "N/A"
    
    minutos_totales = hora_inicio.hour * 60 + hora_inicio.minute + duracion
    horas, minutos = divmod(minutos_totales, 60)
    # Ajuste para asegurar que las horas estén en el formato de 24 horas (0-23)
    horas = horas % 24
    return f"{horas:02d}:{minutos:02d}"
    
def limpiar_formato_hora(hora_input):
    """
    Limpia y formatea cualquier tipo de entrada de hora al formato HH:MM.
    Maneja objetos time, strings en varios formatos y casos especiales.
    """
    if hora_input is None:
        return "N/A"
    
    # Caso 1: Es objeto time
    if isinstance(hora_input, time):
        return hora_input.strftime('%H:%M')
    
    # Caso 2: Es una cadena
    if isinstance(hora_input, str):
        if not hora_input:
            return "N/A"
        
        # Eliminar cualquier parte de microsegundos
        if '.' in hora_input:
            hora_input = hora_input.split('.')[0]
        
        # Extraer solo horas y minutos si contiene colones
        if ':' in hora_input:
            partes = hora_input.split(':')
            if len(partes) >= 2:
                try:
                    horas = int(partes[0])
                    minutos = int(partes[1])
                    return f"{horas:02d}:{minutos:02d}"
                except (ValueError, TypeError):
                    pass  # Si hay error, seguimos con otros métodos
        
        # Intentar interpretar como un formato de hora estándar
        try:
            parsed_time = datetime.strptime(hora_input, '%H:%M:%S').time()
            return parsed_time.strftime('%H:%M')
        except ValueError:
            try:
                parsed_time = datetime.strptime(hora_input, '%H:%M').time()
                return parsed_time.strftime('%H:%M')
            except ValueError:
                pass  # Si hay error, seguimos con otros métodos
    
    # Caso 3: Es un tipo desconocido o no se pudo formatear
    # Intentar convertir a string y luego hacer limpieza básica
    try:
        hora_str = str(hora_input)
        if ':' in hora_str:
            partes = hora_str.split(':')
            if len(partes) >= 2:
                return f"{int(partes[0]):02d}:{int(partes[1]):02d}"
    except:
        pass
    
    # Si nada funciona, devolvemos un valor predeterminado
    return "00:00"

@app.route('/informes/mensual', methods=['GET', 'POST'])
def informe_mensual():
    # Diccionario de nombres de meses en español
    MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Función para calcular la puntualidad
    def calcular_puntualidad(hora_llegada, hora_inicio, nombre_clase=""):
        if not hora_llegada:
            return "N/A"
        
        # Si hora_inicio es None, no podemos calcular la puntualidad
        if hora_inicio is None:
            print("⚠️ ADVERTENCIA: hora_inicio es None, no se puede calcular puntualidad")
            return "N/A"
        
        # Registrar en el log los tipos de datos (debug desactivado)
        # Comentado para producción
        
        # CORRECCIÓN ESPECÍFICA PARA POWER BIKE
        if nombre_clase and "POWER BIKE" in nombre_clase:
            # Crear una nueva hora_inicio fija de 7:30
            hora_correcta = time(hour=7, minute=30)
            # Log eliminado para producción
            hora_inicio = hora_correcta
        
        # Convertir las horas usando nuestra función global
        hora_llegada_convertida = convertir_hora_con_microsegundos(hora_llegada)
        if not hora_llegada_convertida:
            return "Error formato"
        
        hora_inicio_convertida = convertir_hora_con_microsegundos(hora_inicio)
        if not hora_inicio_convertida:
            return "Error formato"
        
        # Usar las horas convertidas
        hora_llegada = hora_llegada_convertida
        hora_inicio = hora_inicio_convertida
        
        # Calcular minutos de retraso (asegurando que ambos son objetos time)
        
        # Verificar si son exactamente iguales (caso especial)
        
        # Corregir la comparación: el profesor es puntual solo si llega a tiempo o antes
        if hora_llegada <= hora_inicio:
            diferencia = (
                datetime.combine(date.min, hora_inicio) - 
                datetime.combine(date.min, hora_llegada)
            ).total_seconds() / 60
            # El profesor llegó puntual
            return "Puntual"
        
        # Calcular minutos de retraso
        diferencia_minutos = (
            datetime.combine(date.min, hora_llegada) - 
            datetime.combine(date.min, hora_inicio)
        ).total_seconds() / 60
        
        resultado = ""
        if diferencia_minutos <= 10:
            resultado = "Retraso leve"
        else:
            resultado = "Retraso significativo"
        
        return resultado

    # Para peticiones GET con parámetros
    if request.method == 'GET' and request.args.get('mes') and request.args.get('anio'):
        mes = int(request.args.get('mes'))
        anio = int(request.args.get('anio'))
        
        # Obtener el primer y último día del mes
        primer_dia = date(anio, mes, 1)
        ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
        
    elif request.method == 'POST':
        mes = int(request.form['mes'])
        anio = int(request.form['anio'])
        
        # Obtener el primer y último día del mes
        primer_dia = date(anio, mes, 1)
        ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
        
    else:
        # Para peticiones GET sin parámetros, mostrar el formulario
        hoy = datetime.now()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        # Initialize empty variables for template to avoid Jinja2 UndefinedError
        conteo_tipos = {'MOVE': 0, 'RIDE': 0, 'BOX': 0, 'OTRO': 0}
        alumnos_tipos = {'MOVE': 0, 'RIDE': 0, 'BOX': 0, 'OTRO': 0}
        
        return render_template('informes/mensual.html', 
                              mes_actual=mes_actual, 
                              anio_actual=anio_actual,
                              # Pass empty dictionaries to avoid undefined errors
                              conteo_tipos=conteo_tipos,
                              alumnos_tipos=alumnos_tipos)
    
    # Esta parte se ejecuta tanto para POST como para GET con parámetros
    # Limpiar caché de la sesión
    db.session.commit()
    db.session.close()
    db.session = db.create_scoped_session()
    
    # Consultar clases realizadas en el rango de fechas usando SQL directo
    # para evitar problemas de caché
    sql_clases = """
    SELECT 
        cr.id, cr.fecha, cr.horario_id, cr.profesor_id, cr.hora_llegada_profesor, 
        cr.cantidad_alumnos, cr.observaciones, cr.audio_file, cr.fecha_registro,
        hc.nombre, hc.hora_inicio, hc.tipo_clase, hc.duracion,
        p.nombre as profesor_nombre, p.apellido as profesor_apellido, p.tarifa_por_clase
    FROM clase_realizada cr
    JOIN horario_clase hc ON cr.horario_id = hc.id
    JOIN profesor p ON cr.profesor_id = p.id
    WHERE cr.fecha >= :fecha_inicio AND cr.fecha <= :fecha_fin
    ORDER BY cr.fecha, hc.hora_inicio
    """
    
    # Agregar debug para ver resultados
    print(f"Consulta de clases para {primer_dia} a {ultimo_dia}")
    
    # Crear una conexión fresca para asegurar que no hay caché
    connection = db.engine.connect()
    result_clases = connection.execute(sql_clases, {
        'fecha_inicio': primer_dia,
        'fecha_fin': ultimo_dia
    })
    
    # Función para convertir string a time
    def convertir_a_time(hora_str):
        if not hora_str:
            return None
                
        # Si ya es un objeto time, devolverlo directamente
        if isinstance(hora_str, time):
            return hora_str
                
        # Intentar convertir string a time
        try:
            return datetime.strptime(hora_str, '%H:%M:%S.%f').time()
        except ValueError:
            try:
                return datetime.strptime(hora_str, '%H:%M:%S').time()
            except ValueError:
                try:
                    return datetime.strptime(hora_str, '%H:%M').time()
                except ValueError:
                    print(f"ERROR: No se pudo convertir {hora_str} a time")
                    return None
    
    # Procesar los resultados y crear objetos para facilitar el manejo
    clases_realizadas = []
    for row in result_clases:
        # Asegurarse de que fecha sea un objeto datetime.date
        fecha = row.fecha
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                try:
                    fecha = datetime.strptime(fecha, '%d/%m/%Y').date()
                except ValueError:
                    fecha = datetime.now().date()

        # Asegurarse de que hora_llegada_profesor sea un objeto time
        hora_llegada = row.hora_llegada_profesor
        if hora_llegada:
            if isinstance(hora_llegada, str):
                hora_llegada = convertir_a_time(hora_llegada)
        else:
            hora_llegada = None

        # Obtener hora_inicio conservando el valor original cuando está disponible
        hora_inicio_original = row.hora_inicio
        hora_inicio = None
        
        # Verificar la hora de llegada para situaciones especiales
        hora_llegada_str = None
        if hora_llegada:
            try:
                hora_llegada_str = hora_llegada.strftime('%H:%M')
            except:
                print(f"ERROR al formatear hora_llegada: {hora_llegada}")
        
        # Procesar la hora de inicio para comparaciones de puntualidad
        if hora_inicio_original:
            # Usar nuestra función global para convertir
            hora_inicio = convertir_hora_con_microsegundos(hora_inicio_original)
            if hora_inicio:
                print(f"DEBUG informe_mensual: Clase ID {row.id}, convertida hora_inicio_original={hora_inicio_original} a {hora_inicio}")
            else:
                print(f"ADVERTENCIA: Clase ID {row.id} tiene hora_inicio en formato inválido: {hora_inicio_original}")
        else:
            print(f"ADVERTENCIA: Clase ID {row.id} no tiene hora_inicio definida en horario")
            # Si tenemos la hora de llegada, NO la usamos como hora de inicio para puntualidad
            # Esta es la causa del problema: la hora de llegada no debe ser la referencia para
            # calcular la puntualidad
            
            # CORRECCIÓN ESPECÍFICA PARA POWER BIKE
            nombre_horario = row.nombre if hasattr(row, 'nombre') else "Sin nombre"
            if "POWER BIKE" in nombre_horario:
                # Para POWER BIKE, sabemos que la hora de inicio es 7:30
                hora_inicio = time(hour=7, minute=30)
                print(f"CORRECCIÓN: Clase POWER BIKE, usando hora fija 7:30 como hora de inicio")
            else:
                # Intentamos extraer la hora del nombre del horario
                import re
                hora_match = re.search(r'(\d{1,2})[:.:](\d{2})', nombre_horario)
                if hora_match:
                    hora, minuto = map(int, hora_match.groups())
                    hora_inicio = time(hour=hora, minute=minuto)
                    print(f"Hora extraída del nombre: {hora_inicio}")
                else:
                    # Si no se puede extraer, dejamos la hora_inicio como None para mostrar un error claro
                    print(f"ADVERTENCIA: No se pudo determinar la hora de inicio para '{nombre_horario}'")
                    hora_inicio = time(hour=0, minute=0)  # Usar 00:00 como valor por defecto

        # Obtener la duración o usar valor por defecto
        duracion = getattr(row, 'duracion', 60)
        
        # Calcular la hora de finalización como string
        if hora_inicio:
            hora_fin_str = calcular_hora_fin(hora_inicio, duracion)
            # Formatear hora_inicio como string para la plantilla
            try:
                hora_inicio_str = hora_inicio.strftime('%H:%M')
                print(f"DEBUG hora_inicio_str: {hora_inicio_str}")
            except:
                print(f"ERROR formateando hora_inicio: {hora_inicio}, tipo: {type(hora_inicio)}")
                hora_inicio_str = None
        else:
            # Si llegamos aquí y no tenemos hora_inicio, intentamos usar directamente el valor original
            # en los casos en que sea un string ya formateado
            if isinstance(hora_inicio_original, str) and (':' in hora_inicio_original):
                hora_inicio_str = hora_inicio_original
                # Calcular hora_fin manualmente
                try:
                    hora, minuto = map(int, hora_inicio_str.split(':')[:2])
                    minutos_totales = hora * 60 + minuto + duracion
                    horas_fin, minutos_fin = divmod(minutos_totales, 60)
                    hora_fin_str = f"{horas_fin:02d}:{minutos_fin:02d}"
                except:
                    print(f"ERROR calculando hora_fin a partir de string: {hora_inicio_original}")
                    hora_fin_str = "Horario no disponible"
            else:
                hora_inicio_str = None
                hora_fin_str = "Horario no disponible"

        # Para la puntualidad usamos la hora del horario original
        hora_para_puntualidad = hora_inicio
        
        # IMPORTANTE: Verificar que la hora para puntualidad no sea la misma que la hora de llegada
        if hora_llegada and hora_para_puntualidad and hora_llegada == hora_para_puntualidad:
            print(f"⚠️ ADVERTENCIA: hora_llegada y hora_para_puntualidad son IGUALES para clase ID {row.id}")
            print(f"Esto podría indicar un problema en cómo se calculó la hora de inicio")
        
        # Registrar en el log para depuración la comparación de puntualidad
        if hora_llegada and hora_para_puntualidad:
            print(f"DEBUG puntualidad informe: Clase ID {row.id}, hora_llegada={hora_llegada}, hora_para_puntualidad={hora_para_puntualidad}")
            diferencia = (datetime.combine(date.min, hora_llegada) - datetime.combine(date.min, hora_para_puntualidad)).total_seconds() / 60
            print(f"DEBUG puntualidad informe: Diferencia en minutos={diferencia}, resultado={calcular_puntualidad(hora_llegada, hora_para_puntualidad, row.nombre)}")

        # Crear un objeto para representar la clase realizada
        clase = {
            'id': row.id,
            'fecha': fecha,
            'horario_id': row.horario_id,
            'hora_llegada_profesor': hora_llegada,
            'hora_llegada_str': hora_llegada_str,
            'cantidad_alumnos': row.cantidad_alumnos,
            'observaciones': row.observaciones,
            'fecha_registro': row.fecha_registro,
            'horario': {
                'id': row.horario_id,
                'nombre': row.nombre,
                'hora_inicio': hora_inicio,
                'hora_inicio_str': hora_inicio_str,
                'tipo_clase': row.tipo_clase,
                'duracion': duracion,
                'hora_fin_str': hora_fin_str
            },
            'profesor': {
                'id': row.profesor_id,
                'nombre': row.profesor_nombre,
                'apellido': row.profesor_apellido,
                'tarifa_por_clase': row.tarifa_por_clase
            }
        }
        
        # Para POWER BIKE, establecemos la hora específica antes de calcular la puntualidad
        if "POWER BIKE" in row.nombre:
            print(f"CORRIGIENDO CLASE POWER BIKE para informe: ID={row.id}, hora_llegada={hora_llegada_str}")
            hora_correcta = time(hour=7, minute=30)
            clase['horario']['hora_inicio'] = hora_correcta
            clase['horario']['hora_inicio_str'] = "07:30"
            # Actualizar hora para puntualidad también
            hora_para_puntualidad = hora_correcta
            print(f"Hora corregida para POWER BIKE: {hora_correcta}")
        
        # Calcular la puntualidad después de las correcciones
        clase['puntualidad'] = calcular_puntualidad(hora_llegada, hora_para_puntualidad, row.nombre)
        
        clases_realizadas.append(clase)
    
    # Generar fechas para el mes seleccionado
    fechas_mes = []
    fecha_actual = primer_dia
    while fecha_actual <= ultimo_dia:
        fechas_mes.append(fecha_actual)
        fecha_actual += timedelta(days=1)
    
    # Crear un diccionario para verificar clases ya registradas
    # Formato: {(fecha, horario_id): True}
    clases_registradas_dict = {}
    for clase in clases_realizadas:
        key = (clase['fecha'], clase['horario_id'])
        clases_registradas_dict[key] = True
    
    # Obtener todos los horarios activos
    # Obtener todos los horarios, incluidos los inactivos pero con fecha de desactivación
    try:
        sql_horarios = """
        SELECT id, nombre, hora_inicio, tipo_clase, dia_semana, profesor_id, duracion, activo, fecha_desactivacion 
        FROM horario_clase
        """
        result_horarios = db.session.execute(sql_horarios)
    except Exception as e:
        # Si la columna activo no existe, usar versión compatible con bases de datos antiguas
        print(f"Error al ejecutar consulta con columna 'activo': {str(e)}")
        print("Usando consulta alternativa sin columna 'activo'")
        sql_horarios = """
        SELECT id, nombre, hora_inicio, tipo_clase, dia_semana, profesor_id, duracion
        FROM horario_clase
        """
        result_horarios = db.session.execute(sql_horarios)
    
    horarios_activos = []
    for row in result_horarios:
        # Extraer la hora_inicio de la base de datos
        hora_inicio_original = row.hora_inicio
        
        # Establecer valores predeterminados
        hora_inicio = None
        hora_inicio_str = None
        
        # Procesar hora_inicio según su tipo
        if hora_inicio_original:
            if isinstance(hora_inicio_original, time):
                # Si es un objeto time, formatear directamente
                hora_inicio = hora_inicio_original  # Mantener el objeto time para ordenar
                hora_inicio_str = hora_inicio_original.strftime('%H:%M')
            elif isinstance(hora_inicio_original, str):
                # Si es una cadena, intentar extraer solo la parte HH:MM
                if ':' in hora_inicio_original:
                    partes = hora_inicio_original.split(':')
                    if len(partes) >= 2:
                        try:
                            horas = int(partes[0])
                            minutos = int(partes[1])
                            # Crear objeto time para ordenamiento y cálculos
                            hora_inicio = time(hour=horas, minute=minutos)
                            hora_inicio_str = f"{horas:02d}:{minutos:02d}"
                        except (ValueError, TypeError):
                            # Si hay error, intentar convertir usando datetime
                            try:
                                dt = datetime.strptime(hora_inicio_original.split('.')[0], '%H:%M:%S')
                                hora_inicio = dt.time()
                                hora_inicio_str = dt.strftime('%H:%M')
                            except:
                                # Si no podemos convertir, usar valores predeterminados
                                hora_inicio = time(hour=0, minute=0)  # 00:00 como fallback
                                hora_inicio_str = "00:00"
                else:
                    # No contiene ":", usar valores predeterminados
                    hora_inicio = time(hour=0, minute=0)
                    hora_inicio_str = "00:00"
            else:
                # Si no hay hora_inicio, usar valores predeterminados
                hora_inicio = time(hour=0, minute=0)
                hora_inicio_str = "00:00"
        
        # Calcular la hora de finalización
        duracion = getattr(row, 'duracion', 60)
        hora_fin_str = calcular_hora_fin(hora_inicio, duracion)
        
        # Verificar si la columna activo existe en el resultado
        try:
            activo = getattr(row, 'activo', True)  # Por defecto activo=True si no existe la columna
            fecha_desactivacion = getattr(row, 'fecha_desactivacion', None)
        except:
            # Si no existe la columna activo, asumimos que está activo
            activo = True
            fecha_desactivacion = None
        
        # Crear el objeto horario con los datos procesados
        horario = {
            'id': row.id,
            'nombre': row.nombre,
            'hora_inicio': hora_inicio_str,  # ¡Importante! Guardar siempre el string formateado
            'hora_inicio_obj': hora_inicio,  # Mantener el objeto time para ordenamiento
            'tipo_clase': row.tipo_clase,
            'dia_semana': row.dia_semana,
            'profesor_id': row.profesor_id,
            'duracion': duracion,
            'hora_fin_str': hora_fin_str,
            'activo': activo,
            'fecha_desactivacion': fecha_desactivacion
        }
        
        # Verificar si es clase POWER BIKE para depuración
        if "POWER BIKE" in row.nombre:
            print(f"DETECTADA CLASE POWER BIKE en horarios_activos: ID={row.id}, hora_inicio_str={hora_inicio_str}, hora_inicio_obj={hora_inicio}")
            
        horarios_activos.append(horario)
    
    # Generar las clases que deberían haberse realizado pero no están registradas
    clases_no_registradas = []
    for horario in horarios_activos:
        for fecha in fechas_mes:
            # Si el día de la semana coincide con el día del horario
            if fecha.weekday() == horario['dia_semana']:
                key = (fecha, horario['id'])
                # Verificar si esta clase no está registrada
                if key not in clases_registradas_dict:
                    # Obtener información del profesor
                    sql_profesor = "SELECT id, nombre, apellido FROM profesor WHERE id = :profesor_id"
                    result_profesor = db.session.execute(sql_profesor, {'profesor_id': horario['profesor_id']}).fetchone()
                    
                    if result_profesor:
                        profesor = {
                            'id': result_profesor.id,
                            'nombre': result_profesor.nombre,
                            'apellido': result_profesor.apellido
                        }
                    else:
                        profesor = {
                            'id': 0,
                            'nombre': 'Desconocido',
                            'apellido': ''
                        }
                    
                    # Asegurarse de que fecha sea un objeto datetime.date
                    if not isinstance(fecha, date):
                        try:
                            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            try:
                                fecha = datetime.strptime(fecha, '%d/%m/%Y').date()
                            except (ValueError, TypeError):
                                fecha = datetime.now().date()
                    
                    # No es necesario procesar más el horario, ya viene con el formato correcto
                    horario_formateado = horario.copy()
                    
                    # Creamos un objeto para representar la clase esperada
                    clase_esperada = {
                        'fecha': fecha,
                        'horario': horario_formateado,
                        'profesor': profesor,
                        'tipo_clase': horario['tipo_clase'],
                        'id_combinado': f"{fecha.strftime('%Y-%m-%d')}|{horario['id']}"
                    }
                    clases_no_registradas.append(clase_esperada)
    
    # Ordenar las clases no registradas por fecha
    clases_no_registradas.sort(key=lambda x: (x['fecha'], x['horario'].get('hora_inicio_obj', time(0, 0))))
    
    # SOLUCIÓN ROBUSTA: Procesamiento completo de todas las horas para eliminar formatos con microsegundos
    for clase in clases_no_registradas:
        # Asegurarnos de que los datos horarios estén correctamente formateados
        if not clase['horario'].get('hora_inicio'):
            # Usar hora_inicio_str o valor por defecto 
            clase['horario']['hora_inicio'] = clase['horario'].get('hora_inicio_str', '00:00')
    
    # Inicializar variables para totales
    total_clases = {'value': 0}
    total_alumnos = {'value': 0}
    total_retrasos = {'value': 0}
    total_pagos = {'value': 0}
    
    # Calcular resumen por profesor
    resumen_profesores = {}
    # Contadores por tipo de clase
    conteo_tipos = {
        'MOVE': 0,
        'RIDE': 0,
        'BOX': 0,
        'OTRO': 0
    }
    # Alumnos por tipo de clase
    alumnos_tipos = {
        'MOVE': 0,
        'RIDE': 0,
        'BOX': 0,
        'OTRO': 0
    }
    
    for clase in clases_realizadas:
        profesor = clase['profesor']
        tipo_clase = clase['horario']['tipo_clase']
        
        # Convert cantidad_alumnos to int if it's a string
        if isinstance(clase['cantidad_alumnos'], str):
            clase['cantidad_alumnos'] = int(clase['cantidad_alumnos']) if clase['cantidad_alumnos'].isdigit() else 0
        
        # Incrementar contadores por tipo
        conteo_tipos[tipo_clase] += 1
        alumnos_tipos[tipo_clase] += clase['cantidad_alumnos']
        
        if profesor['id'] not in resumen_profesores:
            resumen_profesores[profesor['id']] = {
                'profesor': profesor,
                'total_clases': 0,
                'total_alumnos': 0,
                'total_retrasos': 0,
                'pago_total': 0.0,
                'clases_por_tipo': {
                    'MOVE': 0,
                    'RIDE': 0,
                    'BOX': 0,
                    'OTRO': 0
                },
                'alumnos_por_tipo': {
                    'MOVE': 0,
                    'RIDE': 0,
                    'BOX': 0,
                    'OTRO': 0
                }
            }
        resumen_profesores[profesor['id']]['total_clases'] += 1
        
        # Ensure cantidad_alumnos is an integer
        if isinstance(clase['cantidad_alumnos'], str):
            clase['cantidad_alumnos'] = int(clase['cantidad_alumnos']) if clase['cantidad_alumnos'].isdigit() else 0
            
        resumen_profesores[profesor['id']]['total_alumnos'] += clase['cantidad_alumnos']
        resumen_profesores[profesor['id']]['clases_por_tipo'][tipo_clase] += 1
        resumen_profesores[profesor['id']]['alumnos_por_tipo'][tipo_clase] += clase['cantidad_alumnos']
        
        # Determinar la hora a considerar para la puntualidad (la de la clase si está disponible, sino la del horario)
        hora_para_puntualidad = clase['horario']['hora_inicio']
        
        # Verificar si hubo retraso
        if clase['hora_llegada_profesor'] and hora_para_puntualidad and clase['hora_llegada_profesor'] > hora_para_puntualidad:
            resumen_profesores[profesor['id']]['total_retrasos'] += 1
        
        # Ensure cantidad_alumnos is treated as a number for the comparison
        alumnos_count = clase['cantidad_alumnos']
        if isinstance(alumnos_count, str):
            alumnos_count = int(alumnos_count) if alumnos_count.isdigit() else 0
        
        # Check if the class was cancelled based on observations or ausencia_profesor flag
        observaciones = clase.get('observaciones', '').upper()
        clase_cancelada = clase.get('ausencia_profesor', False) or any(keyword in observaciones for keyword in [
            'CLASE CANCELADA', 
            'CANCELAD', 
            'CANCEL', 
            'SUSPENDID', 
            'NO IMPARTID',
            'NO SE IMPARTIÓ',
            'NO SE REALIZÓ'
        ])
        
        # Add a status attribute to clearly identify canceled classes
        if clase_cancelada:
            clase['estado'] = "CANCELADA"
        elif not clase.get('hora_llegada_profesor'):
            # If there's no arrival time, mark as CANCELED
            clase['estado'] = "CANCELADA"
            # Add this class to the list of canceled classes
            if not clase.get('ausencia_profesor'):
                clase['ausencia_profesor'] = True
                # Add an observation if none exists
                add_note = "ATENCIÓN: No se registró hora de llegada del profesor. Clase CANCELADA."
                if clase.get('observaciones'):
                    if "No se registró hora de llegada" not in clase.get('observaciones'):
                        clase['observaciones'] = add_note + " " + clase.get('observaciones')
                else:
                    clase['observaciones'] = add_note
        elif clase.get('profesor_suplente'):
            clase['estado'] = "SUPLENCIA"
        else:
            clase['estado'] = "NORMAL"
        
        # Payment calculation:
        # - If class was cancelled or no arrival time: 0% pay
        # - If teacher attended but no students: 50% pay
        # - Normal class with students: 100% pay
        if clase_cancelada or not clase.get('hora_llegada_profesor'):
            pago_clase = 0  # No payment for canceled classes or no arrival time
        else:
            # Ensure cantidad_alumnos is treated as a number for the comparison
            alumnos_count = clase['cantidad_alumnos']
            if isinstance(alumnos_count, str):
                alumnos_count = int(alumnos_count) if alumnos_count.isdigit() else 0
                
            # Teacher showed up (has arrival time) but no students: 50% pay
            pago_clase = profesor['tarifa_por_clase'] / 2 if alumnos_count == 0 else profesor['tarifa_por_clase']
        
        # Store the individual payment per class
        clase['pago_calculado'] = pago_clase
        
        # Añadir al total del profesor
        resumen_profesores[profesor['id']]['pago_total'] += pago_clase
    
    # Calcular totales globales si hay datos
    if resumen_profesores:
        for profesor_id, datos in resumen_profesores.items():
            total_clases['value'] += datos['total_clases']
            total_alumnos['value'] += datos['total_alumnos']
            total_retrasos['value'] += datos['total_retrasos']
            total_pagos['value'] += datos['pago_total']
    
    # Contadores de clases no registradas por tipo
    conteo_no_registradas = {
        'MOVE': 0,
        'RIDE': 0,
        'BOX': 0,
        'OTRO': 0,
        'total': len(clases_no_registradas)
    }
    
    for clase in clases_no_registradas:
        tipo_clase = clase['tipo_clase']
        conteo_no_registradas[tipo_clase] += 1
    
    # The morning/afternoon classification logic has been removed
    
    return render_template('informes/mensual_resultado.html', 
                          mes=mes, 
                          anio=anio, 
                          clases_realizadas=clases_realizadas,
                          clases_no_registradas=clases_no_registradas,
                          conteo_no_registradas=conteo_no_registradas,
                          resumen_profesores=resumen_profesores,
                          nombre_mes=MESES_ES[mes],
                          conteo_tipos=conteo_tipos,
                          alumnos_tipos=alumnos_tipos,
                          total_clases=total_clases,
                          total_alumnos=total_alumnos,
                          total_retrasos=total_retrasos,
                          total_pagos=total_pagos)

# Rutas para la importación de Excel

@app.route('/importar/asistencia', methods=['GET', 'POST'])
def importar_asistencia():
    """Ruta para importar asistencia desde un archivo Excel."""
    resultados = {
        'procesados': 0,
        'nuevos': 0,
        'actualizados': 0,
        'errores': 0,
        'detalles': []
    }

    if request.method == 'POST':
        # Check if file was uploaded
        if 'archivo' not in request.files:
            flash('No se ha seleccionado un archivo', 'danger')
            return redirect(url_for('importar_asistencia'))
        
        archivo = request.files['archivo']
        if archivo.filename == '':
            flash('No se ha seleccionado un archivo', 'danger')
            return redirect(url_for('importar_asistencia'))
        
        if archivo and allowed_file(archivo.filename, ALLOWED_EXTENSIONS_EXCEL):
            # Initialize debug log
            with open('import_debug.log', 'a', encoding='utf-8') as f:
                f.write(f"\n========== NUEVA IMPORTACIÓN {datetime.now()} ==========\n")
            
            # Initialize error log
            with open('import_errors.log', 'a', encoding='utf-8') as f:
                f.write(f"\n========== NUEVA IMPORTACIÓN {datetime.now()} ==========\n")
            
            try:
                # Read Excel file with pandas
                df = pd.read_excel(archivo)
                
                # Verify required columns
                columnas_requeridas = ['Fecha', 'Hora', 'Intructor', 'Clase', 'Alumnos']
                for columna in columnas_requeridas:
                    if columna not in df.columns:
                        raise ValueError(f"El archivo no contiene la columna requerida: {columna}")
                
                # Log total rows to debug
                with open('import_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"Total de filas a procesar: {len(df)}\n")
                
                # Process each row
                for fila_num, row in df.iterrows():
                    try:
                        # Process date
                        fecha_str = row['Fecha']
                        if pd.isna(fecha_str):
                            raise ValueError("La fecha está vacía")
                        
                        # Log for debugging
                        with open('import_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"FECHA (Fila {fila_num}): '{fecha_str}', Tipo: {type(fecha_str)}\n")
                        
                        # Try to convert date
                        try:
                            if isinstance(fecha_str, str):
                                # Try different date formats
                                formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d.%m.%Y']
                                fecha = None
                                
                                for format_str in formats:
                                    try:
                                        fecha = datetime.strptime(fecha_str, format_str).date()
                                        # Log success
                                        with open('import_debug.log', 'a', encoding='utf-8') as f:
                                            f.write(f"  → Convertido con formato {format_str}: {fecha}\n")
                                        break
                                    except ValueError:
                                        continue
                                
                                if fecha is None:
                                    # Last attempt with pandas
                                    fecha = pd.to_datetime(fecha_str).date()
                                    with open('import_debug.log', 'a', encoding='utf-8') as f:
                                        f.write(f"  → Convertido con pandas: {fecha}\n")
                            elif isinstance(fecha_str, datetime):
                                fecha = fecha_str.date()
                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"  → Es un objeto datetime: {fecha}\n")
                            else:
                                # For Excel date numbers or other formats
                                fecha = pd.to_datetime(fecha_str).date()
                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"  → Convertido desde otro formato: {fecha}\n")
                        except Exception as e:
                            # Log error
                            with open('import_errors.log', 'a', encoding='utf-8') as f:
                                f.write(f"ERROR FECHA (Fila {fila_num}): '{fecha_str}' - {str(e)}\n")
                            
                            raise ValueError(f"No se pudo convertir la fecha '{fecha_str}': {str(e)}")
                        
                        # Process time
                        try:
                            hora_str = row['Hora']
                            
                            # Variable to track attendance
                            no_asistio = False
                            
                            # Log for debugging
                            with open('import_debug.log', 'a', encoding='utf-8') as f:
                                f.write(f"HORA (Fila {fila_num}): '{hora_str}', Tipo: {type(hora_str)}\n")
                            
                            # Check if it's "NO ASISTIO" or similar absence text
                            if isinstance(hora_str, str):
                                hora_upper = str(hora_str).upper().strip()
                                
                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"  → Verificando texto: '{hora_upper}'\n")
                                
                                if any(palabra in hora_upper for palabra in ['NO ASISTIO', 'NO ASISTIÓ', 'AUSENTE', 'CANCELADO']):
                                    hora = time(0, 0)  # Default time for schedule
                                    no_asistio = True
                                    
                                    with open('import_debug.log', 'a', encoding='utf-8') as f:
                                        f.write(f"  → DETECTED as absence\n")
                            elif pd.isna(hora_str):
                                # If the value is NaN or empty
                                hora = time(0, 0)  # Use midnight as default
                                
                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"  → NaN/empty value\n")
                            elif isinstance(hora_str, (int, float)):
                                # Convert Excel decimal to time
                                hora = excel_time_to_time(hora_str)
                                
                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                    f.write(f"  → Numeric value: {hora_str}, converted to: {hora}\n")
                                
                                if hora is None:
                                    raise ValueError(f"Could not convert value {hora_str} to time format")
                            else:
                                # Convert other formats
                                try:
                                    # Ensure it's a string and remove spaces
                                    hora_str = str(hora_str).strip()
                                    
                                    with open('import_debug.log', 'a', encoding='utf-8') as f:
                                        f.write(f"  → Processing time format: '{hora_str}'\n")
                                    
                                    # Check AM/PM format (example: 7:30AM, 7:30 PM)
                                    if 'AM' in hora_str.upper() or 'PM' in hora_str.upper():
                                        # Normalize format (remove spaces between time and AM/PM)
                                        hora_normalizada = hora_str.upper().replace(' ', '')
                                        
                                        with open('import_debug.log', 'a', encoding='utf-8') as f:
                                            f.write(f"  → AM/PM format detected: '{hora_normalizada}'\n")
                                        
                                        # Extract time parts (hour, minute, AM/PM)
                                        import re
                                        match = re.search(r'(\d+)(?::|\.)(\d+)\s*(AM|PM)', hora_str, re.IGNORECASE)
                                        
                                        if match:
                                            h, m, periodo = match.groups()
                                            h = int(h)
                                            m = int(m)
                                            
                                            # Adjust for PM
                                            if periodo.upper() == 'PM' and h < 12:
                                                h += 12
                                            elif periodo.upper() == 'AM' and h == 12:
                                                h = 0
                                            
                                            hora = time(h, m)
                                            
                                            with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                f.write(f"  → Manually converted: h={h}, m={m}, result={hora}\n")
                                        else:
                                            # Attempt 1: standard 12h format
                                            try:
                                                hora_dt = datetime.strptime(hora_normalizada, '%I:%M%p')
                                                hora = hora_dt.time()
                                                
                                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                    f.write(f"  → Converted with strptime format %I:%M%p: {hora}\n")
                                            except ValueError:
                                                # Attempt 2: format with dot
                                                try:
                                                    hora_norm_punto = hora_normalizada.replace(':', '.')
                                                    hora_dt = datetime.strptime(hora_norm_punto, '%I.%M%p')
                                                    hora = hora_dt.time()
                                                    
                                                    with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                        f.write(f"  → Converted with strptime format %I.%M%p: {hora}\n")
                                                except ValueError:
                                                    # Last attempt with pandas
                                                    try:
                                                        hora = pd.to_datetime(hora_str).time()
                                                        
                                                        with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                            f.write(f"  → Converted with pandas: {hora}\n")
                                                    except:
                                                        with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                            f.write(f"  → All attempts failed\n")
                                                        
                                                        raise ValueError(f"Unrecognized AM/PM format: {hora_str}")
                                    elif ':' in hora_str:
                                        # If it has HH:MM format or similar
                                        partes = hora_str.split(':')
                                        try:
                                            hora = time(int(partes[0]), int(partes[1]) if len(partes) > 1 else 0)
                                            
                                            with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                f.write(f"  → Converted with split: {hora}\n")
                                        except ValueError as e:
                                            raise ValueError(f"Invalid time format: {hora_str}")
                                    else:
                                        # Try with 24-hour format
                                        try:
                                            hora_dt = datetime.strptime(hora_str, '%H:%M')
                                            hora = hora_dt.time()
                                            
                                            with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                f.write(f"  → Converted with format %H:%M: {hora}\n")
                                        except ValueError:
                                            # Last attempt with pandas
                                            try:
                                                hora = pd.to_datetime(hora_str).time()
                                                
                                                with open('import_debug.log', 'a', encoding='utf-8') as f:
                                                    f.write(f"  → Converted with pandas: {hora}\n")
                                            except Exception as e_pandas:
                                                raise ValueError(f"Unrecognized time format: {hora_str}")
                                except Exception as e:
                                    # Log error
                                    with open('import_errors.log', 'a', encoding='utf-8') as f:
                                        f.write(f"ERROR TIME (Fila {fila_num}): '{hora_str}' - {str(e)}\n")
                                    
                                    raise ValueError(f"Could not convert time '{hora_str}': {str(e)}")
                        except Exception as e:
                            # Log the detailed error
                            error_info = {
                                'fila': fila_num,
                                'profesor': str(row.get('Intructor', '')),
                                'fecha': str(row.get('Fecha', '')),
                                'hora': str(row.get('Hora', '')),
                                'clase': str(row.get('Clase', '')),
                                'estado': 'Error',
                                'mensaje_error': str(e)
                            }
                            
                            with open('import_errors.log', 'a', encoding='utf-8') as f:
                                f.write(f"ERROR EN FILA {fila_num}:\n")
                                for k, v in error_info.items():
                                    f.write(f"  {k}: {v}\n")
                                f.write("\n" + "-"*50 + "\n")
                            
                            # For user interface
                            resultados['errores'] += 1
                            resultados['detalles'].append({
                                'fila': fila_num,
                                'profesor': str(row.get('Intructor', '')),
                                'fecha': str(row.get('Fecha', '')),
                                'clase': str(row.get('Clase', '')),
                                'estado': 'Error',
                                'errores': [f"({type(e).__name__}) {str(e)}"]
                            })
                            continue  # Skip to the next row
                        
                        # Find or create professor
                        profesor_nombre = row['Intructor']
                        if pd.isna(profesor_nombre) or not profesor_nombre:
                            raise ValueError("El nombre del instructor está vacío")
                        
                        profesor = Profesor.query.filter(Profesor.nombre.ilike(f"%{profesor_nombre}%")).first()
                        if not profesor:
                            try:
                                # Create new professor with a default rate
                                profesor = Profesor(
                                    nombre=profesor_nombre,
                                    apellido='',  # Leave empty for now
                                    email='',     # Leave empty for now
                                    telefono='',  # Leave empty for now
                                    tarifa_por_clase=0.0  # Default rate
                                )
                                db.session.add(profesor)
                                db.session.commit()
                            except Exception as e:
                                db.session.rollback()
                                raise ValueError(f"Error al crear profesor '{profesor_nombre}': {str(e)}")
                        
                        # Find or create class
                        clase_nombre = row['Clase']
                        if pd.isna(clase_nombre) or not clase_nombre:
                            raise ValueError("El nombre de la clase está vacío")
                        
                        # No need to search for a Clase model (it doesn't exist)
                        # We'll use the nombre directamente para HorarioClase
                        
                        # Get number of students
                        try:
                            alumnos = int(row['Alumnos'])
                        except:
                            alumnos = 0
                        
                        # Get comments if available
                        observaciones = row.get('Observaciones', '')
                        if pd.isna(observaciones):
                            observaciones = ''
                        
                        # Calculate arrival time (arrival = scheduled time + delay)
                        hora_llegada = hora
                        
                        # Check if this schedule exists
                        horario = HorarioClase.query.filter_by(
                            dia_semana=fecha.weekday(),
                            hora_inicio=hora,
                            nombre=clase_nombre
                        ).first()
                        
                        if not horario:
                            # Create new schedule
                            horario = HorarioClase(
                                nombre=clase_nombre,
                                dia_semana=fecha.weekday(),
                                hora_inicio=hora,
                                duracion=60,  # Duración en minutos
                                profesor_id=profesor.id,
                                tipo_clase='OTRO'  # Default type
                            )
                            db.session.add(horario)
                            db.session.commit()
                        
                        # Check if this class session already exists
                        clase_existente = ClaseRealizada.query.filter_by(
                            fecha=fecha,
                            horario_id=horario.id
                        ).first()
                        
                        if not clase_existente:
                            # Create new record
                            nueva_clase = ClaseRealizada(
                                fecha=fecha,
                                horario_id=horario.id,
                                profesor_id=profesor.id,
                                hora_llegada_profesor=None if no_asistio else hora,
                                cantidad_alumnos=alumnos,
                                observaciones="PROFESOR NO ASISTIÓ" if no_asistio else ""
                            )
                            db.session.add(nueva_clase)
                            
                            resultados['nuevos'] += 1
                            resultados['detalles'].append({
                                'fila': fila_num,
                                'profesor': profesor.nombre,
                                'fecha': fecha.strftime('%d/%m/%Y'),
                                'clase': horario.nombre,
                                'estado': 'Nuevo',
                                'nota': 'AUSENTE' if no_asistio else ''
                            })
                        else:
                            # Update existing record
                            clase_existente.profesor_id = profesor.id
                            clase_existente.hora_llegada_profesor = None if no_asistio else hora
                            clase_existente.cantidad_alumnos = alumnos
                            if no_asistio:
                                clase_existente.observaciones = "PROFESOR NO ASISTIÓ"
                            
                            resultados['actualizados'] += 1
                            resultados['detalles'].append({
                                'fila': fila_num,
                                'profesor': profesor.nombre,
                                'fecha': fecha.strftime('%d/%m/%Y'),
                                'clase': horario.nombre,
                                'estado': 'Actualizado',
                                'nota': 'AUSENTE' if no_asistio else ''
                            })
                        
                        # Commit the record
                        db.session.commit()
                        resultados['procesados'] += 1
                    
                    except Exception as e:
                        # Log detailed error information
                        error_info = {
                            'fila': fila_num,
                            'profesor': str(row.get('Intructor', '')),
                            'fecha': str(row.get('Fecha', '')),
                            'hora': str(row.get('Hora', '')),
                            'clase': str(row.get('Clase', '')),
                            'estado': 'Error',
                            'mensaje_error': str(e)
                        }
                        
                        # Registrar para depuración
                        with open('import_errors.log', 'a', encoding='utf-8') as f:
                            f.write(f"ERROR EN FILA {fila_num}:\n")
                            for k, v in error_info.items():
                                f.write(f"  {k}: {v}\n")
                            f.write("\n" + "-"*50 + "\n")
                        
                        # For user interface
                        resultados['errores'] += 1
                        resultados['detalles'].append({
                            'fila': fila_num,
                            'profesor': str(row.get('Intructor', '')),
                            'fecha': str(row.get('Fecha', '')),
                            'clase': str(row.get('Clase', '')),
                            'estado': 'Error',
                            'errores': [f"({type(e).__name__}) {str(e)}"]
                        })
                        
                # Log final result
                with open('import_debug.log', 'a', encoding='utf-8') as f:
                    f.write(f"Importación completada: {resultados['procesados']} procesados, {resultados['nuevos']} nuevos, "
                            f"{resultados['actualizados']} actualizados, {resultados['errores']} errores\n")
                
                # Show result to user
                if resultados['errores'] > 0:
                    flash(f"Importación completada con {resultados['errores']} errores. Se procesaron {resultados['procesados']} registros.", 'warning')
                else:
                    flash(f"Importación completada correctamente. Se procesaron {resultados['procesados']} registros.", 'success')
            
            except Exception as e:
                # Log global error
                with open('import_errors.log', 'a', encoding='utf-8') as f:
                    f.write(f"ERROR GLOBAL: {str(e)}\n")
                    f.write(f"{traceback.format_exc()}\n")
                
                flash(f"Error en la importación: {str(e)}", 'danger')
                resultados['errores'] += 1
        else:
            flash('Formato de archivo no permitido. Use archivos Excel (.xlsx, .xls)', 'danger')
    
    return render_template('importar/asistencia.html', titulo="Importar Asistencia", resultados=resultados)

@app.route('/import/asistencia', methods=['POST'])
def importar_asistencia_excel():
    """
    Procesa un archivo Excel con datos de asistencia y los importa al sistema.
    Los registros se asignarán al tipo de clase especificado por el usuario.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No se ha subido ningún archivo'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No se ha seleccionado ningún archivo'})
    
    # Verificar que se ha seleccionado un tipo de clase
    tipo_clase = request.form.get('tipo_clase')
    if not tipo_clase or tipo_clase not in ['MOVE', 'RIDE', 'BOX', 'OTRO']:
        return jsonify({'success': False, 'message': 'Debe seleccionar un tipo de clase válido (MOVE, RIDE, BOX, OTRO)'})
    
    # Resultados para devolver al cliente
    resultados = {
        'total': 0,
        'importados': 0,
        'errores': 0,
        'detalles': []
    }
    
    try:
        # Guardar temporalmente el archivo
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(app.instance_path, filename)
        os.makedirs(app.instance_path, exist_ok=True)
        file.save(temp_filepath)
        
        # Leer con pandas
        df = pd.read_excel(temp_filepath)
        
        # Eliminar el archivo temporal
        os.remove(temp_filepath)
        
        # Verificar columnas requeridas
        required_columns = ['Intructor', 'Fecha', 'Hora', 'Clase', 'Asistentes']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'success': False, 
                'message': f'El archivo no contiene columnas requeridas: {", ".join(missing_columns)}'
            })
        
        # Actualizar el total de registros
        resultados['total'] = len(df)
        
        # Registrar inicio de importación
        with open('import_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"\n=== INICIO IMPORTACIÓN {datetime.now()} ({resultados['total']} registros) ===\n")
            f.write(f"Tipo de clase seleccionado: {tipo_clase}\n")
        
        # Procesar cada fila
        for index, row in df.iterrows():
            fila_num = index + 2  # +2 porque Excel es 1-indexed y tenemos encabezado
            
            try:
                # Datos básicos
                instructor = str(row['Intructor']).strip()
                clase_nombre = str(row['Clase']).strip()
                alumnos = int(row['Asistentes']) if not pd.isna(row['Asistentes']) else 0
                
                # Procesar fecha
                fecha_str = row['Fecha']
                if isinstance(fecha_str, datetime):
                    fecha = fecha_str.date()
                elif isinstance(fecha_str, pd.Timestamp):
                    fecha = fecha_str.date()
                else:
                    # Intentar múltiples formatos de fecha
                    fecha = None
                    # Asegurar que sea string
                    fecha_str = str(fecha_str).strip()
                    # Probar formatos comunes de fecha
                    formatos_fecha = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%d.%m.%Y']
                    for formato in formatos_fecha:
                        try:
                            fecha = datetime.strptime(fecha_str, formato).date()
                            break
                        except ValueError:
                            continue
                    
                    # Si aún no se pudo convertir, intentar con pandas
                    if fecha is None:
                        try:
                            fecha = pd.to_datetime(fecha_str, errors='raise', dayfirst=True).date()
                        except Exception as fecha_error:
                            raise ValueError(f"No se pudo convertir la fecha '{fecha_str}': {str(fecha_error)}")
                
                # Procesar hora
                hora_str = row['Hora']
                
                # Variable para seguimiento de la asistencia
                no_asistio = False
                
                # Comprobar si es "NO ASISTIO" u otro texto que indica ausencia
                if isinstance(hora_str, str) and any(texto in hora_str.upper() for texto in ["NO ASISTIO", "NO ASISTIÓ", "AUSENTE", "CANCELADO"]):
                    # Marcar como no asistido (usamos hora normal para el horario)
                    hora = time(0, 0)  # Hora predeterminada para el horario
                    no_asistio = True
                elif pd.isna(hora_str):
                    # Si el valor es NaN o está vacío
                    hora = time(0, 0)  # Usar medianoche como valor predeterminado
                elif isinstance(hora_str, (int, float)):
                    # Convertir decimal de Excel a tiempo
                    hora = excel_time_to_time(hora_str)
                    if hora is None:
                        raise ValueError(f"No se pudo convertir el valor {hora_str} a formato de hora")
                else:
                    # Asegurar que sea string y eliminar espacios
                    hora_str = str(hora_str).strip()
                    
                    # Convertir otros formatos
                    try:
                        if ':' in hora_str:
                            # Si tiene formato HH:MM o similar
                            # Check for AM/PM format
                            is_pm = 'PM' in hora_str.upper()
                            is_am = 'AM' in hora_str.upper()
                            # Remove AM/PM from string
                            hora_str = hora_str.upper().replace('AM', '').replace('PM', '').strip()
                            
                            partes = hora_str.split(':')
                            horas = int(partes[0])
                            minutos = int(partes[1]) if len(partes) > 1 else 0
                            
                            # Adjust hours for PM
                            if is_pm and horas < 12:
                                horas += 12
                            # Adjust for 12 AM
                            elif is_am and horas == 12:
                                horas = 0
                                
                            hora = time(horas, minutos)
                        else:
                            # Intentar con datetime primero
                            try:
                                hora = datetime.strptime(hora_str, '%H:%M').time()
                            except ValueError:
                                # Último intento con pandas
                                hora = pd.to_datetime(hora_str).time()
                    except Exception as e:
                        raise ValueError(f"No se pudo convertir la hora '{hora_str}': {str(e)}")
                
                # Find or create professor
                profesor_nombre = instructor
                if pd.isna(profesor_nombre) or not profesor_nombre:
                    raise ValueError("El nombre del instructor está vacío")
                
                profesor = Profesor.query.filter(Profesor.nombre.ilike(f"%{profesor_nombre}%")).first()
                if not profesor:
                    try:
                        # Create new professor with a default rate
                        profesor = Profesor(
                            nombre=profesor_nombre,
                            apellido='',  # Leave empty for now
                            email='',     # Leave empty for now
                            telefono='',  # Leave empty for now
                            tarifa_por_clase=0.0  # Default rate
                        )
                        db.session.add(profesor)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        raise ValueError(f"Error al crear profesor '{profesor_nombre}': {str(e)}")
                
                # Find or create class schedule
                # Usamos el tipo_clase que seleccionó el usuario en el formulario
                # Buscar un horario existente o crear uno nuevo
                dia_semana = fecha.weekday()
                horario = HorarioClase.query.filter_by(
                    dia_semana=dia_semana,
                    hora_inicio=hora,
                    tipo_clase=tipo_clase
                ).first()
                
                if not horario:
                    # Create new schedule with the class type from the form
                    horario = HorarioClase(
                        nombre=clase_nombre,
                        dia_semana=dia_semana,
                        hora_inicio=hora,
                        duracion=60,  # Default duration
                        profesor_id=profesor.id,
                        tipo_clase=tipo_clase  # Use the selected class type
                    )
                    db.session.add(horario)
                    db.session.commit()
                
                # Check if this class session already exists
                clase_existente = ClaseRealizada.query.filter_by(
                    fecha=fecha,
                    horario_id=horario.id
                ).first()
                
                if not clase_existente:
                    # Create new record
                    nueva_clase = ClaseRealizada(
                        fecha=fecha,
                        horario_id=horario.id,
                        profesor_id=profesor.id,
                        hora_llegada_profesor=None if no_asistio else hora,
                        cantidad_alumnos=alumnos,
                        observaciones="PROFESOR NO ASISTIÓ" if no_asistio else ""
                    )
                    db.session.add(nueva_clase)
                    
                    resultados['importados'] += 1
                    resultados['detalles'].append({
                        'fila': fila_num,
                        'profesor': profesor.nombre,
                        'fecha': fecha.strftime('%d/%m/%Y'),
                        'clase': horario.nombre,
                        'estado': 'Importado',
                        'tipo': tipo_clase
                    })
                else:
                    # Update existing record
                    clase_existente.profesor_id = profesor.id
                    clase_existente.hora_llegada_profesor = None if no_asistio else hora
                    clase_existente.cantidad_alumnos = alumnos
                    if no_asistio:
                        clase_existente.observaciones = "PROFESOR NO ASISTIÓ"
                    
                    resultados['importados'] += 1
                    resultados['detalles'].append({
                        'fila': fila_num,
                        'profesor': profesor.nombre,
                        'fecha': fecha.strftime('%d/%m/%Y'),
                        'clase': horario.nombre,
                        'estado': 'Actualizado',
                        'tipo': tipo_clase
                    })
                
                # Commit the record
                db.session.commit()
                
            except Exception as e:
                # Registrar error con información detallada
                error_info = {
                    'fila': fila_num,
                    'profesor': str(row.get('Intructor', '')),
                    'fecha': str(row.get('Fecha', '')),
                    'hora': str(row.get('Hora', '')),
                    'clase': str(row.get('Clase', '')),
                    'estado': 'Error',
                    'mensaje_error': str(e)
                }
                
                # Registrar para depuración
                with open('import_errors.log', 'a', encoding='utf-8') as debug_file:
                    debug_file.write(f"ERROR EN FILA {fila_num}:\n")
                    for k, v in error_info.items():
                        debug_file.write(f"  {k}: {v}\n")
                    debug_file.write("\n" + "-"*50 + "\n")
                
                # Para interfaz de usuario
                resultados['errores'] += 1
                resultados['detalles'].append({
                    'fila': fila_num,
                    'profesor': str(row.get('Intructor', '')),
                    'fecha': str(row.get('Fecha', '')),
                    'clase': str(row.get('Clase', '')),
                    'estado': 'Error',
                    'errores': [f"({type(e).__name__}) {str(e)}"]
                })
        
        # Log final result
        with open('import_debug.log', 'a', encoding='utf-8') as f:
            f.write(f"Importación completada: {resultados['total']} registros, {resultados['importados']} importados, "
                    f"{resultados['errores']} errores\n")
        
        return jsonify({
            'success': True,
            'message': f"Se importaron {resultados['importados']} registros de {resultados['total']} (Errores: {resultados['errores']})",
            'results': resultados
        })
    
    except Exception as e:
        # Log global error
        with open('import_errors.log', 'a', encoding='utf-8') as f:
            f.write(f"ERROR GLOBAL: {str(e)}\n")
            f.write(f"{traceback.format_exc()}\n")
        
        return jsonify({
            'success': False,
            'message': f"Error en la importación: {str(e)}",
            'results': resultados
        })

@app.route('/importar', methods=['GET'])
def importar_excel():
    return render_template('importar/excel.html')

# Inicializar la base de datos si no existe
@app.cli.command('init-db')
def init_db_command():
    """Inicializar la base de datos."""
    try:
        # Mostrar la configuración de la base de datos
        click.echo(f'URI de la base de datos: {app.config["SQLALCHEMY_DATABASE_URI"]}')
        click.echo(f'Directorio actual: {os.getcwd()}')
        
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si el archivo se creó
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            click.echo(f'Base de datos creada correctamente en: {os.path.abspath(db_path)}')
        else:
            click.echo(f'No se encontró el archivo de base de datos en: {os.path.abspath(db_path)}')
    except Exception as e:
        click.echo(f'Error al inicializar la base de datos: {str(e)}')

@app.route('/asistencia/upload_audio/<int:horario_id>', methods=['POST'], endpoint='upload_audio_legacy2')
def upload_audio_legacy(horario_id):
    """Ruta legacy que redirige a la nueva ruta"""
    return redirect(url_for('audio_upload', horario_id=horario_id))

@app.route('/asistencia/get_audio/<int:horario_id>')
def get_audio_legacy(horario_id):
    """Ruta legacy que redirige a la nueva ruta"""
    return redirect(url_for('audio_get', horario_id=horario_id))

@app.route('/check_audio/<int:horario_id>')
def check_audio_legacy(horario_id):
    """Ruta legacy que redirige a la nueva ruta"""
    return redirect(url_for('audio_check', horario_id=horario_id))

@app.route('/test-old-upload')
def test_old_upload():
    """Ruta antigua con redirección automática via JavaScript"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0;url=/test-upload">
        <script>
            // Redirección para APIs que usan la URL antigua
            if (window.fetch) {
                const originalFetch = window.fetch;
                window.fetch = function(url, options) {
                    if (url === '/asistencia/upload_audio/5') {
                        console.log('Redirigiendo fetch a nueva URL');
                        return originalFetch('/asistencia/audio/upload/5', options);
                    }
                    return originalFetch(url, options);
                };
            }
        </script>
    </head>
    <body>
        <p>Redirigiendo a la nueva página...</p>
    </body>
    </html>
    """

# Fix the audio route implementations - they are currently empty
@app.route('/asistencia/audio/upload/<int:horario_id>', methods=['POST'])
def audio_upload(horario_id):
    """Implement the main audio upload functionality"""
    try:
        app.logger.info(f"Audio upload request received for horario_id: {horario_id}")
        
        if 'audio' not in request.files:
            app.logger.warning(f"No audio file found in request for horario_id: {horario_id}")
            return jsonify({
                'success': False,
                'message': 'No audio file found in request',
                'error_code': 'NO_AUDIO_FILE'
            }), 400
        
        audio_file = request.files['audio']
        app.logger.info(f"Received file: {audio_file.filename} for horario_id: {horario_id}")
        
        if audio_file.filename == '':
            app.logger.warning(f"Empty filename received for horario_id: {horario_id}")
            return jsonify({
                'success': False,
                'message': 'No selected file or empty filename',
                'error_code': 'EMPTY_FILENAME'
            }), 400
        
        # Check file format
        allowed_extensions = {'mp3', 'wav', 'ogg', 'm4a'}
        file_ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else ''
        
        if file_ext not in allowed_extensions:
            app.logger.warning(f"Invalid file format: {file_ext} for horario_id: {horario_id}")
            return jsonify({
                'success': False,
                'message': f"Formato de archivo no soportado. Por favor usa: {', '.join(allowed_extensions)}",
                'error_code': 'INVALID_FORMAT',
                'file_ext': file_ext,
                'allowed_extensions': list(allowed_extensions)
            }), 400
        
        if audio_file:
            # Asegurar que existen los directorios de almacenamiento
            ensure_upload_dirs()
            
            filename = secure_filename(audio_file.filename)
            timestamp = int(time_module.time())
            new_filename = f"audio_{timestamp}_{filename}"
            
            # Usar el nuevo sistema de almacenamiento organizado por horario_id
            storage_dir = get_audio_storage_path(horario_id)
            save_path = os.path.join(storage_dir, new_filename)
            
            try:
                # Eliminar archivos de audio anteriores para este horario
                try:
                    for old_file in os.listdir(storage_dir):
                        if old_file.startswith("audio_") and old_file != new_filename:
                            os.remove(os.path.join(storage_dir, old_file))
                            app.logger.info(f"Removed old audio file: {old_file} for horario_id: {horario_id}")
                except Exception as e:
                    app.logger.warning(f"Error cleaning old audio files: {str(e)}")
                
                # Guardar el nuevo archivo
                audio_file.save(save_path)
                app.logger.info(f"File saved successfully to {save_path} for horario_id: {horario_id}")
                
                file_size = os.path.getsize(save_path)
                file_size_readable = f"{file_size/1024:.2f} KB"
                
                # Ruta relativa del archivo para guardar en la base de datos
                relative_path = os.path.join(f'horario_{horario_id}', new_filename)
                
                # Update database if possible
                db_updated = False
                db_error = None
                try:
                    clase = ClaseRealizada.query.filter_by(horario_id=horario_id).order_by(ClaseRealizada.id.desc()).first()
                    if clase:
                        clase.audio_file = relative_path
                        db.session.commit()
                        db_updated = True
                        app.logger.info(f"Database updated for horario_id: {horario_id}, clase_id: {clase.id}")
                    else:
                        app.logger.warning(f"No ClaseRealizada found for horario_id: {horario_id}")
                except Exception as db_err:
                    db_error = str(db_err)
                    app.logger.error(f"Error updating database for horario_id: {horario_id}: {db_error}")
                
                return jsonify({
                    'success': True,
                    'message': 'Archivo subido exitosamente',
                    'file_path': f"/static/uploads/audios/permanent/{relative_path}",
                    'file_name': new_filename,
                    'file_size': file_size,
                    'file_size_readable': file_size_readable,
                    'db_updated': db_updated,
                    'db_error': db_error
                })
            except Exception as e:
                error_msg = str(e)
                app.logger.error(f"Error saving file for horario_id: {horario_id}: {error_msg}")
                return jsonify({
                    'success': False,
                    'message': f"Error al guardar el archivo: {error_msg}",
                    'error_code': 'SAVE_ERROR',
                    'error_details': error_msg
                }), 500
        
        app.logger.warning(f"Invalid file for horario_id: {horario_id}")
        return jsonify({
            'success': False,
            'message': 'Archivo invu00e1lido',
            'error_code': 'INVALID_FILE'
        }), 400
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Unexpected error in audio_upload for horario_id: {horario_id}: {error_msg}")
        return jsonify({
            'success': False,
            'message': f"Error inesperado: {error_msg}",
            'error_code': 'UNEXPECTED_ERROR',
            'error_details': error_msg
        }), 500

@app.route('/asistencia/audio/get/<int:horario_id>')
def audio_get(horario_id):
    """Implement the function to get audio files"""
    try:
        app.logger.info(f"Audio get request received for horario_id: {horario_id}")
        
        clase = ClaseRealizada.query.filter_by(horario_id=horario_id).order_by(ClaseRealizada.id.desc()).first()
        
        # Primero intentar buscar en la nueva estructura de directorios
        audio_dir = get_audio_storage_path(horario_id)
        newest_audio = None
        
        if os.path.exists(audio_dir):
            try:
                files = os.listdir(audio_dir)
                audio_files = [f for f in files if f.startswith('audio_')]
                if audio_files:
                    audio_files.sort(reverse=True)
                    newest_audio = audio_files[0]
                    audio_path = os.path.join(audio_dir, newest_audio)
                    
                    # Actualizar la base de datos si encontramos un audio
                    if clase and (not clase.audio_file or not os.path.exists(os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'audios', clase.audio_file))):
                        relative_path = os.path.join(f'horario_{horario_id}', newest_audio)
                        clase.audio_file = relative_path
                        db.session.commit()
                        app.logger.info(f"Updated database with found audio: {relative_path}")
                    
                    # En lugar de enviar el archivo directamente, redirigir a la ruta estática
                    static_url = url_for('static', filename=f'uploads/audios/permanent/horario_{horario_id}/{newest_audio}')
                    app.logger.info(f"Redirecting to static audio URL: {static_url}")
                    return redirect(static_url)
            except Exception as e:
                app.logger.error(f"Error searching for audio files in directory: {str(e)}")
        
        if not clase:
            app.logger.warning(f"No clase found for horario_id: {horario_id}")
            return jsonify({
                'success': False,
                'message': 'No clase registrada found for this schedule',
                'error_code': 'NO_CLASE_FOUND'
            }), 404
            
        if not clase.audio_file:
            app.logger.warning(f"No audio file registered for horario_id: {horario_id}, clase_id: {clase.id}")
            return jsonify({
                'success': False,
                'message': 'No audio file registered for this class',
                'error_code': 'NO_AUDIO_REGISTERED',
                'clase_id': clase.id
            }), 404
        
        # Determinar la ruta relativa para la URL estática
        if clase.audio_file.startswith('horario_') or '/' in clase.audio_file or '\\' in clase.audio_file:
            # Nueva estructura
            static_url = url_for('static', filename=f'uploads/audios/permanent/{clase.audio_file}')
        else:
            # Formato antiguo
            static_url = url_for('static', filename=f'uploads/audios/{clase.audio_file}')
        
        app.logger.info(f"Redirecting to static audio URL: {static_url}")
        return redirect(static_url)
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Error getting audio for horario_id: {horario_id}: {error_msg}")
        return jsonify({
            'success': False,
            'has_audio': False,
            'message': f"Error retrieving audio file: {error_msg}",
            'error_details': error_msg
        }), 500

@app.route('/asistencia/audio/check/<int:horario_id>')
def audio_check(horario_id):
    """Implement the function to check if audio exists"""
    try:
        app.logger.info(f"Audio check request for horario_id: {horario_id}")
        
        clase = ClaseRealizada.query.filter_by(horario_id=horario_id).order_by(ClaseRealizada.id.desc()).first()
        
        # Primero, intentemos buscar en la nueva estructura, incluso si no hay registro en la BD
        audio_dir = get_audio_storage_path(horario_id)
        audio_files = []
        newest_audio = None
        newest_audio_path = None
        
        if os.path.exists(audio_dir):
            try:
                files = os.listdir(audio_dir)
                audio_files = [f for f in files if f.startswith('audio_')]
                if audio_files:
                    audio_files.sort(reverse=True)
                    newest_audio = audio_files[0]
                    newest_audio_path = os.path.join(audio_dir, newest_audio)
                    app.logger.info(f"Found audio file in storage: {newest_audio_path}")
                    
                    # Actualizar la base de datos con la nueva ruta
                    relative_path = os.path.join(f'horario_{horario_id}', newest_audio)
                    clase.audio_file = relative_path
                    db.session.commit()
                    app.logger.info(f"Updated database with found audio: {relative_path}")
                else:
                    app.logger.warning(f"No audio files found in directory: {audio_dir}")
            except Exception as e:
                app.logger.error(f"Error searching for audio files: {str(e)}")
        
        # Si encontramos un archivo pero no hay registro en la BD o el registro es incorrecto
        if newest_audio_path and (not clase or not clase.audio_file or not os.path.exists(os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'audios', 'permanent', clase.audio_file))):
            if clase:
                # Actualizar la BD con la nueva ruta
                relative_path = os.path.join(f'horario_{horario_id}', newest_audio)
                clase.audio_file = relative_path
                db.session.commit()
                app.logger.info(f"Updated database with found audio: {relative_path}")
            elif newest_audio_path:
                app.logger.warning(f"Found audio file but no clase record for horario_id: {horario_id}")
                return jsonify({
                    'success': True,
                    'has_audio': True,
                    'exists': True,
                    'file_name': newest_audio,
                    'file_path': f"/static/uploads/audios/permanent/horario_{horario_id}/{newest_audio}",
                    'file_size': os.path.getsize(newest_audio_path),
                    'file_size_readable': f"{os.path.getsize(newest_audio_path)/1024:.2f} KB",
                    'clase_id': None,
                    'fecha': None
                })
        
        # Si no hay registro en la base de datos y no encontramos archivo
        if not clase and not newest_audio_path:
            app.logger.info(f"No audio registered for horario_id: {horario_id}")
            return jsonify({
                'success': True,
                'has_audio': False,
                'message': 'No audio registered'
            })
            
        # Si hay registro pero no tiene audio
        if clase and not clase.audio_file and not newest_audio_path:
            app.logger.info(f"No audio registered in database for horario_id: {horario_id}")
            return jsonify({
                'success': True,
                'has_audio': False,
                'message': 'No audio registered in database'
            })
        
        # Verificar la ruta del audio en la base de datos
        upload_folder = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'audios')
        audio_path = None
        
        # Determinar la ruta del audio según el formato almacenado
        if clase and clase.audio_file:
            if clase.audio_file.startswith('horario_') or '/' in clase.audio_file or '\\' in clase.audio_file:
                audio_path = os.path.join(upload_folder, 'permanent', clase.audio_file)
            else:
                # Compatibilidad con formato antiguo
                audio_path = os.path.join(upload_folder, clase.audio_file)
        elif newest_audio_path:
            audio_path = newest_audio_path
        
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            app.logger.info(f"Audio file exists for horario_id: {horario_id}, size: {file_size/1024:.2f} KB")
            
            # Extraer el nombre del archivo de la ruta
            file_name = os.path.basename(audio_path)
            
            # Determinar la ruta relativa para el frontend
            if audio_path == newest_audio_path:
                file_path = f"/static/uploads/audios/permanent/horario_{horario_id}/{file_name}"
            elif clase and clase.audio_file and clase.audio_file.startswith('horario_'):
                file_path = f"/static/uploads/audios/permanent/{clase.audio_file}"
            else:
                file_path = f"/static/uploads/audios/{file_name}"
            
            return jsonify({
                'success': True,
                'has_audio': True,
                'exists': True,
                'file_name': file_name,
                'file_path': file_path,
                'file_size': file_size,
                'file_size_readable': f"{file_size/1024:.2f} KB",
                'clase_id': clase.id if clase else None,
                'fecha': clase.fecha.strftime('%Y-%m-%d') if clase and clase.fecha else None
            })
        else:
            app.logger.warning(f"Audio file registered but not found on disk for horario_id: {horario_id}")
            
            # Si tenemos un registro en la BD pero el archivo no existe
            if clase and clase.audio_file:
                file_name = os.path.basename(clase.audio_file) if '/' in clase.audio_file or '\\' in clase.audio_file else clase.audio_file
                return jsonify({
                    'success': True,
                    'has_audio': False,
                    'exists': False,
                    'message': 'The file is registered in the database but does not exist on disk',
                    'file_name': file_name,
                    'clase_id': clase.id
                })
            else:
                return jsonify({
                    'success': True,
                    'has_audio': False,
                    'exists': False,
                    'message': 'No audio file found on disk'
                })
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Error checking audio for horario_id: {horario_id}: {error_msg}")
        return jsonify({
            'success': False,
            'has_audio': False,
            'message': f"Error checking audio: {error_msg}",
            'error_details': error_msg
        }), 500

@app.route('/asistencia/audio/diagnostico')
def audio_diagnostics():
    """Diagnostics endpoint for audio files"""
    try:
        app.logger.info("Audio diagnostics requested")
        
        # Basic info
        upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        audio_folder = os.path.join(upload_folder, 'audios')
        
        # Ensure audio folder exists
        os.makedirs(audio_folder, exist_ok=True)
        
        # Gather disk stats
        disk_stats = {}
        try:
            total, used, free = shutil.disk_usage(audio_folder)
            disk_stats = {
                'total_gb': f"{total / (1024**3):.2f} GB",
                'used_gb': f"{used / (1024**3):.2f} GB",
                'free_gb': f"{free / (1024**3):.2f} GB",
                'usage_percent': f"{used / total * 100:.1f}%"
            }
        except Exception as e:
            disk_stats['error'] = str(e)
        
        # Count audio files in the folder
        audio_files = []
        try:
            if os.path.exists(audio_folder):
                for filename in os.listdir(audio_folder):
                    if filename.startswith('audio_'):
                        file_path = os.path.join(audio_folder, filename)
                        file_size = os.path.getsize(file_path)
                        file_time = os.path.getmtime(file_path)
                        
                        audio_files.append({
                            'filename': filename,
                            'size_kb': f"{file_size/1024:.2f} KB",
                            'last_modified': datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                        })
        except Exception as e:
            app.logger.error(f"Error listing audio files: {str(e)}")
        
        # Get recent classes with audio
        recent_classes = []
        try:
            # Filter to last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            classes_with_audio = ClaseRealizada.query.filter(
                ClaseRealizada.audio_file.isnot(None),
                ClaseRealizada.fecha >= thirty_days_ago
            ).order_by(ClaseRealizada.fecha.desc()).limit(10).all()
            
            for clase in classes_with_audio:
                audio_path = os.path.join(audio_folder, clase.audio_file) if clase.audio_file else None
                file_exists = audio_path and os.path.exists(audio_path)
                
                recent_classes.append({
                    'id': clase.id,
                    'horario_id': clase.horario_id,
                    'fecha': clase.fecha.strftime('%Y-%m-%d') if clase.fecha else None,
                    'asignatura': clase.horario.nombre if clase.horario else "Desconocida",
                    'audio_file': clase.audio_file,
                    'file_exists': file_exists
                })
        except Exception as e:
            app.logger.error(f"Error getting recent classes: {str(e)}")
        
        # Summary counts
        summary = {
            'total_audio_files': len(audio_files),
            'recent_classes_with_audio': len(recent_classes),
            'audio_folder': audio_folder,
            'folder_exists': os.path.exists(audio_folder)
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'disk_stats': disk_stats,
            'recent_audio_files': sorted(audio_files, key=lambda x: x['last_modified'], reverse=True)[:10],
            'recent_classes': recent_classes
        })
    except Exception as e:
        app.logger.error(f"Error in audio diagnostics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error en diagnóstico de audio: {str(e)}"
        }), 500

# Agregar ruta para configuración de notificaciones
@app.route('/configuracion/notificaciones', methods=['GET', 'POST'])
def configuracion_notificaciones():
    """Configuración de notificaciones y alertas"""
    from notifications import check_and_notify_unregistered_classes, send_whatsapp_notification, is_notification_locked
    from notifications import update_notification_schedule, DEFAULT_NOTIFICATION_HOUR_1, DEFAULT_NOTIFICATION_HOUR_2

    if request.method == 'POST':
        # Guardar la configuración del número de teléfono
        telefono = request.form.get('telefono_notificaciones', '').strip()
        hora_notificacion_1 = request.form.get('hora_notificacion_1', DEFAULT_NOTIFICATION_HOUR_1).strip()
        hora_notificacion_2 = request.form.get('hora_notificacion_2', DEFAULT_NOTIFICATION_HOUR_2).strip()
        
        # Validar que el número tenga el formato correcto
        if not telefono:
            flash('Ingrese un número de teléfono válido', 'danger')
        elif not telefono.startswith('+'):
            flash('El número debe incluir el código del país con el prefijo "+" (por ejemplo, +34612345678)', 'warning')
            telefono = '+' + telefono  # Intentar arreglarlo añadiendo el +
        
        # Validar el formato de las horas (HH:MM)
        import re
        hora_formato_valido = re.compile(r'^([01]?[0-9]|2[0-3]):([0-5][0-9])$')
        
        if not hora_formato_valido.match(hora_notificacion_1):
            flash('El formato de la primera hora de notificación debe ser HH:MM (por ejemplo, 13:30)', 'warning')
            hora_notificacion_1 = DEFAULT_NOTIFICATION_HOUR_1
            
        if not hora_formato_valido.match(hora_notificacion_2):
            flash('El formato de la segunda hora de notificación debe ser HH:MM (por ejemplo, 20:30)', 'warning')
            hora_notificacion_2 = DEFAULT_NOTIFICATION_HOUR_2
        
        if telefono:
            # Guardar en el archivo de configuración como variable de entorno permanente
            try:
                # Actualizar run.bat con el nuevo número y horas
                run_bat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run.bat')
                if os.path.exists(run_bat_path):
                    with open(run_bat_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    # Reemplazar la línea con el número de teléfono
                    content = content.replace(
                        'set NOTIFICATION_PHONE_NUMBER=+numero_a_notificar_aqui', 
                        f'set NOTIFICATION_PHONE_NUMBER={telefono}'
                    )
                    
                    # Si ya hay un número configurado, reemplazarlo también
                    import re
                    pattern = r'set NOTIFICATION_PHONE_NUMBER=\+[0-9]+'
                    content = re.sub(pattern, f'set NOTIFICATION_PHONE_NUMBER={telefono}', content)
                    
                    # Agregar o actualizar las horas de notificación
                    if 'set NOTIFICATION_HOUR_1=' in content:
                        content = re.sub(r'set NOTIFICATION_HOUR_1=[0-9:]+', f'set NOTIFICATION_HOUR_1={hora_notificacion_1}', content)
                    else:
                        content += f'\nset NOTIFICATION_HOUR_1={hora_notificacion_1}'
                        
                    if 'set NOTIFICATION_HOUR_2=' in content:
                        content = re.sub(r'set NOTIFICATION_HOUR_2=[0-9:]+', f'set NOTIFICATION_HOUR_2={hora_notificacion_2}', content)
                    else:
                        content += f'\nset NOTIFICATION_HOUR_2={hora_notificacion_2}'
                    
                    with open(run_bat_path, 'w', encoding='utf-8') as file:
                        file.write(content)
            except Exception as e:
                app.logger.error(f"Error al actualizar run.bat: {str(e)}")
            
            # Guardar en las variables actuales
            os.environ['NOTIFICATION_PHONE_NUMBER'] = telefono
            os.environ['NOTIFICATION_HOUR_1'] = hora_notificacion_1
            os.environ['NOTIFICATION_HOUR_2'] = hora_notificacion_2
            
            app.config['NOTIFICATION_PHONE_NUMBER'] = telefono
            app.config['NOTIFICATION_HOUR_1'] = hora_notificacion_1
            app.config['NOTIFICATION_HOUR_2'] = hora_notificacion_2
            
            # Actualizar el scheduler con las nuevas horas
            update_notification_schedule(app)
            
            flash(f'Configuración de notificaciones actualizada. Número configurado: {telefono}', 'success')
            flash(f'Horarios de notificación configurados: {hora_notificacion_1} y {hora_notificacion_2}', 'success')
            
            # Probar la notificación si se solicitó
            if 'enviar_prueba' in request.form:
                # Verificar si ya hay un envío en progreso
                if is_notification_locked():
                    flash('Hay un envío de notificación en progreso. Por favor, espere unos minutos antes de intentar nuevamente.', 'warning')
                else:
                    try:
                        # Enviar un mensaje de prueba directamente
                        mensaje_prueba = f" Mensaje de prueba desde AppClases\n\nEste es un mensaje de prueba para verificar la configuración del sistema de notificaciones. La hora actual es: {datetime.now().strftime('%H:%M:%S')}"
                        
                        # Ejecutar el envío en un proceso independiente para evitar bloqueos
                        sent = send_whatsapp_notification(mensaje_prueba, telefono)
                        if sent:
                            flash('Notificación de prueba enviada. Verifica tu WhatsApp.', 'success')
                        else:
                            flash('No se pudo enviar la notificación de prueba. Revisa los logs para más detalles.', 'warning')
                    except Exception as e:
                        flash(f'Error al enviar notificación de prueba: {str(e)}', 'danger')
                    
        return redirect(url_for('configuracion_notificaciones'))
        
    # Obtener la configuración actual
    current_phone = app.config.get('NOTIFICATION_PHONE_NUMBER', os.environ.get('NOTIFICATION_PHONE_NUMBER', ''))
    current_hour_1 = app.config.get('NOTIFICATION_HOUR_1', os.environ.get('NOTIFICATION_HOUR_1', DEFAULT_NOTIFICATION_HOUR_1))
    current_hour_2 = app.config.get('NOTIFICATION_HOUR_2', os.environ.get('NOTIFICATION_HOUR_2', DEFAULT_NOTIFICATION_HOUR_2))
    
    return render_template('configuracion/notificaciones.html', 
                          telefono_actual=current_phone,
                          hora_notificacion_1=current_hour_1,
                          hora_notificacion_2=current_hour_2)

# Agregar ruta para configuración de exportación de base de datos
@app.route('/configuracion/exportar', methods=['GET', 'POST'])
def configuracion_exportar():
    """Configuración de exportación de base de datos a Excel"""
    from export_to_excel import export_tables_to_excel
    
    # Valores predeterminados
    nivel_proteccion = 'completa'
    directorio = 'backups'
    excel_unificado = True
    excel_individuales = True
    mensaje_resultado = None
    archivos_exportados = []
    
    if request.method == 'POST':
        # Obtener parámetros del formulario
        nivel_proteccion = request.form.get('proteccion_datos', 'completa')
        directorio = request.form.get('directorio', 'backups').strip()
        excel_unificado = 'excel_unificado' in request.form
        excel_individuales = 'excel_individuales' in request.form
        
        # Validar que al menos una opción de exportación esté seleccionada
        if not excel_unificado and not excel_individuales:
            flash('Debe seleccionar al menos un formato de exportación', 'danger')
        else:
            try:
                # Realizar la exportación
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
                resultados = export_tables_to_excel(
                    db_path=db_path,
                    output_dir=directorio,
                    protection_level=nivel_proteccion,
                    create_unified=excel_unificado,
                    create_individual=excel_individuales
                )
                
                # Preparar mensaje de éxito
                total_tablas = len([k for k in resultados.keys() if k != 'completo'])
                total_registros = sum(info['row_count'] for tabla, info in resultados.items() if tabla != 'completo')
                
                mensaje_resultado = f"Exportación completada con éxito. Se exportaron {total_tablas} tablas con un total de {total_registros} registros."
                
                # Obtener lista de archivos exportados para mostrar
                for tabla, info in resultados.items():
                    archivos_exportados.append(info['file_path'])
                
                flash(mensaje_resultado, 'success')
            except Exception as e:
                flash(f'Error durante la exportación: {str(e)}', 'danger')
                app.logger.error(f"Error en exportación a Excel: {str(e)}")
    
    return render_template('configuracion/exportar_base_datos.html',
                          nivel_proteccion=nivel_proteccion,
                          directorio=directorio,
                          excel_unificado=excel_unificado,
                          excel_individuales=excel_individuales,
                          mensaje_resultado=mensaje_resultado,
                          archivos_exportados=archivos_exportados)

# Función para asegurar que los directorios de carga existan
def ensure_upload_dirs():
    """
    Asegura que los directorios necesarios para la carga de archivos existan.
    Crea los directorios si no existen.
    """
    app.logger.info("Verificando directorios de carga...")
    upload_base = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    os.makedirs(upload_base, exist_ok=True)
    
    audio_dir = os.path.join(upload_base, 'audios')
    os.makedirs(audio_dir, exist_ok=True)
    
    permanent_audio_dir = os.path.join(audio_dir, 'permanent')
    os.makedirs(permanent_audio_dir, exist_ok=True)
    
    # Comprobar permisos de escritura
    test_file_path = os.path.join(upload_base, '.write_test')
    try:
        with open(test_file_path, 'w') as f:
            f.write('test')
        os.remove(test_file_path)
        app.logger.info(f"Directories created and write permissions verified: {upload_base}")
        return True
    except Exception as e:
        app.logger.error(f"Error checking write permissions: {str(e)}")
        return False

# Función para gestionar archivos de audio
def get_audio_storage_path(horario_id, filename=None):
    """
    Genera la ruta para almacenar o recuperar un archivo de audio.
    Si filename es None, devuelve el directorio para el horario_id.
    """
    upload_base = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    permanent_audio_dir = os.path.join(upload_base, 'audios', 'permanent')
    
    # Crear directorio específico para este horario si no existe
    horario_dir = os.path.join(permanent_audio_dir, f'horario_{horario_id}')
    os.makedirs(horario_dir, exist_ok=True)
    
    if filename is None:
        return horario_dir
    else:
        return os.path.join(horario_dir, filename)

@app.route('/asistencia/fecha/<string:fecha>/<int:horario_id>', methods=['GET', 'POST'])
def registrar_asistencia_fecha(fecha, horario_id):
    """Registrar asistencia para una fecha específica y horario"""
    try:
        # Convertir la fecha del parámetro URL a un objeto date
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        hoy = datetime.now().date()
        
        # Depuración inicial para mostrar claramente la fecha de la clase vs la fecha actual
        print("="*50)
        print(f"REGISTRO DE ASISTENCIA: fecha_clase={fecha_obj.strftime('%d/%m/%Y')}, fecha_actual={hoy.strftime('%d/%m/%Y')}")
        print(f"¿Se está registrando una clase con fecha diferente a hoy? {'SÍ' if fecha_obj != hoy else 'NO'}")
        print(f"Diferencia de días: {(hoy - fecha_obj).days} días")
        print("="*50)
    except ValueError:
        flash('Formato de fecha inválido. Use YYYY-MM-DD', 'danger')
        return redirect(url_for('control_asistencia'))
    
    # Obtener información del horario
    horario = HorarioClase.query.get_or_404(horario_id)
    if not horario:
        flash(f'No se encontró el horario con ID {horario_id}', 'danger')
        return redirect(url_for('clases_no_registradas'))
        
    # Depuración del horario encontrado
    print(f"HORARIO: ID={horario.id}, Nombre={horario.nombre}, Hora inicio={horario.hora_inicio}")
    
    # Verificar si ya existe un registro para esta fecha y horario usando el ORM
    registro_existente = ClaseRealizada.query.filter_by(
        fecha=fecha_obj,
        horario_id=horario_id
    ).first()
    
    if registro_existente:
        print(f"AVISO: Ya existe un registro para esta clase el {fecha_obj.strftime('%d/%m/%Y')}, ID={registro_existente.id}")
        flash(f'Ya existe un registro para esta clase el {fecha_obj.strftime("%d/%m/%Y")}', 'warning')
        return redirect(url_for('editar_asistencia', id=registro_existente.id))
    
    # También comprobar si hay un registro para hoy (para evitar confusiones)
    if fecha_obj != hoy:
        registro_hoy = ClaseRealizada.query.filter_by(
            fecha=hoy,
            horario_id=horario_id
        ).first()
        
        if registro_hoy:
            print(f"AVISO: Existe un registro para la FECHA ACTUAL ({hoy.strftime('%d/%m/%Y')}), ID={registro_hoy.id}")
            flash(f'Atención: Ya existe un registro para esta clase en la fecha actual ({hoy.strftime("%d/%m/%Y")})', 'info')
    
    # Procesar el formulario si es POST
    if request.method == 'POST':
        # Obtener fecha manual si se proporciona
        fecha_manual = request.form.get('fecha_manual')
        if fecha_manual:
            try:
                nueva_fecha = datetime.strptime(fecha_manual, '%Y-%m-%d').date()
                print(f"MODIFICACIÓN FECHA: Usuario cambió la fecha de {fecha_obj.strftime('%d/%m/%Y')} a {nueva_fecha.strftime('%d/%m/%Y')}")
                
                # Verificar si ya existe un registro para la nueva fecha
                registro_nueva_fecha = ClaseRealizada.query.filter_by(
                    fecha=nueva_fecha,
                    horario_id=horario_id
                ).first()
                
                if registro_nueva_fecha:
                    print(f"AVISO: Ya existe registro para la fecha manual {nueva_fecha.strftime('%d/%m/%Y')}, ID={registro_nueva_fecha.id}")
                    flash(f'Ya existe un registro para esta clase en la fecha {nueva_fecha.strftime("%d/%m/%Y")}', 'warning')
                    return redirect(url_for('editar_asistencia', id=registro_nueva_fecha.id))
                
                # Usar la nueva fecha
                fecha_obj = nueva_fecha
            except ValueError:
                print(f"ERROR: Formato de fecha manual inválido: {fecha_manual}")
                flash('Formato de fecha manual inválido. Use YYYY-MM-DD', 'danger')
                profesores = Profesor.query.all()
                return render_template('asistencia/registrar.html', horario=horario, fecha=fecha_obj, hoy=hoy, profesores=profesores)
        
        # Obtener el estado de la clase (normal, suplencia, cancelada)
        estado_clase = request.form.get('estado_clase', 'normal')
        
        # Inicializar variables
        hora_llegada = None
        cantidad_alumnos = 0
        observaciones = ""
        profesor_id = horario.profesor_id  # Default to the scheduled teacher
        
        # Process form data according to class state
        if estado_clase == 'normal':
            # Normal class with the regular teacher
            hora_llegada = request.form.get('hora_llegada')
            cantidad_alumnos = request.form.get('cantidad_alumnos', 0)
            observaciones = request.form.get('observaciones', '')
            profesor_id = request.form.get('profesor_id') or profesor_id
            
        elif estado_clase == 'suplencia':
            # Class with a substitute teacher
            hora_llegada = request.form.get('hora_llegada_suplente')
            cantidad_alumnos = request.form.get('cantidad_alumnos_suplencia', 0)
            motivo_suplencia = request.form.get('motivo_suplencia', 'otro')
            profesor_id = request.form.get('profesor_suplente') or profesor_id
            observaciones = f"SUPLENCIA - Motivo: {motivo_suplencia} - " + request.form.get('observaciones', '')
            
        elif estado_clase == 'cancelada':
            # Cancelled class
            hora_llegada = None  # No arrival time for cancelled classes
            cantidad_alumnos = 0  # No students for cancelled classes
            motivo_ausencia = request.form.get('motivo_ausencia', 'otro')
            aviso_alumnos = request.form.get('aviso_alumnos', 'no')
            observaciones = f"CLASE CANCELADA - Motivo: {motivo_ausencia} - Aviso: {aviso_alumnos} - " + request.form.get('observaciones', '')
        
        # Convert cantidad_alumnos to integer
        try:
            cantidad_alumnos = int(cantidad_alumnos)
        except (ValueError, TypeError):
            cantidad_alumnos = 0
            
        # Convert profesor_id to integer if provided
        if profesor_id:
            try:
                profesor_id = int(profesor_id)
            except (ValueError, TypeError):
                profesor_id = horario.profesor_id
                print(f"ERROR: ID de profesor inválido, usando el profesor del horario por defecto")
            
        try:
            # Convertir la hora de llegada a un objeto time
            hora_llegada_time = None
            if hora_llegada and estado_clase != 'cancelada':
                try:
                    hora_llegada_time = datetime.strptime(hora_llegada, '%H:%M').time()
                except ValueError:
                    print(f"ERROR: Formato de hora inválido: {hora_llegada}")
                    hora_llegada_time = None
                
            # Crear instancia directamente con SQLAlchemy ORM
            nueva_clase = ClaseRealizada(
                fecha=fecha_obj,  # IMPORTANTE: Esta es la fecha de la clase, no la fecha actual
                horario_id=horario.id,
                profesor_id=profesor_id,
                hora_llegada_profesor=hora_llegada_time,
                cantidad_alumnos=cantidad_alumnos,
                observaciones=observaciones,
                fecha_registro=datetime.utcnow()  # Esta sí es la fecha actual (cuándo se registró)
            )
            
            # Depuración para verificar las horas y fechas
            print("="*50)
            print(f"GUARDANDO CLASE:")
            print(f"- Fecha de la clase: {fecha_obj.strftime('%d/%m/%Y')}")
            print(f"- Fecha actual de registro: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"- Horario ID: {horario.id}, Nombre: {horario.nombre}")
            print(f"- Profesor ID: {profesor_id}")
            print(f"- Hora llegada: {hora_llegada}")
            print(f"- Hora inicio programada: {horario.hora_inicio}")
            print(f"- Cantidad alumnos: {cantidad_alumnos}")
            print(f"- Observaciones: {observaciones}")
            print("="*50)
            
            # Agregar y guardar en la base de datos
            db.session.add(nueva_clase)
            db.session.commit()
            
            # Limpiar caché de métricas para este profesor
            try:
                from models import clear_metrics_cache
                clear_metrics_cache(profesor_id)
                print(f"INFO: Limpiada caché de métricas para profesor_id={profesor_id}")
            except Exception as e:
                print(f"ERROR: No se pudo limpiar caché de métricas - {str(e)}")
            
            db.session.refresh(nueva_clase)
            
            print(f"ÉXITO: Clase registrada con ID={nueva_clase.id}")
            
            # Verificar que la fecha guardada es la correcta
            clase_guardada = ClaseRealizada.query.get(nueva_clase.id)
            print(f"VERIFICACIÓN: Fecha guardada en BD={clase_guardada.fecha.strftime('%d/%m/%Y')}")
            
            # Mensaje especial si se usó una fecha manual
            if fecha_manual and fecha_manual != fecha:
                flash(f'Clase registrada con fecha manual: {fecha_obj.strftime("%d/%m/%Y")}', 'success')
            else:
                flash(f'Asistencia para la clase {horario.nombre} del {fecha_obj.strftime("%d/%m/%Y")} registrada con éxito', 'success')
            
            # Redirigir según si la fecha es hoy o no
            if fecha_obj == hoy:
                return redirect(url_for('control_asistencia'))
            else:
                # Forzar actualización de la caché
                timestamp = int(time_module.time())
                print(f"REDIRECCIÓN: A informe mensual para {fecha_obj.month}/{fecha_obj.year}")
                return redirect(url_for('informe_mensual', 
                                      mes=fecha_obj.month, 
                                      anio=fecha_obj.year, 
                                      refresh=timestamp, 
                                      clear_cache=1))
                
        except Exception as e:
            db.session.rollback()
            print(f"ERROR CRÍTICO: No se pudo registrar la clase - {str(e)}")
            trace = traceback.format_exc()
            print(trace)
            flash(f'Error al registrar la clase: {str(e)}', 'danger')
            return redirect(url_for('clases_no_registradas'))
    
    # Para solicitudes GET, mostrar el formulario
    profesores = Profesor.query.all()
    print(f"FORMULARIO: Mostrando formulario para fecha={fecha_obj.strftime('%d/%m/%Y')}, horario={horario.nombre}")
    return render_template('asistencia/registrar.html', horario=horario, fecha=fecha_obj, hoy=hoy, profesores=profesores)

@app.route('/asistencia/registrar-clases-masivo', methods=['POST'])
@app.route('/registrar-clases-no-registradas', methods=['POST'])  # Alias para mantener compatibilidad
def registrar_clases_no_registradas():
    """Registrar múltiples clases no registradas de forma masiva"""
    if request.method == 'POST':
        print("="*50)
        print("INICIO REGISTRO MASIVO DE CLASES NO REGISTRADAS")
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        print(f"Fecha/hora actual: {fecha_actual}")
        print("="*50)
        
        clases_ids = request.form.getlist('clases_ids[]')
        
        if not clases_ids:
            print("ERROR: No se seleccionaron clases para registrar")
            flash('No seleccionó ninguna clase para registrar', 'warning')
            return redirect(url_for('clases_no_registradas'))
        
        print(f"Se seleccionaron {len(clases_ids)} clases para registro masivo")
        
        # Verificar si se especificó un profesor alternativo para todas las clases
        profesor_id_alternativo = request.form.get('profesor_id_alternativo')
        if profesor_id_alternativo:
            try:
                profesor_id_alternativo = int(profesor_id_alternativo)
                # Verificar que el profesor existe
                profesor = Profesor.query.get(profesor_id_alternativo)
                if not profesor:
                    profesor_id_alternativo = None
                    print(f"ADVERTENCIA: Profesor alternativo con ID={profesor_id_alternativo} no existe")
                    flash('El profesor alternativo seleccionado no existe', 'warning')
                else:
                    print(f"Usando profesor alternativo: ID={profesor.id}, Nombre={profesor.nombre} {profesor.apellido}")
            except (ValueError, TypeError):
                profesor_id_alternativo = None
                print("ERROR: ID de profesor alternativo inválido")
                flash('ID de profesor alternativo inválido', 'warning')
        
        # Check if classes should be registered as cancelled
        registrar_como_canceladas = 'registrar_como_canceladas' in request.form
        motivo_cancelacion = request.form.get('motivo_cancelacion', 'otro')
        
        if registrar_como_canceladas:
            print(f"Las clases se registrarán como CANCELADAS. Motivo: {motivo_cancelacion}")
        
        clases_registradas = 0
        clases_procesadas = []
        
        print("-"*40)
        print("PROCESANDO CLASES:")
        
        for clase_id in clases_ids:
            try:
                # El formato es 'YYYY-MM-DD|horario_id'
                partes = clase_id.split('|')
                if len(partes) != 2:
                    print(f"ERROR: Formato de ID de clase inválido: {clase_id}")
                    continue
                
                fecha_str = partes[0]
                horario_id = int(partes[1])
                
                print(f"Procesando: fecha={fecha_str}, horario_id={horario_id}")
                
                # Convertir la fecha a objeto date
                try:
                    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    print(f"  * Fecha convertida: {fecha_obj.strftime('%d/%m/%Y')}")
                except ValueError:
                    print(f"ERROR: Formato de fecha inválido: {fecha_str}")
                    continue
                
                # Obtener el horario
                horario = HorarioClase.query.get(horario_id)
                if not horario:
                    print(f"ERROR: Horario con ID={horario_id} no encontrado")
                    continue
                
                print(f"  * Horario: ID={horario.id}, Nombre={horario.nombre}, Hora={horario.hora_inicio}")
                
                # Verificar si ya existe un registro para esta fecha y horario
                registro_existente = ClaseRealizada.query.filter_by(
                    fecha=fecha_obj,
                    horario_id=horario_id
                ).first()
                
                if registro_existente:
                    print(f"  * OMITIDO: Ya existe un registro para fecha={fecha_obj.strftime('%d/%m/%Y')}, horario_id={horario_id}, ID={registro_existente.id}")
                    continue
                
                # Determinar el profesor a utilizar
                profesor_id = profesor_id_alternativo if profesor_id_alternativo else horario.profesor_id
                profesor = Profesor.query.get(profesor_id)
                print(f"  * Profesor: ID={profesor_id}, Nombre={(profesor.nombre + ' ' + profesor.apellido) if profesor else 'Desconocido'}")
                
                # Preparar observaciones y valores según si se registran como canceladas
                if registrar_como_canceladas:
                    observaciones = f"CLASE CANCELADA - Motivo: {motivo_cancelacion} - Registrada en masa el {fecha_actual}"
                    hora_llegada = None
                    cantidad_alumnos = 0
                else:
                    observaciones = f"Registrada automáticamente el {fecha_actual}"
                    hora_llegada = None  # No registramos hora de llegada en registro masivo
                    cantidad_alumnos = 0  # Por defecto, sin alumnos
                
                # Crear una nueva clase - IMPORTANTE: usar la fecha original de la clase
                nueva_clase = ClaseRealizada(
                    fecha=fecha_obj,  # Fecha programada original de la clase
                    horario_id=horario_id,
                    profesor_id=profesor_id,
                    hora_llegada_profesor=hora_llegada,
                    cantidad_alumnos=cantidad_alumnos,
                    observaciones=observaciones,
                    fecha_registro=datetime.utcnow()  # Fecha actual (cuándo se registra)
                )
                
                # Guardar en la base de datos
                db.session.add(nueva_clase)
                db.session.commit()
                
                db.session.refresh(nueva_clase)
                
                # Verificar que la fecha guardada es la correcta
                clase_guardada = ClaseRealizada.query.get(nueva_clase.id)
                fecha_guardada = clase_guardada.fecha.strftime('%d/%m/%Y')
                fecha_esperada = fecha_obj.strftime('%d/%m/%Y')
                
                if fecha_guardada == fecha_esperada:
                    print(f"  * ✅ REGISTRADA: ID={nueva_clase.id}, Fecha correcta={fecha_guardada}")
                else:
                    print(f"  * ⚠️ ADVERTENCIA: Fecha guardada ({fecha_guardada}) difiere de la esperada ({fecha_esperada})")
                
                # Registrar éxito
                clases_registradas += 1
                clases_procesadas.append({
                    'fecha': fecha_obj,
                    'horario_id': horario_id,
                    'id': nueva_clase.id
                })
                
            except Exception as e:
                db.session.rollback()
                print(f"  * ❌ ERROR: No se pudo registrar la clase {clase_id} - {str(e)}")
                trace = traceback.format_exc()
                print(trace)
                continue
        
        print("-"*40)
        print(f"RESULTADO: Se registraron {clases_registradas} de {len(clases_ids)} clases")
        print("="*50)
        
        # Mensaje de resultados
        if clases_registradas > 0:
            flash(f'Se registraron {clases_registradas} clases correctamente', 'success')
            
            # Limpiar caché para asegurar que las vistas se actualicen
            db.session.close()
            db.session = db.create_scoped_session()
            
            # Añadir timestamp para forzar actualización completa
            timestamp = int(time_module.time())
            
            # Si hay clases procesadas, redirigir al informe del mes correspondiente
            if clases_procesadas:
                primera_fecha = clases_procesadas[0]['fecha']
                mes = primera_fecha.month
                anio = primera_fecha.year
                print(f"Redirigiendo a informe mensual: {mes}/{anio}")
                return redirect(url_for('informe_mensual', mes=mes, anio=anio, refresh=timestamp, clear_cache=1))
            else:
                return redirect(url_for('clases_no_registradas', refresh=timestamp, clear_cache=1))
        else:
            flash('No se registró ninguna clase nueva', 'warning')
            return redirect(url_for('clases_no_registradas'))
            
    # Si no es POST o hay otro problema
    return redirect(url_for('clases_no_registradas'))

# Add initialization code to ensure the application starts correctly
if __name__ == '__main__':
    # Ensure upload directories exist
    ensure_upload_dirs()
    
    # Create database tables if they don't exist yet
    with app.app_context():
        db.create_all()
    
    # Inicializar scheduler de notificaciones para clases no registradas
    setup_notification_scheduler(app)
    
    # Start the app
    app.run(debug=True, port=8111)

@app.route('/diagnostico/eliminar_clase/<int:id>')
def diagnostico_eliminar_clase(id):
    """
    Ruta de diagnóstico para analizar y eliminar clases con problemas.
    Esta ruta utiliza un enfoque que evita restricciones comunes que pueden
    bloquear la eliminación de clases.
    """
    try:
        # Obtener la clase
        clase = ClaseRealizada.query.get_or_404(id)
        
        # Información de la clase para mostrar en el resultado
        info_clase = {
            'id': clase.id,
            'fecha': str(clase.fecha),
            'horario_id': clase.horario_id,
            'profesor_id': clase.profesor_id,
            'nombre_clase': clase.horario.nombre if clase.horario else "Desconocido",
            'profesor': f"{clase.profesor.nombre} {clase.profesor.apellido}" if clase.profesor else "Desconocido",
            'audio_file': clase.audio_file
        }
        
        # Eliminar archivo de audio si existe
        if clase.audio_file:
            try:
                # Buscar el archivo en diferentes ubicaciones
                audio_paths = []
                
                # Ruta en formato antiguo
                upload_folder = os.path.join(app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'audios')
                audio_path1 = os.path.join(upload_folder, clase.audio_file)
                audio_paths.append(audio_path1)
                
                # Ruta en formato nuevo
                if '/' in clase.audio_file or '\\' in clase.audio_file:
                    audio_path2 = os.path.join(upload_folder, 'permanent', clase.audio_file)
                    audio_paths.append(audio_path2)
                else:
                    horario_dir = os.path.join(upload_folder, 'permanent', f'horario_{clase.horario_id}')
                    audio_path3 = os.path.join(horario_dir, clase.audio_file)
                    audio_paths.append(audio_path3)
                
                # Intentar eliminar el archivo de audio en todas las ubicaciones posibles
                for path in audio_paths:
                    if os.path.exists(path):
                        os.remove(path)
                        info_clase['audio_eliminado'] = f"Archivo de audio eliminado: {path}"
                        break
            except Exception as e:
                info_clase['error_audio'] = f"Error al eliminar archivo de audio: {str(e)}"
        
        # Usar una sesión nueva para evitar problemas con transacciones existentes
        from sqlalchemy.orm import Session
        from sqlalchemy import create_engine
        
        # Usar la misma URI de base de datos que la aplicación
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        session = Session(engine)
        
        try:
            # Obtener la clase en esta nueva sesión
            clase_nueva_sesion = session.query(ClaseRealizada).get(id)
            
            if clase_nueva_sesion:
                # Eliminar la clase
                session.delete(clase_nueva_sesion)
                session.commit()
                info_clase['resultado'] = "Clase eliminada exitosamente con el método alternativo"
            else:
                info_clase['resultado'] = "No se encontró la clase en la nueva sesión"
        except Exception as e:
            session.rollback()
            info_clase['error_eliminar'] = f"Error al eliminar con método alternativo: {str(e)}"
            
            # Intentar con el método original
            try:
                db.session.delete(clase)
                db.session.commit()
                info_clase['resultado'] = "Clase eliminada exitosamente con el método original"
            except Exception as e2:
                db.session.rollback()
                info_clase['error_eliminar2'] = f"Error al eliminar con método original: {str(e2)}"
                
                # Último intento: eliminar directamente con SQL
                try:
                    db.session.execute(f"DELETE FROM clase_realizada WHERE id = {id}")
                    db.session.commit()
                    info_clase['resultado'] = "Clase eliminada exitosamente con SQL directo"
                except Exception as e3:
                    db.session.rollback()
                    info_clase['error_eliminar3'] = f"Error al eliminar con SQL directo: {str(e3)}"
                    info_clase['resultado'] = "No se pudo eliminar la clase"
        finally:
            session.close()
        
        # Redireccionar o mostrar información
        return jsonify(info_clase)
    except Exception as e:
        return jsonify({
            'error': f"Error general: {str(e)}",
            'id': id
        }), 500

@app.route('/configuracion/exportar_db', methods=['GET'])
def exportar_db():
    """Exportar el archivo de la base de datos completo"""
    try:
        # Ruta al archivo de base de datos
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
        
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            flash('No se encontró el archivo de base de datos', 'danger')
            return redirect(url_for('configuracion_exportar'))
        
        # Crear una copia temporal para exportar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'gimnasio_backup_{timestamp}.db'
        temp_path = os.path.join(os.path.dirname(db_path), 'backups', backup_filename)
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        # Copiar el archivo (sin bloquear la base de datos)
        import shutil
        shutil.copy2(db_path, temp_path)
        
        # Enviar el archivo al cliente
        return send_file(temp_path, 
                         as_attachment=True, 
                         download_name=backup_filename,
                         mimetype='application/octet-stream')
    
    except Exception as e:
        app.logger.error(f"Error exportando la base de datos: {str(e)}")
        flash(f'Error al exportar la base de datos: {str(e)}', 'danger')
        return redirect(url_for('configuracion_exportar'))

@app.route('/configuracion/exportar_db_completo', methods=['GET'])
def exportar_db_completo():
    """Exportar el archivo de la base de datos junto con los archivos de audio"""
    try:
        import shutil
        import zipfile
        import time
        import glob
        
        # Registrar inicio del proceso
        app.logger.info("="*80)
        app.logger.info("INICIANDO PROCESO DE BACKUP COMPLETO (DB + AUDIOS)")
        app.logger.info(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        app.logger.info("="*80)
        
        # Imprimir en consola también para diagnóstico inmediato
        print("="*80)
        print("INICIANDO PROCESO DE BACKUP COMPLETO (DB + AUDIOS)")
        print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Ruta al archivo de base de datos
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
        
        # Verificar que el archivo existe
        if not os.path.exists(db_path):
            mensaje = 'No se encontró el archivo de base de datos'
            app.logger.error(mensaje)
            print(f"ERROR: {mensaje}")
            flash(mensaje, 'danger')
            return redirect(url_for('configuracion_exportar'))
        
        # Crear una carpeta temporal para la exportación
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_dir = os.path.join(os.path.dirname(db_path), 'backups', f'export_temp_{timestamp}')
        os.makedirs(temp_dir, exist_ok=True)
        app.logger.info(f"Directorio temporal de backup creado: {temp_dir}")
        print(f"Directorio temporal de backup creado: {temp_dir}")
        
        # Copiar la base de datos a la carpeta temporal
        backup_filename = f'gimnasio_backup_{timestamp}.db'
        temp_db_path = os.path.join(temp_dir, backup_filename)
        shutil.copy2(db_path, temp_db_path)
        app.logger.info(f"Base de datos copiada a: {temp_db_path}")
        print(f"Base de datos copiada a: {temp_db_path}")
        
        # Preparar la carpeta principal para los archivos de audio
        upload_base = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        audio_base_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_base, 'audios')
        temp_audio_folder = os.path.join(temp_dir, 'audios')
        
        # Crear directorio de audios en la carpeta temporal
        os.makedirs(temp_audio_folder, exist_ok=True)
        app.logger.info(f"Directorio temporal para audios creado: {temp_audio_folder}")
        print(f"Directorio temporal para audios creado: {temp_audio_folder}")
        
        # Variable para contar archivos
        audio_count = 0
        audio_errors = 0
        total_size = 0
        
        # 1. Copiar audios de la carpeta principal
        if os.path.exists(audio_base_folder):
            app.logger.info(f"Copiando audios de la carpeta principal: {audio_base_folder}")
            print(f"Copiando audios de la carpeta principal: {audio_base_folder}")
            
            for audio_file in os.listdir(audio_base_folder):
                src_path = os.path.join(audio_base_folder, audio_file)
                if os.path.isfile(src_path):
                    try:
                        # Saltar archivos temporales o de sistema
                        if audio_file.startswith('.') or audio_file == 'permanent':
                            continue
                            
                        dest_path = os.path.join(temp_audio_folder, audio_file)
                        shutil.copy2(src_path, dest_path)
                        file_size = os.path.getsize(src_path)
                        total_size += file_size
                        audio_count += 1
                        
                        app.logger.debug(f"Audio copiado: {audio_file} ({file_size/1024:.2f} KB)")
                        print(f"Audio copiado: {audio_file} ({file_size/1024:.2f} KB)")
                    except Exception as e:
                        error_msg = f"Error al copiar audio {audio_file}: {str(e)}"
                        app.logger.error(error_msg)
                        print(f"ERROR: {error_msg}")
                        audio_errors += 1
        
        # 2. Copiar audios de la estructura de carpetas por horario (permanent)
        permanent_audio_dir = os.path.join(audio_base_folder, 'permanent')
        if os.path.exists(permanent_audio_dir):
            app.logger.info(f"Procesando carpeta de audios permanentes: {permanent_audio_dir}")
            print(f"Procesando carpeta de audios permanentes: {permanent_audio_dir}")
            
            # Crear directorio para audios permanentes
            temp_permanent_dir = os.path.join(temp_audio_folder, 'permanent')
            os.makedirs(temp_permanent_dir, exist_ok=True)
            
            # Obtener todos los directorios de horarios
            horario_dirs = [d for d in os.listdir(permanent_audio_dir) 
                           if os.path.isdir(os.path.join(permanent_audio_dir, d))]
            
            app.logger.info(f"Se encontraron {len(horario_dirs)} directorios de horarios")
            print(f"Se encontraron {len(horario_dirs)} directorios de horarios")
            
            # Copiar audios de cada directorio de horario
            for horario_dir in horario_dirs:
                src_horario_path = os.path.join(permanent_audio_dir, horario_dir)
                dest_horario_path = os.path.join(temp_permanent_dir, horario_dir)
                
                # Crear directorio del horario en el destino
                os.makedirs(dest_horario_path, exist_ok=True)
                
                horario_file_count = 0
                horario_errors = 0
                
                # Copiar cada archivo de audio en el directorio del horario
                for audio_file in os.listdir(src_horario_path):
                    src_file_path = os.path.join(src_horario_path, audio_file)
                    
                    if os.path.isfile(src_file_path):
                        try:
                            dest_file_path = os.path.join(dest_horario_path, audio_file)
                            shutil.copy2(src_file_path, dest_file_path)
                            file_size = os.path.getsize(src_file_path)
                            total_size += file_size
                            audio_count += 1
                            horario_file_count += 1
                            
                            app.logger.debug(f"Audio {horario_dir}/{audio_file} copiado ({file_size/1024:.2f} KB)")
                        except Exception as e:
                            error_msg = f"Error al copiar audio {horario_dir}/{audio_file}: {str(e)}"
                            app.logger.error(error_msg)
                            print(f"ERROR: {error_msg}")
                            audio_errors += 1
                            horario_errors += 1
                
                app.logger.info(f"Horario {horario_dir}: {horario_file_count} archivos copiados, {horario_errors} errores")
                print(f"Horario {horario_dir}: {horario_file_count} archivos copiados, {horario_errors} errores")
        
        # Crear archivo ZIP con todo el contenido
        zip_filename = f'gimnasio_backup_completo_{timestamp}.zip'
        zip_path = os.path.join(os.path.dirname(db_path), 'backups', zip_filename)
        
        app.logger.info(f"Creando archivo ZIP: {zip_path}")
        print(f"Creando archivo ZIP: {zip_path}")
        
        audio_files_in_zip = 0
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Agregar la base de datos
            zipf.write(temp_db_path, arcname=backup_filename)
            
            # Agregar los archivos de audio
            for root, _, files in os.walk(temp_audio_folder):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        # Calcular la ruta relativa dentro del ZIP
                        rel_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname=rel_path)
                        audio_files_in_zip += 1
                        app.logger.debug(f"Archivo agregado al ZIP: {rel_path}")
                    except Exception as e:
                        error_msg = f"Error al agregar archivo al ZIP {file}: {str(e)}"
                        app.logger.error(error_msg)
                        print(f"ERROR: {error_msg}")
        
        # Verificar que todos los archivos se agregaron al ZIP
        zip_verification = zipfile.ZipFile(zip_path, 'r')
        zip_file_count = len(zip_verification.namelist())
        zip_verification.close()
        
        # Eliminar directorio temporal después de crear el ZIP
        shutil.rmtree(temp_dir)
        app.logger.info(f"Directorio temporal eliminado: {temp_dir}")
        print(f"Directorio temporal eliminado: {temp_dir}")
        
        # Calcular tamaño del ZIP
        zip_size = os.path.getsize(zip_path)
        
        # Registrar éxito
        summary = (
            f"Backup completo creado: {zip_path}\n"
            f"- Tamaño del archivo ZIP: {zip_size/1024/1024:.2f} MB\n"
            f"- Archivos de audio procesados: {audio_count}\n"
            f"- Tamaño total de audios: {total_size/1024/1024:.2f} MB\n"
            f"- Archivos incluidos en el ZIP: {zip_file_count}\n"
            f"- Errores durante el proceso: {audio_errors}"
        )
        
        app.logger.info("="*50)
        app.logger.info("RESUMEN DEL BACKUP:")
        app.logger.info(summary)
        app.logger.info("="*50)
        
        print("="*50)
        print("RESUMEN DEL BACKUP:")
        print(summary)
        print("="*50)
        
        # Enviar el archivo ZIP al cliente
        return send_file(zip_path, 
                         as_attachment=True, 
                         download_name=zip_filename,
                         mimetype='application/zip')
    
    except Exception as e:
        error_msg = f"Error exportando backup completo: {str(e)}"
        app.logger.error(error_msg)
        app.logger.error(traceback.format_exc())
        
        print("="*50)
        print(f"ERROR EN BACKUP: {error_msg}")
        print(traceback.format_exc())
        print("="*50)
        
        flash(f'Error al exportar el backup completo: {str(e)}', 'danger')
        return redirect(url_for('configuracion_exportar'))

@app.route('/configuracion/importar_db_completo', methods=['POST'])
def importar_db_completo():
    """Importar un archivo ZIP con la base de datos y archivos de audio"""
    if 'zip_file' not in request.files:
        flash('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('configuracion_exportar'))
    
    zip_file = request.files['zip_file']
    
    if zip_file.filename == '':
        flash('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('configuracion_exportar'))
    
    if not zip_file.filename.endswith('.zip'):
        flash('El archivo debe tener extensión .zip', 'danger')
        return redirect(url_for('configuracion_exportar'))
    
    try:
        import zipfile
        import tempfile
        import shutil
        import glob
        
        # Registrar inicio del proceso
        app.logger.info("="*80)
        app.logger.info("INICIANDO PROCESO DE IMPORTACIÓN DE BACKUP COMPLETO (DB + AUDIOS)")
        app.logger.info(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        app.logger.info(f"Archivo ZIP: {zip_file.filename}")
        app.logger.info("="*80)
        
        # Imprimir en consola también
        print("="*80)
        print("INICIANDO PROCESO DE IMPORTACIÓN DE BACKUP COMPLETO (DB + AUDIOS)")
        print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Archivo ZIP: {zip_file.filename}")
        print("="*80)
        
        # Crear directorio temporal para descomprimir
        with tempfile.TemporaryDirectory() as temp_dir:
            app.logger.info(f"Directorio temporal creado: {temp_dir}")
            print(f"Directorio temporal creado: {temp_dir}")
            
            zip_path = os.path.join(temp_dir, 'backup.zip')
            zip_file.save(zip_path)
            
            # Verificar el contenido del ZIP antes de descomprimirlo
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_contents = zip_ref.namelist()
                    db_files = [f for f in zip_contents if f.endswith('.db')]
                    app.logger.info(f"Contenido del ZIP: {len(zip_contents)} archivos, {len(db_files)} bases de datos")
                    print(f"Contenido del ZIP: {len(zip_contents)} archivos, {len(db_files)} bases de datos")
                    
                    if not db_files:
                        error_msg = "El archivo ZIP no contiene una base de datos válida"
                        app.logger.error(error_msg)
                        print(f"ERROR: {error_msg}")
                        flash(error_msg, 'danger')
                        return redirect(url_for('configuracion_exportar'))
                    
                    # Extraer contenido del ZIP
                    app.logger.info("Extrayendo archivos del ZIP...")
                    print("Extrayendo archivos del ZIP...")
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                error_msg = "El archivo no es un ZIP válido o está corrupto"
                app.logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                flash(error_msg, 'danger')
                return redirect(url_for('configuracion_exportar'))
            
            # Buscar el archivo .db en el directorio temporal
            db_file = None
            for file in db_files:
                db_file = os.path.join(temp_dir, file)
                if os.path.exists(db_file):
                    break
            
            if not db_file or not os.path.exists(db_file):
                error_msg = "No se pudo encontrar la base de datos en el archivo ZIP"
                app.logger.error(error_msg)
                print(f"ERROR: {error_msg}")
                flash(error_msg, 'danger')
                return redirect(url_for('configuracion_exportar'))
            
            app.logger.info(f"Base de datos encontrada: {db_file}")
            print(f"Base de datos encontrada: {db_file}")
            
            # Ruta al archivo de base de datos original
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
            
            # Crear una copia de seguridad antes de reemplazar
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(os.path.dirname(db_path), 'backups', f'gimnasio_antes_importar_{timestamp}.db')
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Hacer copia de seguridad de la DB actual
            shutil.copy2(db_path, backup_path)
            app.logger.info(f"Backup de la base de datos actual creado: {backup_path}")
            print(f"Backup de la base de datos actual creado: {backup_path}")
            
            # Hacer copia de seguridad de los audios actuales
            upload_base = app.config.get('UPLOAD_FOLDER', 'static/uploads')
            audio_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), upload_base, 'audios')
            audio_backup_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups', f'audios_backup_{timestamp}')
            
            audio_backup_count = 0
            if os.path.exists(audio_folder):
                app.logger.info(f"Realizando backup de los audios actuales: {audio_folder} -> {audio_backup_folder}")
                print(f"Realizando backup de los audios actuales: {audio_folder} -> {audio_backup_folder}")
                
                # Hacer una copia de seguridad completa de la carpeta de audios
                shutil.copytree(audio_folder, audio_backup_folder, dirs_exist_ok=True)
                
                # Contar archivos respaldados
                audio_backup_count = sum(
                    len(files) for _, _, files in os.walk(audio_backup_folder)
                )
                
                app.logger.info(f"Se han respaldado {audio_backup_count} archivos de audio en {audio_backup_folder}")
                print(f"Se han respaldado {audio_backup_count} archivos de audio en {audio_backup_folder}")
            
            # Cerrar la conexión actual a la base de datos
            app.logger.info("Cerrando la conexión actual a la base de datos...")
            print("Cerrando la conexión actual a la base de datos...")
            db.session.remove()
            
            # Reemplazar la base de datos
            app.logger.info(f"Reemplazando base de datos: {db_file} -> {db_path}")
            print(f"Reemplazando base de datos: {db_file} -> {db_path}")
            shutil.copy2(db_file, db_path)
            
            # Verificar si el ZIP incluye archivos de audio
            extracted_audio_folder = os.path.join(temp_dir, 'audios')
            
            audio_restored_count = 0
            audio_errors = 0
            
            if os.path.exists(extracted_audio_folder):
                app.logger.info(f"Restaurando archivos de audio: {extracted_audio_folder} -> {audio_folder}")
                print(f"Restaurando archivos de audio: {extracted_audio_folder} -> {audio_folder}")
                
                # Asegurar que el directorio de audio existe
                os.makedirs(audio_folder, exist_ok=True)
                
                # Restaurar la estructura completa de archivos de audio
                for root, dirs, files in os.walk(extracted_audio_folder):
                    # Calcular la ruta relativa
                    rel_path = os.path.relpath(root, extracted_audio_folder)
                    
                    # Crear la estructura de directorios en el destino
                    if rel_path != '.':
                        target_dir = os.path.join(audio_folder, rel_path)
                        os.makedirs(target_dir, exist_ok=True)
                        app.logger.debug(f"Creado directorio: {target_dir}")
                    
                    # Copiar cada archivo
                    for file in files:
                        try:
                            src_file = os.path.join(root, file)
                            
                            # Determinar la ruta de destino
                            if rel_path == '.':
                                # Archivo en la raíz de audios
                                dest_file = os.path.join(audio_folder, file)
                            else:
                                # Archivo en subdirectorio
                                dest_file = os.path.join(audio_folder, rel_path, file)
                            
                            # Copiar el archivo
                            shutil.copy2(src_file, dest_file)
                            audio_restored_count += 1
                            
                            if audio_restored_count % 50 == 0:
                                app.logger.info(f"Restaurados {audio_restored_count} archivos hasta ahora...")
                                print(f"Restaurados {audio_restored_count} archivos hasta ahora...")
                            
                        except Exception as e:
                            error_msg = f"Error al restaurar audio {rel_path}/{file}: {str(e)}"
                            app.logger.error(error_msg)
                            print(f"ERROR: {error_msg}")
                            audio_errors += 1
                
                app.logger.info(f"Se han restaurado {audio_restored_count} archivos de audio desde el backup")
                print(f"Se han restaurado {audio_restored_count} archivos de audio desde el backup")
                
                if audio_errors > 0:
                    app.logger.warning(f"Hubo {audio_errors} errores durante la restauración de audios")
                    print(f"ADVERTENCIA: Hubo {audio_errors} errores durante la restauración de audios")
        
        # Registrar resumen del proceso
        summary = (
            f"Backup completo importado exitosamente.\n"
            f"- Base de datos respaldada en: {backup_path}\n"
            f"- Respaldo de {audio_backup_count} archivos de audio en: {audio_backup_folder}\n"
            f"- {audio_restored_count} archivos de audio restaurados\n"
            f"- {audio_errors} errores durante la restauración"
        )
        
        app.logger.info("="*50)
        app.logger.info("RESUMEN DE LA IMPORTACIÓN:")
        app.logger.info(summary)
        app.logger.info("="*50)
        
        print("="*50)
        print("RESUMEN DE LA IMPORTACIÓN:")
        print(summary)
        print("="*50)
        
        flash('Backup completo importado exitosamente. Se ha creado una copia de seguridad de la base de datos y archivos de audio anteriores.', 'success')
        
        return redirect(url_for('configuracion_exportar'))
    
    except Exception as e:
        error_msg = f"Error importando backup completo: {str(e)}"
        app.logger.error(error_msg)
        app.logger.error(traceback.format_exc())
        
        print("="*50)
        print(f"ERROR EN IMPORTACIÓN: {error_msg}")
        print(traceback.format_exc())
        print("="*50)
        
        flash(f'Error al importar el backup completo: {str(e)}', 'danger')
        return redirect(url_for('configuracion_exportar'))

@app.route('/generate-logo-png')
def generate_logo_png():
    """Generate a PNG version of the O2 logo and save it to static/img/o2-logo.png"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        import os
        
        # Create a new image with a transparent background
        size = (200, 200)
        img = Image.new('RGBA', size, color=(34, 34, 34, 255))  # Dark background
        draw = ImageDraw.Draw(img)
        
        # Draw outer circle
        draw.ellipse([(10, 10), (190, 190)], outline=(255, 255, 255, 255), width=10)
        
        # Draw inner circle
        draw.ellipse([(30, 30), (170, 170)], outline=(255, 255, 255, 255), width=10)
        
        # Try to add text "2" (this part might not work if the font is not available)
        try:
            font = ImageFont.truetype("arial.ttf", 100)
        except IOError:
            font = ImageFont.load_default()
        
        # Draw the "2" in the center
        draw.text((100, 80), "2", font=font, fill=(255, 255, 255, 255), anchor="mm")
        
        # Save the image
        output_path = os.path.join(app.static_folder, 'img', 'o2-logo.png')
        img.save(output_path)
        
        return f"Logo generated and saved to {output_path}"
    
    except Exception as e:
        app.logger.error(f"Error generating logo: {str(e)}")
        return f"Error generating logo: {str(e)}", 500

@app.route('/generate-favicon-ico')
def generate_favicon_ico():
    """Generate a favicon.ico file from the O2 logo SVG"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        import os
        
        # Crear las imágenes para diferentes tamaños (16x16, 32x32, 48x48)
        sizes = [16, 32, 48]
        favicon_images = []
        
        for size in sizes:
            # Crear una nueva imagen con fondo negro
            img = Image.new('RGBA', (size, size), color=(34, 34, 34, 255))
            draw = ImageDraw.Draw(img)
            
            # Calcular proporciones para los círculos
            outer_radius = int(size * 0.95 / 2)
            inner_radius = int(size * 0.7 / 2)
            circle_width = max(1, int(size * 0.08))  # Al menos 1 píxel de ancho
            
            # Dibujar círculo exterior
            draw.ellipse(
                [(size/2 - outer_radius, size/2 - outer_radius), 
                 (size/2 + outer_radius, size/2 + outer_radius)], 
                outline=(255, 255, 255, 255), width=circle_width
            )
            
            # Dibujar círculo interior
            draw.ellipse(
                [(size/2 - inner_radius, size/2 - inner_radius), 
                 (size/2 + inner_radius, size/2 + inner_radius)], 
                outline=(255, 255, 255, 255), width=circle_width
            )
            
            # En tamaños pequeños, usar un punto blanco en lugar del número "2"
            if size < 32:
                # Dibujar un punto en el centro
                center_radius = max(1, int(size * 0.15))
                draw.ellipse(
                    [(size/2 - center_radius, size/2 - center_radius), 
                     (size/2 + center_radius, size/2 + center_radius)], 
                    fill=(255, 255, 255, 255)
                )
            else:
                # Intentar usar una fuente para el "2"
                try:
                    # La fuente y tamaño dependen del tamaño del icono
                    font_size = int(size * 0.6)
                    font = ImageFont.truetype("arial.ttf", font_size)
                    # Posicionar el texto centrado
                    text_width = font_size * 0.6  # Aproximado
                    draw.text((size/2 - text_width/2, size/2 - font_size/2), "2", 
                              font=font, fill=(255, 255, 255, 255))
                except Exception:
                    # Si falla, usar un punto en el centro como fallback
                    center_radius = int(size * 0.2)
                    draw.ellipse(
                        [(size/2 - center_radius, size/2 - center_radius), 
                         (size/2 + center_radius, size/2 + center_radius)], 
                        fill=(255, 255, 255, 255)
                    )
            
            favicon_images.append(img)
        
        # Guardar como archivo .ico con múltiples tamaños
        output_path = os.path.join(app.static_folder, 'favicon.ico')
        favicon_images[0].save(
            output_path, 
            format='ICO', 
            sizes=[(size, size) for size in sizes],
            append_images=favicon_images[1:]
        )
        
        return f"Favicon.ico generado en {output_path}"
    
    except Exception as e:
        app.logger.error(f"Error generando favicon.ico: {str(e)}")
        return f"Error generando favicon.ico: {str(e)}", 500

@app.route('/asistencia/depurar-base-datos')
def depurar_asistencia_base_datos():
    """
    Función para depurar problemas con clases no registradas.
    Esta función identificará y eliminará duplicados en la base de datos.
    """
    try:
        # Verificar si hay clases duplicadas
        duplicados = db.session.query(
            ClaseRealizada.fecha,
            ClaseRealizada.horario_id,
            func.count().label('total')
        ).group_by(
            ClaseRealizada.fecha,
            ClaseRealizada.horario_id
        ).having(func.count() > 1).all()
        
        if not duplicados:
            flash('No se encontraron duplicados en la base de datos', 'success')
            return redirect(url_for('control_asistencia'))
        
        total_duplicados = len(duplicados)
        flash(f'Se encontraron {total_duplicados} conjuntos de clases duplicadas', 'warning')
        
        # Eliminar duplicados
        clases_eliminadas = 0
        for duplicado in duplicados:
            fecha = duplicado.fecha
            horario_id = duplicado.horario_id
            
            # Obtener todas las clases con esa fecha y horario
            clases = ClaseRealizada.query.filter_by(
                fecha=fecha,
                horario_id=horario_id
            ).order_by(ClaseRealizada.id).all()
            
            # Mantener la primera clase y eliminar las demás
            for clase in clases[1:]:
                db.session.delete(clase)
                clases_eliminadas += 1
                
        db.session.commit()
        flash(f'Se eliminaron {clases_eliminadas} clases duplicadas', 'success')
        
        # Forzar un reinicio de la sesión para limpiar la caché
        db.session.remove()
        db.session = db.create_scoped_session()
        
        return redirect(url_for('control_asistencia'))
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error al depurar la base de datos: {str(e)}', 'danger')
        return redirect(url_for('control_asistencia'))

@app.route('/mantenimiento/depurar-base-datos')
def depurar_base_datos():
    """
    Función para depurar la base de datos y resolver problemas comunes.
    Esta ruta permite realizar operaciones de limpieza y mantenimiento.
    """
    resultados = {
        'success': True,
        'mensajes': []
    }
    
    try:
        # 1. Reiniciar completamente la sesión de base de datos
        db.session.close()
        db.session = db.create_scoped_session()
        resultados['mensajes'].append("Sesión de base de datos reiniciada exitosamente")
        
        # 2. Verificar clases duplicadas (misma fecha y horario)
        sql_duplicados = """
        SELECT cr1.id, cr1.fecha, cr1.horario_id, cr1.profesor_id
        FROM clase_realizada cr1
        JOIN (
            SELECT fecha, horario_id, COUNT(*) as cnt
            FROM clase_realizada
            GROUP BY fecha, horario_id
            HAVING COUNT(*) > 1
        ) cr2 ON cr1.fecha = cr2.fecha AND cr1.horario_id = cr2.horario_id
        ORDER BY cr1.fecha, cr1.horario_id, cr1.id
        """
        
        duplicados = db.session.execute(sql_duplicados).fetchall()
        
        if duplicados:
            resultados['mensajes'].append(f"Se encontraron {len(duplicados)} clases duplicadas")
            
            # Agrupar por fecha y horario
            grupos_duplicados = {}
            for dup in duplicados:
                key = (dup.fecha, dup.horario_id)
                if key not in grupos_duplicados:
                    grupos_duplicados[key] = []
                grupos_duplicados[key].append(dup.id)
            
            # Resolver duplicados (mantener el ID más bajo y eliminar los demás)
            for key, ids in grupos_duplicados.items():
                fecha, horario_id = key
                ids_ordenados = sorted(ids)
                id_mantener = ids_ordenados[0]
                ids_eliminar = ids_ordenados[1:]
                
                resultados['mensajes'].append(f"Manteniendo clase ID {id_mantener} para fecha {fecha} y horario {horario_id}")
                
                for id_eliminar in ids_eliminar:
                    try:
                        # Eliminar directo con SQL para evitar restricciones
                        db.session.execute(f"DELETE FROM clase_realizada WHERE id = {id_eliminar}")
                        resultados['mensajes'].append(f"Eliminada clase duplicada ID {id_eliminar}")
                    except Exception as e:
                        resultados['mensajes'].append(f"Error al eliminar clase ID {id_eliminar}: {str(e)}")
            
            db.session.commit()
        else:
            resultados['mensajes'].append("No se encontraron clases duplicadas")
        
        # 3. Buscar clases con referencias a horarios que ya no existen
        sql_huerfanas = """
        SELECT cr.id, cr.fecha, cr.horario_id
        FROM clase_realizada cr
        LEFT JOIN horario_clase hc ON cr.horario_id = hc.id
        WHERE hc.id IS NULL
        """
        
        huerfanas = db.session.execute(sql_huerfanas).fetchall()
        
        if huerfanas:
            resultados['mensajes'].append(f"Se encontraron {len(huerfanas)} clases huérfanas (sin horario asociado)")
            
            for h in huerfanas:
                try:
                    # Intentar recuperar eliminando solo la clase problemática
                    db.session.execute(f"DELETE FROM clase_realizada WHERE id = {h.id}")
                    resultados['mensajes'].append(f"Eliminada clase huérfana ID {h.id} (fecha: {h.fecha}, horario_id inválido: {h.horario_id})")
                except Exception as e:
                    resultados['mensajes'].append(f"Error al eliminar clase huérfana ID {h.id}: {str(e)}")
            
            db.session.commit()
        else:
            resultados['mensajes'].append("No se encontraron clases huérfanas")
        
        # 4. Verificar consistencia de profesores
        sql_prof_inconsistentes = """
        SELECT cr.id, cr.fecha, cr.horario_id, cr.profesor_id as prof_clase, hc.profesor_id as prof_horario
        FROM clase_realizada cr
        JOIN horario_clase hc ON cr.horario_id = hc.id
        WHERE cr.profesor_id != hc.profesor_id
        """
        
        inconsistentes = db.session.execute(sql_prof_inconsistentes).fetchall()
        
        if inconsistentes:
            resultados['mensajes'].append(f"Se encontraron {len(inconsistentes)} clases con profesor inconsistente")
            
            for inc in inconsistentes:
                try:
                    # Corregir la inconsistencia actualizando el profesor de la clase al del horario
                    db.session.execute(
                        "UPDATE clase_realizada SET profesor_id = :prof_horario WHERE id = :id",
                        {'prof_horario': inc.prof_horario, 'id': inc.id}
                    )
                    resultados['mensajes'].append(f"Corregida clase ID {inc.id} - profesor actualizado de {inc.prof_clase} a {inc.prof_horario}")
                except Exception as e:
                    resultados['mensajes'].append(f"Error al corregir profesor en clase ID {inc.id}: {str(e)}")
            
            db.session.commit()
        else:
            resultados['mensajes'].append("No se encontraron clases con profesor inconsistente")
            
        # Final: Compactar la base de datos (VACUUM)
        try:
            db.session.execute("VACUUM")
            resultados['mensajes'].append("Base de datos compactada exitosamente")
        except Exception as e:
            resultados['mensajes'].append(f"Error al compactar la base de datos: {str(e)}")
        
        flash('Depuración de base de datos completada con éxito', 'success')
        
    except Exception as e:
        resultados['success'] = False
        resultados['mensajes'].append(f"Error general: {str(e)}")
        flash(f'Error durante la depuración: {str(e)}', 'danger')
    
    return render_template('mantenimiento/depurar_base_datos.html', resultados=resultados)

@app.route('/mantenimiento/test-debug')
def test_debug_mantenimiento():
    return "Ruta de prueba para mantenimiento activa"

@app.route('/test-debug-root')
def test_debug_root():
    return "Ruta de prueba en la raíz activa"

@app.route('/configuracion/importar_db', methods=['POST'])
def importar_db():
    """Importar un archivo de base de datos"""
    if 'db_file' not in request.files:
        flash('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('configuracion_exportar'))
    
    db_file = request.files['db_file']
    
    if db_file.filename == '':
        flash('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('configuracion_exportar'))
    
    if not db_file.filename.endswith('.db'):
        flash('El archivo debe tener extensión .db', 'danger')
        return redirect(url_for('configuracion_exportar'))
    
    try:
        # Ruta al archivo de base de datos original
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gimnasio.db')
        
        # Crear una copia de seguridad antes de reemplazar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(os.path.dirname(db_path), 'backups', f'gimnasio_antes_importar_{timestamp}.db')
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Copiar el archivo original como respaldo
        import shutil
        shutil.copy2(db_path, backup_path)
        
        # Hacer una copia de seguridad de los archivos de audio existentes
        audio_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'audios')
        audio_backup_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups', f'audios_backup_{timestamp}')
        
        # Verificar si hay archivos de audio para respaldar
        existing_audio_files = []
        if os.path.exists(audio_folder):
            # Crear directorio de respaldo de audios
            os.makedirs(audio_backup_folder, exist_ok=True)
            
            # Guardar lista de archivos existentes y copiarlos al respaldo
            existing_audio_files = os.listdir(audio_folder)
            for audio_file in existing_audio_files:
                if os.path.isfile(os.path.join(audio_folder, audio_file)):
                    shutil.copy2(
                        os.path.join(audio_folder, audio_file),
                        os.path.join(audio_backup_folder, audio_file)
                    )
            
            app.logger.info(f"Se han respaldado {len(existing_audio_files)} archivos de audio en {audio_backup_folder}")
        
        # Cerrar la conexión actual a la base de datos antes de reemplazarla
        db.session.remove()
        
        # Guardar el archivo subido como el nuevo archivo de base de datos
        db_file.save(db_path)
        
        # Restaurar los archivos de audio para que no se pierdan durante la importación
        os.makedirs(audio_folder, exist_ok=True)
        for audio_file in existing_audio_files:
            # Verificar si el archivo ya existe en el destino
            if not os.path.exists(os.path.join(audio_folder, audio_file)):
                # Copiar desde el respaldo si no existe
                shutil.copy2(
                    os.path.join(audio_backup_folder, audio_file),
                    os.path.join(audio_folder, audio_file)
                )
        
        # Registrar el éxito
        app.logger.info(f"Base de datos importada exitosamente. Respaldo guardado en {backup_path}")
        app.logger.info(f"Archivos de audio preservados en la importación. Respaldo en {audio_backup_folder}")
        flash('Base de datos importada exitosamente. Se ha creado una copia de seguridad de la base de datos anterior y se han preservado los archivos de audio.', 'success')
        
        # Reiniciar la aplicación (esto no funciona en todas las configuraciones)
        # En producción, esto debería mostrar instrucciones para reiniciar manualmente
        return redirect(url_for('configuracion_exportar'))
    
    except Exception as e:
        app.logger.error(f"Error importando la base de datos: {str(e)}")
        flash(f'Error al importar la base de datos: {str(e)}', 'danger')
        return redirect(url_for('configuracion_exportar'))

@app.route('/reporte_mensual/<int:mes>/<int:anio>')
def reporte_mensual(mes, anio):
    # Diccionario de nombres de meses en español
    MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    # Obtener el primer y último día del mes
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
    
    # Consultar horarios activos
    try:
        # Intentar usar el filtro activo
        sql_horarios_activos = """
        SELECT hc.id, hc.nombre, hc.hora_inicio, hc.duracion, p.nombre
        FROM horario_clase hc
        LEFT JOIN profesor p ON hc.profesor_id = p.id
        WHERE hc.activo = 1 AND hc.id NOT IN (
            SELECT horario_id FROM clase_realizada 
            WHERE fecha >= :fecha_inicio AND fecha <= :fecha_fin
        )
        """
    except Exception as e:
        # Si falla, es posible que la columna activo no exista
        app.logger.warning(f"Error al consultar con filtro activo en reporte_mensual: {str(e)}. Usando consulta sin filtro.")
        sql_horarios_activos = """
        SELECT hc.id, hc.nombre, hc.hora_inicio, hc.duracion, p.nombre
        FROM horario_clase hc
        LEFT JOIN profesor p ON hc.profesor_id = p.id
        WHERE hc.id NOT IN (
            SELECT horario_id FROM clase_realizada 
            WHERE fecha >= :fecha_inicio AND fecha <= :fecha_fin
        )
        """
    
    # Consultar clases completadas
    sql_clases_completadas = """
    SELECT hc.id, hc.nombre, hc.hora_inicio, hc.duracion, p.nombre
    FROM clase_realizada cr
    JOIN horario_clase hc ON cr.horario_id = hc.id
    LEFT JOIN profesor p ON cr.profesor_id = p.id
    WHERE cr.fecha >= :fecha_inicio AND cr.fecha <= :fecha_fin
    """
    
    # Ejecutar consultas
    schedules_active = db.session.execute(sql_horarios_activos, {
        'fecha_inicio': primer_dia, 
        'fecha_fin': ultimo_dia
    }).fetchall()
    
    schedules_completed = db.session.execute(sql_clases_completadas, {
        'fecha_inicio': primer_dia, 
        'fecha_fin': ultimo_dia
    }).fetchall()
    
    # Resto del código para procesar los horarios...
    horarios_procesados = []
    
    for row in schedules_active:
        clase_id = row[0]
        nombre_clase = row[1]
        hora_inicio_str = row[2]
        duracion_clase = row[3]
        nombre_instructor = row[4] if row[4] else "No asignado"
        realizada = False  # Al ser activa, no ha sido realizada

        # Manejo adecuado cuando hora_inicio es None o inválido
        if hora_inicio_str:
            try:
                hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M:%S').time() if hora_inicio_str else None
                hora_inicio_str = hora_inicio_str.split(':')[0] + ':' + hora_inicio_str.split(':')[1] if hora_inicio else "N/A"
                hora_fin_str = calcular_hora_fin(hora_inicio_str, duracion_clase)
                horario_str = f"{hora_inicio_str} - {hora_fin_str}" if hora_inicio_str != "N/A" else "Horario no disponible"
            except (ValueError, IndexError):
                horario_str = "Horario no disponible"
        else:
            horario_str = "Horario no disponible"
            
        horarios_procesados.append({
            'id': clase_id,
            'nombre': nombre_clase,
            'horario': horario_str,
            'instructor': nombre_instructor,
            'realizada': realizada
        })
    
    for row in schedules_completed:
        clase_id = row[0]
        nombre_clase = row[1]
        hora_inicio_str = row[2]
        duracion_clase = row[3]
        nombre_instructor = row[4] if row[4] else "No asignado"
        realizada = True  # Ya fue realizada

        # Manejo adecuado cuando hora_inicio es None o inválido
        if hora_inicio_str:
            try:
                hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M:%S').time() if hora_inicio_str else None
                hora_inicio_str = hora_inicio_str.split(':')[0] + ':' + hora_inicio_str.split(':')[1] if hora_inicio else "N/A"
                hora_fin_str = calcular_hora_fin(hora_inicio_str, duracion_clase)
                horario_str = f"{hora_inicio_str} - {hora_fin_str}" if hora_inicio_str != "N/A" else "Horario no disponible"
            except (ValueError, IndexError):
                horario_str = "Horario no disponible"
        else:
            horario_str = "Horario no disponible"
            
        horarios_procesados.append({
            'id': clase_id,
            'nombre': nombre_clase,
            'horario': horario_str,
            'instructor': nombre_instructor,
            'realizada': realizada
        })
    
    return render_template('reporte_mensual.html', 
                          mes=mes, 
                          anio=anio, 
                          nombre_mes=MESES_ES[mes],
                          horarios=horarios_procesados)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

@app.template_filter('format_hora')
def format_hora(hora):
    """Convierte cualquier formato de hora a HH:MM"""
    if not hora:
        return "N/A"
    
    # Si es objeto time, formatear directamente
    if isinstance(hora, time):
        return hora.strftime('%H:%M')
    
    # Si es string, extraer solo HH:MM
    if isinstance(hora, str) and ':' in hora:
        partes = hora.split(':')
        if len(partes) >= 2:
            try:
                return f"{int(partes[0]):02d}:{int(partes[1]):02d}"
            except ValueError:
                pass
    
    # Si todo falla, devolver el valor original
    return hora

def convertir_hora_con_microsegundos(valor_hora):
    """
    Convierte una hora en formato string a objeto time, manejando varios formatos incluyendo los que tienen microsegundos.
    
    Args:
        valor_hora: El valor de hora a convertir (string o time)
        
    Returns:
        Objeto time o None si no se puede convertir
    """
    if valor_hora is None:
        return None
        
    # Si ya es un objeto time, devolverlo directamente
    if isinstance(valor_hora, time):
        return valor_hora
        
    # Si es string, intentar convertir
    if isinstance(valor_hora, str):
        # Eliminar parte de microsegundos si existe
        if '.' in valor_hora:
            valor_hora = valor_hora.split('.')[0]
            
        # Intentar varios formatos
        for formato in ['%H:%M:%S', '%H:%M']:
            try:
                return datetime.strptime(valor_hora, formato).time()
            except ValueError:
                continue
                
    # Si todas las conversiones fallan
    # Registrar en el log pero no imprimir en consola
    app.logger.error(f"No se pudo convertir {valor_hora} a objeto time")
    return None

@app.route('/informes/profesor/<int:profesor_id>/metricas')
def metricas_profesor(profesor_id):
    """Mostrar métricas detalladas de un profesor específico"""
    try:
        # Diccionario de nombres de meses en español
        MESES_ES = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        # Obtener datos del profesor
        profesor = Profesor.query.get_or_404(profesor_id)
        
        # Manejar bases de datos que pueden no tener la columna fecha_desactivacion en HorarioClase
        try:
            # Verificar si podemos acceder a HorarioClase con todas las columnas
            HorarioClase.query.filter_by(id=1).first()
        except Exception as db_error:
            # Si hay un error relacionado con columnas faltantes, ejecutar update_db.py
            app.logger.error(f"Error al acceder a HorarioClase: {str(db_error)}")
            if "no such column" in str(db_error).lower():
                flash(f"Actualizando esquema de base de datos: {str(db_error)}", "warning")
                import subprocess
                try:
                    subprocess.run(["python", "update_db.py"], check=True)
                    flash("Base de datos actualizada correctamente", "success")
                except subprocess.CalledProcessError:
                    flash("Error al actualizar la base de datos", "danger")
        
        # Verificar si se debe mostrar el modo de depuración
        debug_mode = request.args.get('debug', type=bool, default=False)
        
        # Obtener parámetros de filtro opcional
        tipo_clase = request.args.get('tipo_clase', default=None)
        
        # Obtener todas las clases del profesor
        clases = profesor.obtener_todas_clases()
        
        # Obtener datos de meses disponibles para los selectores
        meses_disponibles = obtener_meses_disponibles(clases)
        
        # Variables comunes
        mes_actual = None
        mes_comparacion = None
        mes_actual_nombre = "Sin selección"
        mes_comparacion_nombre = "Sin selección"
        error = None
        
        # Verificar si estamos en modo comparación
        if 'comparar' in request.args:
            # --- MODO COMPARACIÓN ENTRE MESES ---
            mes_actual_str = request.args.get('mes_actual', default=None)
            mes_comparacion_str = request.args.get('mes_comparacion', default=None)
            
            # Procesar primer mes (mes actual)
            if mes_actual_str:
                try:
                    anio, mes = mes_actual_str.split('-')
                    mes_actual = (int(anio), int(mes))
                    mes_actual_nombre = f"{MESES_ES[int(mes)]} {anio}"
                except (ValueError, TypeError):
                    flash(f"Formato del primer mes inválido. Use YYYY-MM", "warning")
            
            # Procesar segundo mes (mes de comparación)
            if mes_comparacion_str:
                try:
                    anio, mes = mes_comparacion_str.split('-')
                    mes_comparacion = (int(anio), int(mes))
                    mes_comparacion_nombre = f"{MESES_ES[int(mes)]} {anio}"
                except (ValueError, TypeError):
                    flash(f"Formato del segundo mes inválido. Use YYYY-MM", "warning")
            
            # Validar selección de ambos meses
            if not mes_actual or not mes_comparacion:
                error = "Debe seleccionar dos meses diferentes para realizar la comparación."
                metricas = {}
            elif mes_actual == mes_comparacion:
                error = "Los meses seleccionados para comparar deben ser diferentes."
                metricas = {}
            else:
                # Calcular métricas con comparación
                from utils.metricas_profesores import calcular_metricas_profesor
                
                # Obtener el tipo de métricas seleccionado (mensual o totales)
                tipo_metricas_original = request.args.get('tipo_metricas', default='mensual')
                
                # Siempre usar los meses específicos en modo comparación, incluso en métricas totales
                metricas = calcular_metricas_profesor(
                    profesor_id=profesor.id,
                    clases=clases,
                    mes_actual=mes_actual,
                    mes_comparacion=mes_comparacion
                )
                
                # Manejar errores de validación
                if 'error_comparacion' in metricas:
                    error = metricas['error_comparacion']
                    if 'comparacion' in metricas:
                        del metricas['comparacion']
            
            # En modo comparación, respetamos el tipo de vista seleccionado
            # (mensual o totales) para mantener la consistencia visual
            tipo_metricas = tipo_metricas_original
            
        else:
            # --- MODO VISUALIZACIÓN NORMAL ---
            tipo_metricas = request.args.get('tipo_metricas', default='mensual')
            mes_actual_str = request.args.get('mes_actual', default=None)
            
            # Procesar parámetros de mes solo si es tipo mensual
            if tipo_metricas == 'mensual' and mes_actual_str:
                try:
                    anio, mes = mes_actual_str.split('-')
                    mes_actual = (int(anio), int(mes))
                    mes_actual_nombre = f"{MESES_ES[int(mes)]} {anio}"
                except (ValueError, TypeError):
                    flash(f"Formato de mes inválido. Use YYYY-MM", "warning")
                    # Si hay un error, mostramos las métricas totales
                    tipo_metricas = 'totales'
            
            # Para métricas totales, mostrar mensaje apropiado
            if tipo_metricas == 'totales':
                mes_actual = None
                mes_actual_nombre = "Todas las clases"
            elif tipo_metricas == 'mensual' and not mes_actual:
                # Si no se seleccionó un mes pero estamos en vista mensual y hay meses disponibles,
                # seleccionamos el mes más reciente por defecto
                if meses_disponibles:
                    mes_mas_reciente = meses_disponibles[0]  # El primer elemento es el más reciente
                    mes_actual = (mes_mas_reciente['anio'], mes_mas_reciente['mes'])
                    mes_actual_nombre = mes_mas_reciente['etiqueta']
            
            # Calcular métricas según el tipo seleccionado
            from utils.metricas_profesores import calcular_metricas_profesor
            metricas = calcular_metricas_profesor(
                profesor_id=profesor.id,
                clases=clases,
                mes_actual=mes_actual,
                mes_comparacion=None  # No hay comparación en este modo
            )
        
        # Obtener tipos de clase para filtros en la UI
        tipos_clase = HorarioClase.obtener_tipos_clase()
        
        # Obtener ranking de profesores para comparativas si no está presente
        if 'ranking_profesores' not in metricas.get('metricas_actual', {}) or not metricas.get('metricas_actual', {}).get('ranking_profesores'):
            if 'metricas_actual' in metricas:
                metricas['metricas_actual']['ranking_profesores'] = Profesor.obtener_ranking_profesores()
            else:
                metricas['ranking_profesores'] = Profesor.obtener_ranking_profesores()
        
        return render_template(
            'informes/metricas_profesor.html', 
            profesor=profesor, 
            metricas=metricas if 'metricas_actual' not in metricas else metricas['metricas_actual'],
            metricas_comparacion=metricas.get('metricas_comparacion'),
            comparacion=metricas.get('comparacion'),
            tipos_clase=tipos_clase,
            tipo_clase_actual=tipo_clase or 'Todos',
            debug_mode=debug_mode,
            mes_actual=mes_actual,
            mes_comparacion=mes_comparacion,
            meses_disponibles=meses_disponibles,
            mes_actual_nombre=mes_actual_nombre,
            mes_comparacion_nombre=mes_comparacion_nombre,
            tipo_metricas=tipo_metricas,  # Tipo de métricas seleccionado
            comparar_meses='comparar' in request.args,  # Indicar si estamos en modo comparación
            error=error  # Pasar el error de validación a la plantilla
        )
    except Exception as e:
        app.logger.error(f"Error en metricas_profesor: {str(e)}")
        flash(f"Error al cargar métricas del profesor: {str(e)}", "danger")
        return redirect(url_for('informe_mensual'))


def obtener_meses_disponibles(clases):
    """
    Obtiene una lista de meses disponibles para los que hay datos.
    
    Args:
        clases (list): Lista de objetos ClaseRealizada
        
    Returns:
        list: Lista de diccionarios con años y meses disponibles
    """
    # Diccionario de nombres de meses en español
    MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    if not clases:
        return []
    
    # Agrupar por mes
    meses = {}
    for clase in clases:
        clave = f"{clase.fecha.year}-{clase.fecha.month:02d}"
        if clave not in meses:
            meses[clave] = {
                'valor': clave,
                'etiqueta': f"{MESES_ES[clase.fecha.month]} {clase.fecha.year}",
                'anio': clase.fecha.year,
                'mes': clase.fecha.month
            }
    
    # Ordenar por fecha (más reciente primero)
    return sorted(list(meses.values()), key=lambda x: f"{x['anio']}-{x['mes']:02d}", reverse=True)

@app.route('/mantenimiento/fix-dates')
def fix_problematic_dates():
    """
    Función de mantenimiento para corregir formatos de fecha problemáticos
    en la base de datos.
    """
    try:
        # Obtener conexión directa a SQLite
        import sqlite3
        conn = sqlite3.connect('gimnasio.db')
        cursor = conn.cursor()
        
        # Corregir la fecha problemática específica
        cursor.execute("""
            UPDATE evento_horario 
            SET fecha = '2025-05-16 08:18:35' 
            WHERE fecha = '2025-05-16T08:18:35.167165'
        """)
        
        problematic_record_fixes = cursor.rowcount
        
        # Corregir cualquier otro registro con formato 'T'
        cursor.execute("""
            SELECT id, fecha FROM evento_horario 
            WHERE fecha LIKE '%T%'
        """)
        
        t_format_records = cursor.fetchall()
        fixed_t_format = 0
        
        for record_id, date_str in t_format_records:
            # Convertir de formato ISO a formato estándar
            try:
                date_part, time_part = date_str.split('T')
                if '.' in time_part:
                    time_part = time_part.split('.')[0]
                    
                fixed_date = f"{date_part} {time_part}"
                
                cursor.execute(
                    "UPDATE evento_horario SET fecha = ? WHERE id = ?",
                    (fixed_date, record_id)
                )
                fixed_t_format += 1
            except Exception as e:
                app.logger.error(f"Error fixing date format for record {record_id}: {str(e)}")
        
        # Corregir cualquier registro con microsegundos (formato con punto)
        cursor.execute("""
            SELECT id, fecha FROM evento_horario 
            WHERE fecha LIKE '%.%'
        """)
        
        microsecond_records = cursor.fetchall()
        fixed_microseconds = 0
        
        for record_id, date_str in microsecond_records:
            # Eliminar los microsegundos
            try:
                if ' ' in date_str:  # Formato estándar con microsegundos
                    parts = date_str.split('.')
                    fixed_date = parts[0]  # Tomar solo la parte antes del punto
                    
                    cursor.execute(
                        "UPDATE evento_horario SET fecha = ? WHERE id = ?",
                        (fixed_date, record_id)
                    )
                    fixed_microseconds += 1
            except Exception as e:
                app.logger.error(f"Error fixing microsecond format for record {record_id}: {str(e)}")
        
        # Confirmar cambios
        conn.commit()
        
        # Verificar si aún quedan registros problemáticos
        cursor.execute("SELECT COUNT(*) FROM evento_horario WHERE fecha LIKE '%T%'")
        remaining_t = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM evento_horario WHERE fecha LIKE '%.%'")
        remaining_ms = cursor.fetchone()[0]
        
        conn.close()
        
        return render_template(
            'mantenimiento/resultado.html',
            titulo="Corrección de fechas",
            mensaje=f"Se corrigieron {problematic_record_fixes} registros con la fecha problemática específica, {fixed_t_format} registros con formato 'T' y {fixed_microseconds} registros con microsegundos. Quedan {remaining_t} registros con 'T' y {remaining_ms} con microsegundos.",
            detalles=f"La operación de mantenimiento ha finalizado exitosamente."
        )
        
    except Exception as e:
        app.logger.error(f"Error en fix_problematic_dates: {str(e)}")
        return render_template(
            'mantenimiento/resultado.html',
            titulo="Error en corrección de fechas",
            mensaje=f"Ocurrió un error: {str(e)}",
            detalles=f"No se pudieron corregir las fechas problemáticas."
        )