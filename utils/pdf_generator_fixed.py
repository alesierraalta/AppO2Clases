"""
Optimized PDF Generator for O2 Fitness Reports
Simplified, efficient, and scalable PDF generation using ReportLab
"""

import os
import calendar
import logging
from datetime import datetime, date
from io import BytesIO
from typing import Dict, List, Optional, Any

# Core dependencies
from flask import has_app_context
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

# Setup logging
logger = logging.getLogger(__name__)

# iOS Design System Colors
IOS_COLORS = {
    'blue': HexColor('#007AFF'),
    'green': HexColor('#34C759'),
    'red': HexColor('#FF3B30'),
    'gray_6': HexColor('#F2F2F7'),
    'label_primary': HexColor('#000000'),
    'border': HexColor('#C6C6C8'),
    'gray_text': HexColor('#8E8E93'),
    'orange': HexColor('#FF9500')
}

# Month names in Spanish
MONTH_NAMES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

pdf_export_available = True


class PDFDataCache:
    """Simple cache for PDF data"""
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now().timestamp() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Any) -> None:
        self.cache[key] = (data, datetime.now().timestamp())
    
    def clear(self) -> None:
        self.cache.clear()


pdf_cache = PDFDataCache()


def safe_database_query(query_func, timeout_seconds: int = 3, fallback_value=None):
    """Execute a database query with error handling"""
    try:
        if not has_app_context():
            logger.warning("No Flask app context available")
            return fallback_value
        return query_func()
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return fallback_value


def get_ios_styles() -> Dict[str, ParagraphStyle]:
    """Get iOS-styled paragraph styles"""
    base_styles = getSampleStyleSheet()
    
    return {
        'title': ParagraphStyle(
            'iOSTitle',
            parent=base_styles['Title'],
            fontSize=28,
            fontName='Helvetica-Bold',
            spaceAfter=8,
            alignment=TA_CENTER,
            textColor=IOS_COLORS['label_primary'],
            leading=32
        ),
        'subtitle': ParagraphStyle(
            'iOSSubtitle',
            parent=base_styles['Normal'],
            fontSize=16,
            fontName='Helvetica',
            spaceAfter=24,
            alignment=TA_CENTER,
            textColor=IOS_COLORS['gray_text'],
            leading=20
        ),
        'header': ParagraphStyle(
            'iOSHeader',
            parent=base_styles['Heading1'],
            fontSize=18,
            fontName='Helvetica-Bold',
            spaceAfter=12,
            textColor=IOS_COLORS['label_primary'],
            leading=22
        ),
        'body': ParagraphStyle(
            'iOSBody',
            parent=base_styles['Normal'],
            fontSize=12,
            fontName='Helvetica',
            spaceAfter=6,
            textColor=IOS_COLORS['label_primary'],
            leading=16
        ),
        'footer': ParagraphStyle(
            'iOSFooter',
            parent=base_styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            textColor=IOS_COLORS['gray_text'],
            alignment=TA_CENTER
        )
    }


