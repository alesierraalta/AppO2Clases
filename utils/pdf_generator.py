import os

import calendar
from flask import render_template, url_for
from datetime import datetime, date
import io
from io import BytesIO
import signal
import threading
from contextlib import contextmanager
import sys

import subprocess
from pathlib import Path

# Try importing WeasyPrint but provide fallback
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    weasyprint_available = True
except (ImportError, OSError):
    weasyprint_available = False

# Alternative PDF generation with more compatibility
try:
    import pdfkit
    pdfkit_available = True
except ImportError:
    pdfkit_available = False

# ReportLab PDF generation (fallback)
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    reportlab_available = True
except ImportError:
    reportlab_available = False

# PDF export is available if ANY of the PDF libraries is available
pdf_export_available = weasyprint_available or pdfkit_available or reportlab_available

class PDFTimeoutError(Exception):
    """Custom timeout exception for PDF generation"""
    pass

@contextmanager
def timeout_context(seconds):
    """Context manager for implementing timeouts"""
    def timeout_handler(signum, frame):
        raise PDFTimeoutError(f"PDF generation timed out after {seconds} seconds")
    
    # Set up the timeout
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Clean up
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def safe_database_query(query_func, timeout_seconds=5, fallback_value=None):
    """
    Execute a database query with timeout protection
    """
    try:
        with timeout_context(timeout_seconds):
            return query_func()
    except (PDFTimeoutError, Exception) as e:
        print(f"Database query failed or timed out: {e}")
        return fallback_value

