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

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Aseguramos que busque el logo en la ruta del servidor
LOGOS_POSIBLES = ["logo besco 2026.jpeg", "logo.png", "logo.jpg"]
LOGO_PATH = None
for logo in LOGOS_POSIBLES:
    path = os.path.join(BASE_DIR, logo)
    if os.path.exists(path):
        LOGO_PATH = path
        break

# --- FUNCIONES DE APOYO ---
def limpiar_texto(texto):
    if not isinstance(texto, str): texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

# --- CLASE PDF ---
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if LOGO_PATH:
            self.image(LOGO_PATH, 10, 8, 45)
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
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def photo_grid(self, title, photos, prefix="img"):
        if not photos: return
        self.add_custom_section(title)
        ancho_foto, alto_foto, espacio_v = 90, 65, 72
        for i, foto in enumerate(photos):
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_p = f"temp_{prefix}_{i}_{uuid.uuid4().hex}.jpg"
            img.save(temp_p, format="JPEG")
            col = i % 2
            if col == 0 and (self.get_y() + alto_foto > 265): self.add_page()
            y_act = self.get_y()
            self.image(temp_p, x=10 + (col * 95), y=y_act, w=ancho_foto, h=alto_foto)
            if col == 1 or i == len(photos) - 1: self.set_y(y_act + espacio_v)

    def folio_grid(self, title, photo_files):
        for i, foto in enumerate(photo_files[:4]):
            self.add_page()
            self.add_custom_section(f"{title} - {i+1}")
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_f = f"temp_folio_{i}.jpg"
            img.save(temp_f, format="JPEG")
            self.image(temp_f, x=10, y=self.get_y()+5, w=190)

# --- INTERFAZ ---
st.set_page_config(page_title="BESCO | Reporte General", layout="wide")
st.title("📑 Sistema de Evidencia Técnica BESCO")

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    cliente = col1.text_input("Cliente")
    folio = col2.text_input("Folio / OT / TK", max_chars=20)
    fecha_ejec = col3.date_input("Fecha", datetime.now())
    
    col4, col5 = st.columns(2)
    sucursal = col4.text_input("Sucursal")
    oficina = col5.selectbox("Oficina", ["Acapulco", "Toluca", "Pachuca", "Michoacán", "CDMX", "Tampico"])

num_equipos = st.number_input("Equipos atendidos", 1, 20, 1)
equipos_data = []
for i in range(num_equipos):
    with st.expander(f"EQUIPO {i+1}", expanded=True):
        tag = st.text_input("TAG", key=f"t{i}")
        act = st.text_area("Actividades", key=f"a{i}")
        fa = st.file_uploader("Fotos ANTES", accept_multiple_files=True, key=f"fa{i}")
        fd = st.file_uploader("Fotos DESPUÉS", accept_multiple_files=True, key=f"fd{i}")
        equipos_data.append({"tag": tag, "act": act, "fa": fa, "fd": fd})

df_mat = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripción"]), num_rows="dynamic")

# --- GENERACIÓN Y ENVÍO ---
if st.button("🚀 Generar y Enviar Reporte", type="primary"):
    pdf = BESCO_PDF()
    pdf.add_page()
    pdf.add_custom_section("Información General")
    pdf.cell(0, 7, limpiar_texto(f"Cliente: {cliente} | Folio: {folio} | Oficina: {oficina}"))
    pdf.ln(10)
    
    for eq in equipos_data:
        pdf.add_custom_section(f"EQUIPO: {eq['tag']}")
        pdf.multi_cell(0, 7, limpiar_texto(f"Actividades: {eq['act']}"))
        pdf.photo_grid("Fotos ANTES", eq['fa'], "antes")
        pdf.photo_grid("Fotos DESPUÉS", eq['fd'], "despues")

    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
    
    try:
        msg = EmailMessage()
        msg['Subject'] = limpiar_texto(f"Reporte BESCO: {cliente} | {folio}")
        msg['From'] = st.secrets["EMAIL_SENDER"]
        msg['To'] = "gerardo.mendez@besco.mx"
        msg.set_content("Reporte generado.")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=f"Reporte_{folio}.pdf")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"])
            smtp.send_message(msg)
        st.success("✅ ¡Reporte enviado!")
    except Exception as e:
        st.error(f"Error: {e}")

    st.download_button("📥 Descargar", data=pdf_bytes, file_name=f"Reporte_{folio}.pdf", mime="application/pdf")
