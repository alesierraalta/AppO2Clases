from flask import Blueprint, request, jsonify
import os
import base64
from werkzeug.utils import secure_filename
from models import Profesor, HorarioClase, ClaseRealizada, clear_metrics_cache
from datetime import datetime, timedelta
import logging
import calendar

# Crear un Blueprint para organizar mejor las rutas
api = Blueprint('api', __name__, url_prefix='/api')

# Configurar la carpeta de subidas
UPLOAD_FOLDER = 'static/uploads/audio'
# Asegurarse de que el directorio existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurar logger
logger = logging.getLogger(__name__)

@api.route('/upload_audio/<int:user_id>', methods=['POST'])
def upload_audio(user_id):
    # Agregar log para depuración
    print(f"Headers: {request.headers}")
    print(f"Files: {request.files}")
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file found'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if audio_file:
        filename = secure_filename(audio_file.filename)
        upload_method = request.form.get('upload_method', 'default')
        
        # Puedes personalizar el nombre del archivo para evitar colisiones
        save_path = os.path.join(UPLOAD_FOLDER, f'user_{user_id}_{filename}')
        
        try:
            audio_file.save(save_path)
            # Ruta relativa para acceder desde el navegador
            relative_path = f'/static/uploads/audio/user_{user_id}_{filename}'
            return jsonify({
                'message': f'File uploaded successfully as {filename}',
                'file_path': relative_path,
                'upload_method': upload_method
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

@api.route('/upload_audio_base64/<int:user_id>', methods=['POST'])
def upload_audio_base64(user_id):
    data = request.json
    
    if not data or 'audio_data' not in data:
        return jsonify({'error': 'No se proporcionaron datos de audio'}), 400
    
    try:
        # Decodificar datos Base64
        audio_data = base64.b64decode(data['audio_data'])
        
        # Obtener nombre de archivo y tipo MIME
        filename = secure_filename(data.get('filename', f'audio_{user_id}.mp3'))
        
        # Guardar archivo
        save_path = os.path.join(UPLOAD_FOLDER, f'user_{user_id}_{filename}')
        
        with open(save_path, 'wb') as f:
            f.write(audio_data)
        
        # Ruta relativa para acceder desde el navegador
        relative_path = f'/static/uploads/audio/user_{user_id}_{filename}'
        return jsonify({
            'message': 'Archivo subido correctamente en formato Base64',
            'file_path': relative_path
        })
    
    except Exception as e:
        return jsonify({'error': f'Error al procesar archivo Base64: {str(e)}'}), 500 

@api.route('/profesores', methods=['GET'])
def get_profesores():
    """Retorna la lista de todos los profesores."""
    try:
        profesores = Profesor.query.all()
        result = [{
            'id': p.id,
            'nombre': p.nombre,
            'apellido': p.apellido,
            'email': p.email,
            'telefono': p.telefono
        } for p in profesores]
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        logger.error(f"Error en get_profesores: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/profesores/<int:profesor_id>', methods=['GET'])
def get_profesor(profesor_id):
    """Retorna los datos de un profesor específico."""
    try:
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            return jsonify({'status': 'error', 'message': 'Profesor no encontrado'}), 404
            
        result = {
            'id': profesor.id,
            'nombre': profesor.nombre,
            'apellido': profesor.apellido,
            'email': profesor.email,
            'telefono': profesor.telefono
        }
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        logger.error(f"Error en get_profesor: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/profesores/<int:profesor_id>/clases', methods=['GET'])
def get_clases_profesor(profesor_id):
    """Retorna las clases realizadas por un profesor en un período específico."""
    try:
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            return jsonify({'status': 'error', 'message': 'Profesor no encontrado'}), 404
        
        # Obtener parámetros de filtro
        periodo = request.args.get('periodo', type=int, default=30)  # días
        fecha_fin_str = request.args.get('fecha_fin', default=None)
        tipo_clase = request.args.get('tipo_clase', default=None)
        
        # Convertir fecha_fin si se proporciona
        fecha_fin = None
        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        # Obtener clases del período
        clases = profesor.get_clases_periodo(
            fecha_inicio=(fecha_fin or datetime.now().date()) - timedelta(days=periodo),
            fecha_fin=fecha_fin,
            tipo_clase=tipo_clase
        )
        
        # Formatear resultados
        result = [{
            'id': c.id,
            'fecha': c.fecha.strftime('%Y-%m-%d'),
            'hora_inicio': c.horario.hora_inicio.strftime('%H:%M') if c.horario and c.horario.hora_inicio else None,
            'hora_llegada': c.hora_llegada_profesor.strftime('%H:%M') if c.hora_llegada_profesor else None,
            'tipo_clase': c.horario.tipo_clase if c.horario else 'OTRO',
            'nombre_clase': c.horario.nombre if c.horario else 'N/A',
            'cantidad_alumnos': c.cantidad_alumnos,
            'puntualidad': c.puntualidad,
            'minutos_diferencia': c.minutos_diferencia
        } for c in clases]
        
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        logger.error(f"Error en get_clases_profesor: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/profesores/<int:profesor_id>/metricas', methods=['GET'])
def get_metricas_profesor(profesor_id):
    """Retorna las métricas detalladas de un profesor."""
    try:
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            return jsonify({'status': 'error', 'message': 'Profesor no encontrado'}), 404
        
        # Obtener parámetros de filtro
        periodo_meses = request.args.get('periodo', type=int, default=12)
        fecha_fin_str = request.args.get('fecha_fin', default=None)
        force_recalculate = request.args.get('force_recalculate', type=bool, default=False)
        
        # Nuevos parámetros para comparación mensual
        mes_actual_str = request.args.get('mes_actual', default=None)  # formato: YYYY-MM
        mes_comparacion_str = request.args.get('mes_comparacion', default=None)  # formato: YYYY-MM
        
        # Convertir fecha_fin si se proporciona
        fecha_fin = None
        if fecha_fin_str:
            try:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'status': 'error', 'message': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400
        
        # Convertir parámetros de mes si se proporcionan
        mes_actual = None
        mes_comparacion = None
        
        if mes_actual_str:
            try:
                anio, mes = mes_actual_str.split('-')
                mes_actual = (int(anio), int(mes))
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': 'Formato de mes_actual inválido. Use YYYY-MM'}), 400
        
        if mes_comparacion_str:
            try:
                anio, mes = mes_comparacion_str.split('-')
                mes_comparacion = (int(anio), int(mes))
            except (ValueError, TypeError):
                return jsonify({'status': 'error', 'message': 'Formato de mes_comparacion inválido. Use YYYY-MM'}), 400
        
        # Calcular métricas
        from utils.metricas_profesores import calcular_metricas_profesor
        
        # Obtener todas las clases del profesor
        clases = profesor.obtener_todas_clases()
        
        metricas = calcular_metricas_profesor(
            profesor_id=profesor.id,
            clases=clases,
            mes_actual=mes_actual,
            mes_comparacion=mes_comparacion
        )
        
        # Manejar caso de error o validación
        if 'error' in metricas or 'error_comparacion' in metricas:
            error_message = metricas.get('error', metricas.get('error_comparacion', 'No hay datos suficientes'))
            return jsonify({
                'status': 'warning', 
                'message': error_message,
                'data': {
                    'mes_actual': mes_actual,
                    'mes_comparacion': mes_comparacion,
                    'metricas': metricas
                }
            }), 200
            
        # Eliminar el campo 'clases' para reducir el tamaño de la respuesta
        if 'metricas_actual' in metricas and 'clases' in metricas['metricas_actual']:
            del metricas['metricas_actual']['clases']
        
        if 'metricas_comparacion' in metricas and metricas['metricas_comparacion'] and 'clases' in metricas['metricas_comparacion']:
            del metricas['metricas_comparacion']['clases']
        
        return jsonify({'status': 'success', 'data': metricas}), 200
    except Exception as e:
        logger.error(f"Error en get_metricas_profesor: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/profesores/ranking', methods=['GET'])
def get_ranking_profesores():
    """Retorna el ranking de profesores según un tipo de métrica específico."""
    try:
        # Obtener parámetros
        tipo_metrica = request.args.get('tipo', default='puntualidad')
        limite = request.args.get('limite', type=int, default=10)
        
        # Validar tipo de métrica
        tipos_validos = ['puntualidad', 'alumnos', 'clases']
        if tipo_metrica not in tipos_validos:
            return jsonify({'status': 'error', 'message': f'Tipo de métrica inválido. Use uno de: {tipos_validos}'}), 400
        
        # Obtener ranking
        ranking = Profesor.obtener_ranking_profesores(tipo_metrica=tipo_metrica, limite=limite)
        
        return jsonify({'status': 'success', 'data': ranking}), 200
    except Exception as e:
        logger.error(f"Error en get_ranking_profesores: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/estadisticas/tipos_clase', methods=['GET'])
def get_estadisticas_tipos_clase():
    """Retorna estadísticas agregadas por tipo de clase."""
    try:
        # Obtener estadísticas
        estadisticas = HorarioClase.estadisticas_por_tipo()
        
        return jsonify({'status': 'success', 'data': estadisticas}), 200
    except Exception as e:
        logger.error(f"Error en get_estadisticas_tipos_clase: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/estadisticas/historicas', methods=['GET'])
def get_estadisticas_historicas():
    """Retorna estadísticas históricas mensualmente."""
    try:
        # Obtener parámetros
        profesor_id = request.args.get('profesor_id', type=int, default=None)
        tipo_clase = request.args.get('tipo_clase', default=None)
        periodo_meses = request.args.get('periodo', type=int, default=12)
        
        # Obtener estadísticas
        estadisticas = ClaseRealizada.obtener_estadisticas_historicas(
            profesor_id=profesor_id,
            tipo_clase=tipo_clase,
            periodo_meses=periodo_meses
        )
        
        return jsonify({'status': 'success', 'data': estadisticas}), 200
    except Exception as e:
        logger.error(f"Error en get_estadisticas_historicas: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/cache/metricas/clear', methods=['POST'])
def clear_cache_metricas():
    """Limpia la caché de métricas."""
    try:
        # Obtener parámetros
        profesor_id = request.json.get('profesor_id', None) if request.json else None
        
        # Limpiar caché
        clear_metrics_cache(profesor_id)
        
        return jsonify({
            'status': 'success', 
            'message': f"Caché {'del profesor {profesor_id}' if profesor_id else 'global'} limpiada correctamente"
        }), 200
    except Exception as e:
        logger.error(f"Error en clear_cache_metricas: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@api.route('/profesores/<int:profesor_id>/meses_disponibles', methods=['GET'])
def get_meses_disponibles_profesor(profesor_id):
    """Retorna la lista de meses para los que hay datos de clases para un profesor."""
    try:
        # Diccionario de nombres de meses en español
        MESES_ES = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            return jsonify({'status': 'error', 'message': 'Profesor no encontrado'}), 404
        
        # Obtener todas las clases del profesor
        clases = profesor.obtener_todas_clases()
        
        # Agrupar por mes
        meses = {}
        for clase in clases:
            clave = f"{clase.fecha.year}-{clase.fecha.month:02d}"
            if clave not in meses:
                meses[clave] = {
                    'valor': clave,  # Formato ISO YYYY-MM
                    'etiqueta': f"{MESES_ES[clase.fecha.month]} {clase.fecha.year}",
                    'anio': clase.fecha.year,
                    'mes': clase.fecha.month
                }
        
        # Ordenar por fecha (más reciente primero)
        meses_ordenados = sorted(list(meses.values()), key=lambda x: f"{x['anio']}-{x['mes']:02d}", reverse=True)
        
        return jsonify({
            'status': 'success', 
            'data': meses_ordenados
        }), 200
    except Exception as e:
        logger.error(f"Error en get_meses_disponibles_profesor: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500 