def generate_pdf_from_template(template_name, template_vars, css_files=None, base_url=None):
    """
    Generate a PDF from a Jinja2 HTML template
    
    Args:
        template_name (str): The name of the template to render
        template_vars (dict): Variables to pass to the template
        css_files (list): List of CSS file paths to include
        base_url (str): The base URL to resolve relative URLs
        
    Returns:
        bytes: The generated PDF as bytes
    """
    # Add PDF flag to template vars to enable PDF-specific styling
    template_vars['is_pdf'] = True
    
    # Add timestamp for PDF generation
    template_vars['pdf_generation_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log the attempt to generate a PDF
    print(f"Generating PDF for {template_name}")
    
    # For report templates, use specific PDF generators based on template type
    if 'metricas_profesor' in template_name:
        print(f"Using professor metrics PDF generator for {template_name}")
        try:
            return generate_professor_metrics_pdf(template_name, template_vars, css_files, base_url)
        except Exception as e:
            print(f"Professor metrics PDF generation failed, falling back to visual dashboard: {e}")
            return generate_visual_dashboard_pdf(template_name, template_vars, css_files, base_url)
    elif 'mensual' in template_name or 'informe' in template_name:
        print(f"Using monthly report PDF generator for {template_name}")
        try:
            return generate_web_styled_pdf(template_name, template_vars, css_files, base_url)
        except Exception as e:
            print(f"Monthly report PDF generation failed, falling back to visual dashboard: {e}")
            return generate_visual_dashboard_pdf(template_name, template_vars, css_files, base_url)
    
    # Render the HTML template
    html_content = render_template(template_name, **template_vars)
    
    # Try WeasyPrint first if available
    if weasyprint_available:
        try:
            html_doc = HTML(string=html_content, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()
            return pdf_bytes
        except Exception as e:
            print(f"WeasyPrint failed: {e}")
    
    # Try pdfkit as fallback
    if pdfkit_available:
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None
            }
            pdf_bytes = pdfkit.from_string(html_content, False, options=options)
            return pdf_bytes
        except Exception as e:
            print(f"pdfkit failed: {e}")
    
    # Final fallback - return None if no PDF generation method works
    print("No PDF generation method available")
    return None

def generate_pdf_with_charts(template_name, template_vars=None, css_files=None, base_url=None, chart_images=None):
    """
    Generate PDF with embedded chart images from Chart.js
    
    Args:
        template_name (str): The name of the template to render
        template_vars (dict): Variables to pass to the template
        css_files (list): List of CSS file paths to include
        base_url (str): The base URL to resolve relative URLs
        chart_images (dict): Dictionary of chart images in base64 format
        
    Returns:
        bytes: The generated PDF as bytes
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib.colors import HexColor, Color, white, black
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.graphics.shapes import Drawing, Rect, String
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.legends import Legend
        from reportlab.graphics import renderPDF
        from reportlab.platypus.flowables import Flowable
        import calendar
        from datetime import datetime, date
        from pathlib import Path
        import base64
        import io
        
        # Try to import PIL, fallback if not available
        try:
            from PIL import Image as PILImage
            pil_available = True
        except ImportError:
            pil_available = False
        
        # iOS Design System Colors
        IOS_BLUE = HexColor('#007AFF')
        IOS_GREEN = HexColor('#34C759')
        IOS_RED = HexColor('#FF3B30')
        IOS_GRAY_6 = HexColor('#F2F2F7')
        IOS_LABEL_PRIMARY = HexColor('#000000')
        IOS_BORDER = HexColor('#C6C6C8')
        IOS_GRAY_TEXT = HexColor('#8E8E93')
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=IOS_BLUE,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=IOS_LABEL_PRIMARY,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Title
        mes = template_vars.get('mes', 1)
        anio = template_vars.get('anio', 2024)
        nombre_mes = template_vars.get('nombre_mes', 'Enero')
        
        title = Paragraph(f"Informe Mensual con Gráficos: {nombre_mes} {anio}", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # KPIs Section
        kpi_subtitle = Paragraph("📊 Indicadores Clave de Rendimiento", subtitle_style)
        story.append(kpi_subtitle)
        
        # KPI Table
        total_clases = template_vars.get('total_clases', 0)
        total_alumnos = template_vars.get('total_alumnos', 0)
        total_pagos = template_vars.get('total_pagos', 0)
        avg_alumnos = round(total_alumnos / total_clases, 1) if total_clases > 0 else 0
        
        kpi_data = [
            ['📅 Total Clases', f'{total_clases}'],
            ['👥 Total Alumnos', f'{total_alumnos}'],
            ['💰 Total Pagos', f'${total_pagos:,.2f}'],
            ['📈 Promedio Alumnos/Clase', f'{avg_alumnos}']
        ]
        
        kpi_table = Table(kpi_data, colWidths=[8*cm, 4*cm])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), IOS_GRAY_6),
            ('TEXTCOLOR', (0, 0), (-1, -1), IOS_LABEL_PRIMARY),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, IOS_BORDER)
        ]))
        
        story.append(kpi_table)
        story.append(Spacer(1, 30))
        
        # Charts Section
        if chart_images and pil_available:
            chart_subtitle = Paragraph("📈 Análisis Visual Avanzado", subtitle_style)
            story.append(chart_subtitle)
            story.append(Spacer(1, 10))
            
            # Process and add charts
            chart_configs = [
                ('classDistributionChart', 'Distribución de Clases por Tipo'),
                ('studentParticipationChart', 'Participación de Alumnos por Tipo'),
                ('performanceComparisonChart', 'Comparación de Rendimiento'),
                ('averageStudentsChart', 'Promedio de Alumnos por Clase'),
                ('occupancyChart', 'Nivel de Ocupación')
            ]
            
            for chart_id, chart_title in chart_configs:
                if chart_id in chart_images:
                    try:
                        # Decode base64 image
                        image_data = chart_images[chart_id]
                        if image_data.startswith('data:image/png;base64,'):
                            image_data = image_data.split(',')[1]
                        
                        # Convert to PIL Image and then to ReportLab Image
                        image_bytes = base64.b64decode(image_data)
                        pil_image = PILImage.open(io.BytesIO(image_bytes))
                        
                        # Save to temporary buffer for ReportLab
                        temp_buffer = io.BytesIO()
                        pil_image.save(temp_buffer, format='PNG')
                        temp_buffer.seek(0)
                        
                        # Create ReportLab Image
                        chart_image = Image(temp_buffer, width=12*cm, height=8*cm)
                        
                        # Add chart title
                        chart_title_para = Paragraph(chart_title, ParagraphStyle(
                            'ChartTitle',
                            parent=styles['Normal'],
                            fontSize=12,
                            spaceAfter=10,
                            textColor=IOS_LABEL_PRIMARY,
                            alignment=TA_CENTER,
                            fontName='Helvetica-Bold'
                        ))
                        
                        story.append(chart_title_para)
                        story.append(chart_image)
                        story.append(Spacer(1, 20))
                        
                    except Exception as e:
                        print(f"Error processing chart {chart_id}: {e}")
                        # Add placeholder text if chart fails
                        error_para = Paragraph(f"[Gráfico: {chart_title} - Error al procesar]", styles['Normal'])
                        story.append(error_para)
                        story.append(Spacer(1, 10))
                        continue
        elif chart_images and not pil_available:
            # Add note about missing PIL
            note_para = Paragraph("Nota: Los gráficos no se pudieron incluir. PIL no está disponible.", 
                                ParagraphStyle('Note', parent=styles['Normal'], textColor=IOS_RED))
            story.append(note_para)
            story.append(Spacer(1, 20))
        
        # Data Analysis Section
        analysis_subtitle = Paragraph("📋 Análisis de Datos Detallado", subtitle_style)
        story.append(analysis_subtitle)
        
        # Type distribution
        conteo_tipos = template_vars.get('conteo_tipos', {})
        alumnos_tipos = template_vars.get('alumnos_tipos', {})
        
        if conteo_tipos:
            analysis_data = [['Tipo de Clase', 'Cantidad de Clases', 'Total Alumnos', 'Promedio por Clase']]
            
            for tipo in ['MOVE', 'RIDE', 'BOX', 'OTRO']:
                clases = conteo_tipos.get(tipo, 0)
                alumnos = alumnos_tipos.get(tipo, 0)
                promedio = round(alumnos / clases, 1) if clases > 0 else 0
                
                if clases > 0:  # Only show types with classes
                    analysis_data.append([tipo, str(clases), str(alumnos), str(promedio)])
            
            analysis_table = Table(analysis_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
            analysis_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), IOS_BLUE),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), IOS_GRAY_6),
                ('TEXTCOLOR', (0, 1), (-1, -1), IOS_LABEL_PRIMARY),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, IOS_BORDER),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(analysis_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} | O2 Fitness - Sistema de Gestión de Clases"
        footer = Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=IOS_GRAY_TEXT,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        import traceback
        print(f"Error generating PDF with charts: {e}")
        traceback.print_exc()
        return None

# Placeholder functions for compatibility
def generate_visual_dashboard_pdf(template_name, template_vars, css_files=None, base_url=None):
    """Fallback PDF generator"""
    return generate_pdf_from_template(template_name, template_vars, css_files, base_url)

def generate_professor_metrics_pdf(template_name, template_vars, css_files=None, base_url=None):
    """Professor metrics PDF generator"""
    return generate_pdf_from_template(template_name, template_vars, css_files, base_url)

def generate_web_styled_pdf(template_name, template_vars, css_files=None, base_url=None):
    """Web-styled PDF generator"""
    return generate_pdf_from_template(template_name, template_vars, css_files, base_url)