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

# --- CONFIGURACIÓN Y LIMPIEZA ---
def limpiar_texto(texto):
    if not isinstance(texto, str): texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

st.set_page_config(page_title="BESCO | Reporte General", layout="wide")

class BESCO_PDF(FPDF):
    def header(self):
        # Logo ajustado (50% más grande)
        logo_path = os.path.join(os.path.dirname(__file__), "logo besco 2026.jpeg")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 45)
            
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, limpiar_texto('REPORTE DE SERVICIO TÉCNICO'), 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, limpiar_texto(f"Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), 0, 1, 'R')
        self.ln(20)

# --- INTERFAZ COMPACTA ---
st.title("📑 Reporte General de Evidencia Técnica")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    cliente = col1.text_input("Cliente")
    folio = col2.text_input("Folio / OT / TK", max_chars=20)
    fecha = col3.date_input("Fecha de Ejecución")
    
    col4, col5 = st.columns(2)
    sucursal = col4.text_input("Sucursal / Inmueble")
    oficina = col5.selectbox("Oficina", ["Acapulco", "Toluca", "Pachuca", "Michoacán", "CDMX", "Tampico"])

# --- LÓGICA DE GENERACIÓN ---
if st.button("🚀 Generar y Enviar Reporte", type="primary", use_container_width=True):
    if not cliente or not folio:
        st.error("⚠️ Cliente y Folio son obligatorios.")
    else:
        with st.spinner("Generando PDF..."):
            pdf = BESCO_PDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 10)
            
            # Datos básicos
            pdf.cell(0, 7, limpiar_texto(f"Cliente: {cliente}"), 0, 1)
            pdf.cell(0, 7, limpiar_texto(f"Folio: {folio}"), 0, 1)
            pdf.cell(0, 7, limpiar_texto(f"Sucursal: {sucursal}"), 0, 1)
            
            # Generar PDF
            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
            
            # Envío de correo (usando st.secrets)
            try:
                msg = EmailMessage()
                msg['Subject'] = limpiar_texto(f"Reporte BESCO: {cliente} | {folio}")
                msg['From'] = st.secrets.get("EMAIL_SENDER", "admin@besco.mx")
                msg['To'] = "gerardo.mendez@besco.mx"
                msg.set_content(limpiar_texto("Reporte generado desde la app."))
                msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"Reporte_{folio}.pdf")
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"])
                    smtp.send_message(msg)
                st.success("✅ ¡Reporte generado y enviado con éxito!")
            except Exception as e:
                st.warning("⚠️ PDF generado, pero fallo al enviar correo. Descárgalo abajo.")
                st.error(f"Detalle: {e}")
            
            st.download_button("📥 Descargar Reporte", data=pdf_bytes, file_name=f"Reporte_{folio}.pdf", mime="application/pdf", use_container_width=True)
