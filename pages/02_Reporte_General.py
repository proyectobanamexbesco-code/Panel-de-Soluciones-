import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import io
from pypdf import PdfWriter

# --- CONFIGURACIÓN Y LIMPIEZA ---
def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

st.set_page_config(page_title="BESCO | Reporte General", layout="wide")

class BESCO_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.cell(0, 10, limpiar_texto('REPORTE GENERAL DE MANTENIMIENTO - BESCO'), 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, limpiar_texto(f'Página {self.page_no()}'), 0, 0, 'C')

# --- INTERFAZ DE USUARIO ---
st.title("📋 Generador de Reporte General")

with st.expander("Datos del Reporte", expanded=True):
    col1, col2 = st.columns(2)
    cliente = col1.text_input("Cliente")
    folio = col2.text_input("Folio / OT / TK", max_chars=20)
    ubicacion = st.text_input("Ubicación / Sucursal")
    observaciones = st.text_area("Observaciones Generales")

if st.button("🚀 Generar PDF"):
    try:
        pdf = BESCO_PDF()
        pdf.add_page()
        
        # Sección de Información
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, limpiar_texto("Información del Servicio"), 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 7, limpiar_texto(f"Cliente: {cliente}"), 0, 1)
        pdf.cell(0, 7, limpiar_texto(f"Folio: {folio}"), 0, 1)
        pdf.cell(0, 7, limpiar_texto(f"Ubicación: {ubicacion}"), 0, 1)
        pdf.ln(5)
        
        # Sección de Observaciones
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, limpiar_texto("Observaciones"), 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 7, limpiar_texto(observaciones))

        # Generación del archivo en memoria
        pdf_output = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
        pdf_output.write(pdf_bytes)
        pdf_output.seek(0)

        st.success("¡Reporte generado exitosamente!")
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_output,
            file_name=f"Reporte_{folio}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Error al generar el reporte: {e}")
        st.info("Asegúrate de que 'pypdf' esté en tu requirements.txt")

# --- MENSAJE DE AYUDA ---
st.markdown("---")
st.caption("Si la aplicación se corta, verifica los logs en la consola de Streamlit Cloud para confirmar que la instalación de librerías finalizó correctamente.")
