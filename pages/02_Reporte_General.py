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

# --- CONFIGURACIÓN DE RUTAS Y LOGOTIPO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Lista de nombres de archivos de logo permitidos
LOGOS_POSIBLES = ["logo besco 2026.jpeg", "logo.png", "logo.jpg"]
LOGO_PATH = None
for logo in LOGOS_POSIBLES:
    path = os.path.join(BASE_DIR, logo)
    if os.path.exists(path):
        LOGO_PATH = path
        break

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Portal de Soluciones", layout="wide")

st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold !important; color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CLASE PDF ---
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                img_logo = Image.open(LOGO_PATH).convert("RGB")
                temp_logo = f"temp_logo_{uuid.uuid4().hex}.jpg"
                img_logo.save(temp_logo, format="JPEG")
                orig_w, orig_h = img_logo.size
                escala = 25 / orig_h
                self.image(temp_logo, x=10, y=8, w=orig_w * escala, h=25)
            except: pass
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, 'REPORTE DE SERVICIO TÉCNICO - BESCO', 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, f"Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'R')
        self.ln(12)

    def add_custom_section(self, title):
        if self.get_y() > 250: self.add_page()
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f"{self.section_count}. {title.upper()}", 0, 1, 'L', fill=True)
        self.section_count += 1
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def photo_grid(self, title, photos, eq_index, prefix="img"):
        if not photos: return
        self.add_custom_section(title)
        ancho, alto, esp_v = 90, 65, 72
        for i, foto in enumerate(photos):
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_p = f"temp_{prefix}_{uuid.uuid4().hex}.jpg"
            img.save(temp_p, format="JPEG")
            col = i % 2
            if col == 0 and (self.get_y() + alto > 265): self.add_page()
            y_act = self.get_y()
            self.image(temp_p, x=10 + (col * 95), y=y_act, w=ancho, h=alto)
            if col == 1 or i == len(photos) - 1: self.set_y(y_act + esp_v)

    def folio_grid(self, title, photo_files):
        for i, foto in enumerate(photo_files[:4]):
            self.add_page()
            self.add_custom_section(f"{title} - Evidencia {i+1}")
            foto.seek(0)
            img = Image.open(foto).convert("RGB")
            temp_f = f"temp_folio_{uuid.uuid4().hex}.jpg"
            img.save(temp_f, format="JPEG")
            self.image(temp_f, x=10, y=self.get_y()+5, w=190)

# --- LÓGICA DE CORREO ---
def enviar_correo(pdf_bytes, cliente, folio, sucursal, oficina, nombre_archivo, correos_extra, fecha_ejec, dest_oficina):
    try:
        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        destinatarios = list(set(dest_oficina + ([c.strip() for c in correos_extra.split(",")] if correos_extra else [])))
        msg = EmailMessage()
        msg['Subject'] = f"Reporte BESCO: {cliente} | TK: {folio} | Of: {oficina}"
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios)
        msg.set_content(f"Reporte generado.\n\nFecha: {fecha_ejec}\nOficina: {oficina}\nCliente: {cliente}\nFolio: {folio}\nSucursal: {sucursal}")
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error SMTP: {e}")
        return False

# --- INTERFAZ PRINCIPAL ---
st.title("📑 Portal de Soluciones BESCO - Reporte General")

c1, c2, c3 = st.columns([2, 1, 1.5])
cliente = c1.text_input("Cliente")
folio = c2.text_input("Folio / OT / TK", max_chars=20)
fecha_ejec = c3.date_input("Fecha de Ejecución", datetime.now())

col_l1, col_l2 = st.columns(2)
sucursal = col_l1.text_input("Sucursal")
oficina = col_l2.selectbox("Oficina", ["Acapulco", "Toluca", "Pachuca", "Michoacán", "Zonas/ CDMX", "CDMX", "Ben & Company", "BX+", "Emerson", "Odoo", "Tampico"])

