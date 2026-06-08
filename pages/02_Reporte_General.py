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

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="BESCO | Reporte General", layout="wide")

def limpiar_texto(texto):
    if not isinstance(texto, str): texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

# Clase PDF con tu estructura original
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        logo_path = os.path.join(os.path.dirname(__file__), "logo besco 2026.jpeg")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 45)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, limpiar_texto('REPORTE DE SERVICIO TÉCNICO - BESCO'), 0, 1, 'R')
        self.ln(20)

    def add_custom_section(self, title):
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, limpiar_texto(f"{self.section_count}. {title.upper()}"), 0, 1, 'L', fill=True)
        self.section_count += 1
        self.set_text_color(0, 0, 0)
        self.ln(5)

# --- INTERFAZ ---
st.title("📑 Sistema de Evidencia Técnica BESCO")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    cliente = col1.text_input("Cliente")
    folio = col2.text_input("Folio / OT / TK", max_chars=20)
    fecha_ejec = col3.date_input("Fecha de Ejecución")
    col4, col5 = st.columns(2)
    sucursal = col4.text_input("Sucursal / Inmueble")
    oficina = col5.selectbox("Oficina", ["Acapulco", "Toluca", "Pachuca", "Michoacán", "CDMX", "Tampico"])

st.subheader("Equipos y Materiales")
num_equipos = st.number_input("Número de equipos", 1, 20, 1)
equipos_data = []
for i in range(num_equipos):
    with st.expander(f"Equipo {i+1}", expanded=True):
        tag = st.text_input(f"TAG {i+1}", key=f"t{i}")
        actividades = st.text_area(f"Actividades {i+1}", key=f"a{i}")
        equipos_data.append({"tag": tag, "actividades": actividades})

df_mat = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripción"]), num_rows="dynamic")

# --- LÓGICA FINAL ---
if st.button("🚀 Generar y Enviar Reporte", type="primary"):
    with st.spinner("Procesando..."):
        pdf = BESCO_PDF()
        pdf.add_page()
        
        pdf.add_custom_section("Información General")
        pdf.cell(0, 7, limpiar_texto(f"Cliente: {cliente} | Folio: {folio}"))
        pdf.ln(10)
        
        pdf.add_custom_section("Detalle de Equipos")
        for eq in equipos_data:
            pdf.cell(0, 7, limpiar_texto(f"TAG: {eq['tag']}"))
            pdf.ln(5)
            pdf.multi_cell(0, 7, limpiar_texto(f"Actividades: {eq['actividades']}"))
            pdf.ln(5)

        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')

        # Envío de Correo
        try:
            msg = EmailMessage()
            msg['Subject'] = limpiar_texto(f"Reporte BESCO: {cliente} | {folio}")
            msg['From'] = st.secrets["EMAIL_SENDER"]
            msg['To'] = "gerardo.mendez@besco.mx"
            msg.set_content("Reporte adjunto.")
            msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"Reporte_{folio}.pdf")
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"])
                smtp.send_message(msg)
            st.success("✅ Enviado.")
        except Exception as e:
            st.error(f"Error: {e}")

        st.download_button("📥 Descargar", data=pdf_bytes, file_name=f"Reporte_{folio}.pdf", mime="application/pdf")
