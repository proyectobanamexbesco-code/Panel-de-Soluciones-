import streamlit as st
import pandas as pd
import sys
import os
from fpdf import FPDF
from datetime import date

# Asegura que la app encuentre tu archivo utils.py en la carpeta principal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client

# Configuración individual de la página
st.set_page_config(page_title="Cotizaciones | Besco", page_icon="📄")

st.title("📄 Cotizaciones - Sistema Besco")

# st.cache_data hace que la app sea mucho más rápida al no descargar el Excel en cada clic
@st.cache_data(ttl=600)
def cargar_preciario():
    try:
        client = obtener_gspread_client()
        sheet = client.open("Preciario Besco").sheet1
        df = pd.DataFrame(sheet.get_all_records())
        # Normalizamos los títulos para evitar errores por espacios o minúsculas
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return pd.DataFrame()

df_precios = cargar_preciario()

if not df_precios.empty:
    with st.form("cotizador_form"):
        cliente = st.text_input("Nombre del Cliente")
        
        # Apuntamos exactamente a la columna que mostraste en tu captura
        conceptos = st.multiselect("Selecciona los conceptos del preciario", df_precios["CONCEPTO"].tolist())
        
        # Botón de envío del formulario
        submit = st.form_submit_button("Generar PDF de Cotización")
        
        if submit:
            if cliente and conceptos:
                st.success(f"Procesando cotización para {cliente}...")
                
                # Generación del PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, f"Cotizacion para: {cliente}", ln=True)
                
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"Fecha: {date.today().strftime('%d/%m/%Y')}", ln=True)
                pdf.ln(10)
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Conceptos Seleccionados:", ln=True)
                
                pdf.set_font("Arial", size=12)
                for c in conceptos:
                    # multi_cell permite que los textos largos se ajusten al ancho de la hoja
                    pdf.multi_cell(0, 8, f"- {c}")
                    pdf.ln(2)
                
                # Preparar descarga del PDF
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(
                    label="📥 Descargar Documento PDF",
                    data=pdf_bytes,
                    file_name=f"Cotizacion_{cliente.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("Por favor, ingresa el nombre del cliente y selecciona al menos un concepto.")
else:
    st.info("Cargando base de datos o el preciario está vacío.")