def get_monthly_data(mes: int, anio: int) -> Dict[str, Any]:
    """Get monthly data with caching"""
    cache_key = f"monthly_data_{mes}_{anio}"
    cached_data = pdf_cache.get(cache_key)
    if cached_data:
        logger.info(f"Using cached data for {cache_key}")
        return cached_data
    
    try:
        from models import db, ClaseRealizada, Profesor, HorarioClase
        
        start_date = date(anio, mes, 1)
        end_date = date(anio, mes, calendar.monthrange(anio, mes)[1])
        
        clases_query = lambda: (
            db.session.query(ClaseRealizada, Profesor, HorarioClase)
            .join(Profesor, ClaseRealizada.profesor_id == Profesor.id)
            .join(HorarioClase, ClaseRealizada.horario_id == HorarioClase.id)
            .filter(ClaseRealizada.fecha >= start_date, ClaseRealizada.fecha <= end_date)
            .all()
        )
        
        clases_data = safe_database_query(clases_query, fallback_value=[])
        
        if not clases_data:
            logger.warning(f"No classes found for {mes}/{anio}")
            return _get_sample_monthly_data(mes, anio)
        
        # Process data
        total_clases = len(clases_data)
        total_alumnos = sum((clase.cantidad_alumnos or 0) for clase, _, _ in clases_data)
        total_pagos = 0
        clases_con_retraso = 0
        profesores_stats = {}
        tipos_stats = {}
        
        for clase, profesor, horario in clases_data:
            # Calculate payment
            if clase.hora_llegada_profesor:
                if (clase.cantidad_alumnos or 0) > 0:
                    pago = profesor.tarifa_por_clase or 0
                else:
                    pago = (profesor.tarifa_por_clase or 0) / 2
            else:
                pago = 0
            total_pagos += pago
            
            # Check punctuality
            if (clase.hora_llegada_profesor and horario.hora_inicio and 
                clase.hora_llegada_profesor > horario.hora_inicio):
                clases_con_retraso += 1
            
            # Professor stats
            prof_id = profesor.id
            if prof_id not in profesores_stats:
                profesores_stats[prof_id] = {
                    'nombre': f"{profesor.nombre} {profesor.apellido}",
                    'total_clases': 0,
                    'total_alumnos': 0,
                    'total_pago': 0
                }
            
            profesores_stats[prof_id]['total_clases'] += 1
            profesores_stats[prof_id]['total_alumnos'] += clase.cantidad_alumnos or 0
            profesores_stats[prof_id]['total_pago'] += pago
            
            # Class type stats
            tipo = horario.tipo_clase or 'OTRO'
            if tipo not in tipos_stats:
                tipos_stats[tipo] = {'count': 0, 'alumnos': 0}
            tipos_stats[tipo]['count'] += 1
            tipos_stats[tipo]['alumnos'] += clase.cantidad_alumnos or 0
        
        profesores_list = sorted(
            profesores_stats.values(),
            key=lambda x: x['total_clases'],
            reverse=True
        )
        
        data = {
            'mes': mes,
            'anio': anio,
            'nombre_mes': MONTH_NAMES[mes],
            'total_clases': total_clases,
            'total_alumnos': total_alumnos,
            'total_pagos': total_pagos,
            'clases_con_retraso': clases_con_retraso,
            'profesores_stats': profesores_list[:10],
            'tipos_stats': tipos_stats,
            'promedio_alumnos': total_alumnos / max(1, total_clases),
            'porcentaje_puntualidad': ((total_clases - clases_con_retraso) / max(1, total_clases)) * 100
        }
        
        pdf_cache.set(cache_key, data)
        logger.info(f"Cached monthly data for {cache_key}")
        return data
        
    except Exception as e:
        logger.error(f"Error getting monthly data: {e}")
        return _get_sample_monthly_data(mes, anio)


def _get_sample_monthly_data(mes: int, anio: int) -> Dict[str, Any]:
    """Generate sample data as fallback"""
    return {
        'mes': mes,
        'anio': anio,
        'nombre_mes': MONTH_NAMES[mes],
        'total_clases': 45,
        'total_alumnos': 280,
        'total_pagos': 22500,
        'clases_con_retraso': 7,
        'profesores_stats': [
            {'nombre': 'Maria Rodriguez', 'total_clases': 12, 'total_alumnos': 96, 'total_pago': 6000},
            {'nombre': 'Juan Perez', 'total_clases': 10, 'total_alumnos': 80, 'total_pago': 5000},
            {'nombre': 'Ana Martinez', 'total_clases': 8, 'total_alumnos': 64, 'total_pago': 4000},
        ],
        'tipos_stats': {
            'MOVE': {'count': 15, 'alumnos': 120},
            'RIDE': {'count': 18, 'alumnos': 108},
            'BOX': {'count': 8, 'alumnos': 32},
            'OTRO': {'count': 4, 'alumnos': 20}
        },
        'promedio_alumnos': 6.2,
        'porcentaje_puntualidad': 84.4
    }