c_t1, c_t2, c_t3, c_t4 = st.columns(4)
tecnico = c_t1.text_input("Técnico")
supervisor = c_t2.text_input("Supervisor")
tipo_serv = c_t3.selectbox("Servicio", ["Preventivo", "Correctivo", "Emergencia"])
ref = c_t4.selectbox("Referencia", ["Con Ticket", "Sin Ticket"])

st.subheader("Evidencia Documental")
archivos_folio = st.file_uploader("Subir archivos (JPG/PDF)", accept_multiple_files=True)

st.subheader("Equipos")
num_eq = st.number_input("Número de equipos", 1, 20, 1)
equipos_data = []
for i in range(num_eq):
    with st.expander(f"Equipo {i+1}", expanded=True):
        cat = st.selectbox("Categoría", ["Aire Acondicionado", "Tableros Eléctricos", "Hidroneumático", "Conservación", "Hidrosanitario", "Iluminación", "Otros"], key=f"c{i}")
        estatus = st.selectbox("Estatus", ["Operando correctamente", "Operando con observaciones", "No queda operando"], key=f"e{i}")
        tag = st.text_input("TAG", key=f"tg{i}")
        act = st.text_area("Actividades", key=f"a{i}")
        fa = st.file_uploader("Fotos ANTES", accept_multiple_files=True, key=f"fa{i}")
        fd = st.file_uploader("Fotos DESPUÉS", accept_multiple_files=True, key=f"fd{i}")
        equipos_data.append({"cat": cat, "estatus": estatus, "tag": tag, "act": act, "fa": fa, "fd": fd})

df_mat = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripción"]), num_rows="dynamic")

# --- ENVÍO ---
mapeo = {"Acapulco": ["itzallana.vazquez@besco.mx", "gerardo.fuentes@besco.mx"], "Toluca": ["policarpo.rosaliano@besco.mx", "monica.iniestra@besco.mx"], "Pachuca": ["german.constantino@besco.mx"], "Michoacán": ["cristobal.rodriguez@besco.mx", "ximena.acosta@besco.mx", "javier.zamano@besco.mx"], "Zonas/ CDMX": ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "brenda.cervantes@besco.mx"], "CDMX": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx"], "Ben & Company": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx"], "BX+": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "patricia.cortes@besco.mx"], "Emerson": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "patricia.cortes@besco.mx"], "Odoo": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "dorian.rodriguez@besco.mx"], "Tampico": ["ingrid.lucio@besco.mx", "joel.perez@besco.mx", "gerardo.mendez@besco.mx"]}
dest_oficina = mapeo.get(oficina, ["gerardo.mendez@besco.mx"])
if "gerardo.mendez@besco.mx" not in dest_oficina: dest_oficina.append("gerardo.mendez@besco.mx")
correos_extra = st.text_input("Correos adicionales")

if st.button("🚀 Generar y Enviar Reporte"):
    pdf = BESCO_PDF()
    pdf.add_page()
    pdf.cell(0, 10, f"Cliente: {cliente} | Folio: {folio}", 0, 1)
    
    for eq in equipos_data:
        pdf.add_custom_section(f"EQUIPO: {eq['tag']} - {eq['cat']}")
        pdf.multi_cell(0, 7, f"Actividades: {eq['act']}")
        pdf.photo_grid("Antes", eq['fa'], eq['tag'])
        pdf.photo_grid("Después", eq['fd'], eq['tag'])
        
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    # Procesar adjuntos PDF
    pdfs = [f for f in archivos_folio if f and f.type == "application/pdf"]
    if pdfs:
        merger = PdfWriter()
        merger.append(io.BytesIO(pdf_bytes))
        for p in pdfs:
            p.seek(0)
            merger.append(p)
        out = io.BytesIO()
        merger.write(out)
        pdf_bytes = out.getvalue()
        
    if enviar_correo(pdf_bytes, cliente, folio, sucursal, oficina, f"Reporte_{folio}.pdf", correos_extra, fecha_ejec.strftime('%d/%m/%Y'), dest_oficina):
        st.success("✅ Enviado.")
    st.download_button("📥 Descargar", data=pdf_bytes, file_name=f"Reporte_{folio}.pdf", mime="application/pdf")
