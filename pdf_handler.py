from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import pypdf

# Register system fonts for Windows
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Italic', 'ariali.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-BoldItalic', 'arialbi.ttf'))
    
    pdfmetrics.registerFont(TTFont('Calibri', 'calibri.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri-Bold', 'calibrib.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri-Italic', 'calibrii.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri-BoldItalic', 'calibriz.ttf'))
except Exception as e:
    print(f"Warning: Could not register some fonts: {e}")

class PDFHandler:
    @staticmethod
    def _get_font_name(base_font, is_bold, is_italic):
        font_name = base_font
        if base_font in ['Arial', 'Calibri', 'Helvetica']:
            suffix = ""
            if is_bold and is_italic:
                suffix = "-BoldItalic" if base_font != 'Helvetica' else "-BoldOblique"
            elif is_bold:
                suffix = "-Bold"
            elif is_italic:
                suffix = "-Italic" if base_font != 'Helvetica' else "-Oblique"
            font_name = f"{base_font}{suffix}"
        return font_name

    @staticmethod
    def _apply_text_settings(c, font_name, font_size, color):
        try:
            c.setFont(font_name, font_size)
        except KeyError:
            # Fallback to base font or Helvetica
            try:
                c.setFont(font_name.split('-')[0], font_size)
            except:
                c.setFont('Helvetica', font_size)
                
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16)/255.0 for i in (0, 2, 4))
        c.setFillColorRGB(*rgb)

    @staticmethod
    def _draw_text_box(c, text_value, text_config, img_h):
        if text_value is None or str(text_value).strip() == "":
            return
        x_min, y_min, x_max, y_max = text_config['box']
        base_font = text_config.get('font', 'Arial')
        font_size = text_config.get('size', 60)
        color = text_config.get('color', '#000000')
        alignment = text_config.get('align', 'center')
        is_bold = text_config.get('bold', False)
        is_italic = text_config.get('italic', False)
        
        font_name = PDFHandler._get_font_name(base_font, is_bold, is_italic)
        PDFHandler._apply_text_settings(c, font_name, font_size, color)
        
        box_center_y = y_min + (y_max - y_min) / 2
        pdf_y = img_h - box_center_y - (font_size / 3)
        box_w = x_max - x_min
        
        text_str = str(text_value)
        if alignment == 'center':
            c.drawCentredString(x_min + box_w / 2, pdf_y, text_str)
        elif alignment == 'right':
            c.drawRightString(x_max, pdf_y, text_str)
        else:
            c.drawString(x_min, pdf_y, text_str)

    @staticmethod
    def generate_certificate(template_path, name, text_config, output_path):
        with Image.open(template_path) as img:
            img_w, img_h = img.size
            
        c = canvas.Canvas(output_path, pagesize=(img_w, img_h))
        c.drawImage(template_path, 0, 0, width=img_w, height=img_h)
        PDFHandler._draw_text_box(c, name, text_config, img_h)
        c.save()

    @staticmethod
    def generate_certificate_multi(template_path, fields_values, text_configs, output_path):
        with Image.open(template_path) as img:
            img_w, img_h = img.size
            
        c = canvas.Canvas(output_path, pagesize=(img_w, img_h))
        c.drawImage(template_path, 0, 0, width=img_w, height=img_h)
        
        for text_val, cfg in zip(fields_values, text_configs):
            PDFHandler._draw_text_box(c, text_val, cfg, img_h)
            
        c.save()

    @staticmethod
    def generate_merged_certificates(template_path, names, text_config, output_path, progress_cb=None):
        """Generates a single PDF with all certificates. Very fast and produces tiny file size."""
        with Image.open(template_path) as img:
            img_w, img_h = img.size
            
        c = canvas.Canvas(output_path, pagesize=(img_w, img_h))
        total = len(names)
        for i, name in enumerate(names):
            c.drawImage(template_path, 0, 0, width=img_w, height=img_h)
            PDFHandler._draw_text_box(c, name, text_config, img_h)
            c.showPage()
            
            if progress_cb:
                progress_cb(i+1, total, "Generating Combined PDF")
                
        c.save()

    @staticmethod
    def generate_merged_certificates_multi(template_path, rows_fields_values, text_configs, output_path, progress_cb=None):
        """Generates a single PDF with all certificates for multiple text boxes."""
        with Image.open(template_path) as img:
            img_w, img_h = img.size
            
        c = canvas.Canvas(output_path, pagesize=(img_w, img_h))
        total = len(rows_fields_values)
        for i, fields_values in enumerate(rows_fields_values):
            c.drawImage(template_path, 0, 0, width=img_w, height=img_h)
            for text_val, cfg in zip(fields_values, text_configs):
                PDFHandler._draw_text_box(c, text_val, cfg, img_h)
            c.showPage()
            
            if progress_cb:
                progress_cb(i+1, total, "Generating Combined PDF")
                
        c.save()

    @staticmethod
    def merge_pdfs(pdf_paths, output_path):
        merger = pypdf.PdfWriter()
        for pdf in pdf_paths:
            merger.append(pdf)
        merger.write(output_path)
        merger.close()

