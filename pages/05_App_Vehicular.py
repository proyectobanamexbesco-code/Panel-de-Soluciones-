import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
from datetime import datetime

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="App Vehicular",
    page_icon="🚗",
    layout="wide"
)

st.title("📋 Reporte Vehicular")

# ---------------------------------------------------
# CARGAR DATA
# ---------------------------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_excel("CONCENTRADO REGION CENTRO 1.xlsx", engine="openpyxl")
    df.columns = ["Region","Oficina","Placa","Modelo","Responsable","Puesto"]
    return df

df = cargar_datos()

# ---------------------------------------------------
# SELECCIÓN
# ---------------------------------------------------
placa = st.selectbox("Selecciona la placa", df["Placa"].unique())
data = df[df["Placa"] == placa].iloc[0]

col1, col2 = st.columns(2)

with col1:
    st.text(f"Oficina: {data['Oficina']}")
    st.text(f"Modelo: {data['Modelo']}")

with col2:
    st.text(f"Responsable: {data['Responsable']}")
    st.text(f"Puesto: {data['Puesto']}")

# ---------------------------------------------------
# CARGA IMÁGENES
# ---------------------------------------------------
st.markdown("### 📸 Evidencias")

secciones = [
    "Frente","Atras","Costado Izquierdo","Costado Derecho",
    "Tablero","Asientos Delanteros","Asientos Traseros",
    "Herramienta","Llanta","Tarjeta","Poliza"
]

imagenes = {}

for sec in secciones:
    imagenes[sec] = st.file_uploader(f"{sec}", type=["jpg","png"], key=sec)

# ---------------------------------------------------
# OBSERVACIONES
# ---------------------------------------------------
observaciones = st.text_area("📝 Observaciones")

# ---------------------------------------------------
# GENERAR PDF
# ---------------------------------------------------
def generar_pdf():
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp.name, pagesize=letter)

    y = 750

    c.drawString(50, y, "REPORTE VEHICULAR")
    y -= 30

    c.drawString(50, y, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 30

    c.drawString(50, y, f"Placa: {placa}")
    y -= 20
    c.drawString(50, y, f"Oficina: {data['Oficina']}")
    y -= 20
    c.drawString(50, y, f"Modelo: {data['Modelo']}")
    y -= 20
    c.drawString(50, y, f"Responsable: {data['Responsable']}")
    y -= 20
    c.drawString(50, y, f"Puesto: {data['Puesto']}")
    y -= 30

    if observaciones:
        c.drawString(50, y, f"Observaciones: {observaciones}")
        y -= 30

    for nombre, img in imagenes.items():
        if img:
            img_temp = tempfile.NamedTemporaryFile(delete=False)
            img_temp.write(img.read())
            img_temp.close()

            c.drawString(50, y, nombre)
            y -= 10
            c.drawImage(img_temp.name, 50, y-100, width=200, height=100)
            y -= 120

            if y < 100:
                c.showPage()
                y = 750

    c.save()
    return temp.name

# ---------------------------------------------------
# BOTONES
# ---------------------------------------------------
if st.button("📄 Generar PDF"):
    pdf = generar_pdf()

    with open(pdf, "rb") as f:
        st.download_button(
            "⬇️ Descargar Reporte",
            data=f,
            file_name=f"Reporte_{placa}.pdf",
            mime="application/pdf"
        )
