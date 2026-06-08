import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import smtplib
from email.message import EmailMessage
import io
import uuid
from pypdf import PdfWriter

# --- RUTAS PARA EL LOGOTIPO BESCO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOGO_PATH = r"C:\Users\GerardoMendez\OneDrive - Grupo Besco\Escritorio\MisProyectos\logo.png"
CLOUD_LOGO_BESCO = os.path.join(BASE_DIR, "logo besco 2026.jpeg")

if os.path.exists(CLOUD_LOGO_BESCO):
    LOGO_PATH = CLOUD_LOGO_BESCO
elif os.path.exists(LOCAL_LOGO_PATH):
    LOGO_PATH = LOCAL_LOGO_PATH
else:
    LOGO_PATH = None

# --- FUNCIÓN DE LIMPIEZA DE TEXTO ---
def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    # Reemplaza caracteres conflictivos por algo seguro en latin-1
    return texto.encode('latin-1', 'replace').decode('latin-1')

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Evidencia Técnica", layout="wide")

class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                img_logo = Image.open(LOGO_PATH).convert("RGB")
                temp_logo = "temp_logo_principal.jpg"
                img_logo.save(temp_logo, format="JPEG")
                orig_w, orig_h = img_logo.size
                final_h = 25
                escala = final_h / orig_h
                self.image(temp_logo, x=10, y=8, w=orig_w * escala, h=final_h)
            except Exception:
                pass
                    
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, limpiar_texto('REPORTE DE SERVICIO TÉCNICO - BESCO'), 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, limpiar_texto(f"Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), 0, 1, 'R')
        self.ln(12)

    def add_custom_section(self, title):
        if self.get_y() > 250: self.add_page()
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, limpiar_texto(f"{self.section_count}. {title.upper()}"), 0, 1, 'L', fill=True)
        self.section_count += 1
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def photo_grid(self, title, photos, prefix="img"):
        if not photos: return
        self.add_custom_section(title)
        ancho, alto, esp = 90, 65, 72
        for i, foto in enumerate(photos):
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_p = f"temp_{prefix}_{uuid.uuid4().hex}.jpg"
            img.save(temp_p, format="JPEG")
            col = i % 2
            if col == 0 and (self.get_y() + alto > 265): self.add_page()
            y_act = self.get_y()
            self.image(temp_p, x=10 + (col * 95), y=y_act, w=ancho, h=alto)
            if col == 1 or i == len(photos) - 1: self.set_y(y_act + esp)

def enviar_correo(pdf_bytes, cliente, folio, sucursal, oficina, nombre_archivo, correos_extra, fecha_ejec, lista_destinatarios):
    try:
        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        destinatarios = list(set(lista_destinatarios + ([c.strip() for c in correos_extra.split(",")] if correos_extra else [])))
        msg = EmailMessage()
        msg['Subject'] = limpiar_texto(f"Reporte BESCO: {cliente} | TK: {folio}")
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios)
        msg.set_content(limpiar_texto(f"Reporte técnico para {cliente}, folio {folio}."))
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error SMTP: {e}")
        return False

# --- INTERFAZ ---
st.title("📑 Sistema de Evidencia Técnica BESCO")
cliente = st.text_input("Cliente")
folio = st.text_input("Folio / OT / TK", max_chars=20)
# ... [Resto de tus inputs] ...

if st.button("🚀 Generar y Enviar Reporte"):
    with st.spinner("Generando..."):
        pdf = BESCO_PDF()
        pdf.add_page()
        pdf.add_custom_section("Información General")
        pdf.cell(0, 7, limpiar_texto(f"Cliente: {cliente} | Folio: {folio}"), 0, 1)
        # ... [Lógica de generación de celdas con limpiar_texto()] ...

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        
        # Integración de PDFs adicionales
        # ... [Lógica de pypdf usando merger] ...

        nom_archivo = limpiar_texto(f"Reporte_{cliente}_{folio}.pdf").replace(" ", "_")
        enviar_correo(pdf_bytes, cliente, folio, "Sucursal", "Oficina", nom_archivo, "", "Fecha", [])
        st.download_button("📥 Descargar", data=pdf_bytes, file_name=nom_archivo, mime="application/pdf")