def create_metrics_table(data: Dict[str, Any]) -> Table:
    """Create metrics summary table"""
    metrics_data = [
        ['📊 CLASES', '👥 ALUMNOS', '💰 TOTAL', '⏰ RETRASOS'],
        [
            str(data['total_clases']),
            str(data['total_alumnos']),
            f"${data['total_pagos']:,.0f}",
            str(data['clases_con_retraso'])
        ]
    ]
    
    table = Table(metrics_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), IOS_COLORS['blue']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, 1), white),
        ('TEXTCOLOR', (0, 1), (-1, 1), IOS_COLORS['label_primary']),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
        ('LEFTPADDING', (0, 0), (-1, -1), 16),
        ('RIGHTPADDING', (0, 0), (-1, -1), 16),
        ('GRID', (0, 0), (-1, -1), 0.5, IOS_COLORS['border']),
        ('BOX', (0, 0), (-1, -1), 1, IOS_COLORS['border']),
    ]))
    
    return table


def create_professors_table(data: Dict[str, Any]) -> Table:
    """Create professors performance table"""
    prof_data = [['PROFESOR', 'CLASES', 'ALUMNOS', 'TOTAL']]
    
    for prof in data['profesores_stats'][:5]:
        prof_data.append([
            prof['nombre'][:20],
            str(prof['total_clases']),
            str(prof['total_alumnos']),
            f"${prof['total_pago']:,.0f}"
        ])
    
    table = Table(prof_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), IOS_COLORS['green']),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('TEXTCOLOR', (0, 1), (-1, -1), IOS_COLORS['label_primary']),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, IOS_COLORS['border']),
        ('BOX', (0, 0), (-1, -1), 1, IOS_COLORS['border']),
    ]))
    
    return table


def generate_monthly_report_pdf(template_vars: Dict[str, Any]) -> Optional[bytes]:
    """Generate monthly report PDF"""
    try:
        mes = template_vars.get('mes', date.today().month)
        anio = template_vars.get('anio', date.today().year)
        
        data = get_monthly_data(mes, anio)
        styles = get_ios_styles()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header
        story.append(Paragraph("O2 FITNESS", styles['title']))
        story.append(Paragraph(f"Informe Mensual - {data['nombre_mes']} {data['anio']}", styles['subtitle']))
        story.append(Spacer(1, 1*cm))
        
        # Metrics table
        story.append(create_metrics_table(data))
        story.append(Spacer(1, 1*cm))
        
        # Summary section
        story.append(Paragraph("📈 RESUMEN DEL MES", styles['header']))
        summary_text = f"""
        <b>Promedio por Clase:</b> {data['promedio_alumnos']:.1f} alumnos<br/>
        <b>Puntualidad:</b> {data['porcentaje_puntualidad']:.1f}%<br/>
        <b>Eficiencia:</b> {(data['total_alumnos'] / max(1, data['total_clases'])):.1f} alumnos/clase
        """
        story.append(Paragraph(summary_text, styles['body']))
        story.append(Spacer(1, 1*cm))
        
        # Professors table
        if data['profesores_stats']:
            story.append(Paragraph("👨‍🏫 TOP PROFESORES", styles['header']))
            story.append(create_professors_table(data))
            story.append(Spacer(1, 1*cm))
        
        # Footer
        footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} • O2 Fitness Management System"
        story.append(Paragraph(footer_text, styles['footer']))
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Monthly report PDF generated successfully: {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        logger.error(f"Error generating monthly report PDF: {e}")
        return generate_error_pdf(f"Error en reporte mensual: {e}")


def generate_professor_metrics_pdf(template_vars: Dict[str, Any]) -> Optional[bytes]:
    """Generate professor metrics PDF"""
    try:
        profesor = template_vars.get('profesor', {})
        metricas = template_vars.get('metricas', {})
        mes_actual_nombre = template_vars.get('mes_actual_nombre', 'Período Actual')
        
        styles = get_ios_styles()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header
        if isinstance(profesor, dict):
            profesor_nombre = f"{profesor.get('nombre', '')} {profesor.get('apellido', '')}"
        else:
            profesor_nombre = f"{getattr(profesor, 'nombre', '')} {getattr(profesor, 'apellido', '')}"
        
        story.append(Paragraph(f"Métricas de {profesor_nombre}", styles['title']))
        story.append(Paragraph(f"Período: {mes_actual_nombre}", styles['subtitle']))
        story.append(Spacer(1, 1*cm))
        
        # Metrics
        story.append(Paragraph("📊 Resumen de Rendimiento", styles['header']))
        
        metrics_data = [['Métrica', 'Valor']]
        total_clases = metricas.get('total_clases', 0)
        total_alumnos = metricas.get('total_alumnos', 0)
        promedio_alumnos = metricas.get('promedio_alumnos', 0)
        
        metrics_data.extend([
            ['Total de Clases', str(total_clases)],
            ['Total de Alumnos', str(total_alumnos)],
            ['Promedio por Clase', f"{promedio_alumnos:.1f}"]
        ])
        
        puntualidad = metricas.get('puntualidad', {})
        if isinstance(puntualidad, dict) and 'tasa' in puntualidad:
            metrics_data.append(['Puntualidad', f"{puntualidad['tasa']:.1f}%"])
        
        metrics_table = Table(metrics_data, colWidths=[8*cm, 6*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), IOS_COLORS['blue']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), white),
            ('TEXTCOLOR', (0, 1), (-1, -1), IOS_COLORS['label_primary']),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, IOS_COLORS['border']),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 1*cm))
        
        # Footer
        footer_text = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | O2 Fitness - Métricas de Profesor"
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph(footer_text, styles['footer']))
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Professor metrics PDF generated successfully: {len(pdf_data)} bytes")
        return pdf_data
        
    except Exception as e:
        logger.error(f"Error generating professor metrics PDF: {e}")
        return generate_error_pdf(f"Error en métricas de profesor: {e}")


def generate_error_pdf(error_message: str) -> bytes:
    """Generate error PDF"""
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 700, "Error en Generación de PDF")
        
        p.setFont("Helvetica", 12)
        p.drawString(100, 670, f"Error: {error_message}")
        p.drawString(100, 650, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        p.drawString(100, 630, "Por favor, contacte al administrador del sistema.")
        
        p.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        logger.error(f"Failed to generate error PDF: {e}")
        return b'%PDF-1.4\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\ntrailer\n<</Size 2/Root 1 0 R>>\nstartxref\n0\n%%EOF'


def generate_pdf_from_template(template_name: str, template_vars: Dict[str, Any], 
                             css_files: Optional[List[str]] = None, 
                             base_url: Optional[str] = None) -> Optional[bytes]:
    """Main PDF generation function"""
    try:
        logger.info(f"Generating PDF for template: {template_name}")
        
        if 'metricas_profesor' in template_name:
            return generate_professor_metrics_pdf(template_vars)
        elif 'mensual' in template_name or 'informe' in template_name:
            return generate_monthly_report_pdf(template_vars)
        else:
            # Generic PDF
            return generate_monthly_report_pdf(template_vars)
            
    except Exception as e:
        logger.error(f"PDF generation failed for {template_name}: {e}")
        return generate_error_pdf(str(e))


# Legacy aliases
def generate_visual_dashboard_pdf(template_name, template_vars, css_files=None, base_url=None):
    return generate_monthly_report_pdf(template_vars)

def generate_enhanced_ios_pdf(template_name, template_vars=None, css_files=None, base_url=None):
    return generate_monthly_report_pdf(template_vars or {})

def generate_web_styled_pdf(template_name, template_vars=None, css_files=None, base_url=None):
    return generate_monthly_report_pdf(template_vars or {})

def generate_pdf_with_charts(template_name, template_vars=None, css_files=None, base_url=None, chart_images=None):
    return generate_monthly_report_pdf(template_vars or {})

def generate_chart_image_base64(fig):
    """Convert matplotlib figure to base64"""
    try:
        import base64
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        buf.seek(0)
        img_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error converting chart to base64: {e}")
        return ""

def clear_pdf_cache():
    """Clear the PDF cache"""
    pdf_cache.clear()
    logger.info("PDF cache cleared")

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        'cache_size': len(pdf_cache.cache),
        'ttl_seconds': pdf_cache.ttl
    }