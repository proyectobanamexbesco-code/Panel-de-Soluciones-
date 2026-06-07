import streamlit as st
import pandas as pd
import sys
import os
from fpdf import FPDF
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client

st.set_page_config(page_title="Cotizaciones | Besco", page_icon="📄", layout="wide")

st.title("📄 Generador de Cotizaciones")

@st.cache_data(ttl=600)
def cargar_preciario():
    # ... (tu lógica de carga de preciario)
    return pd.DataFrame()

df_precios = cargar_preciario()

# El form engloba todo, pero usaremos contenedores dentro para separar visualmente
with st.form("cotizador_form"):
    
    # --- SECCIÓN 1: Cliente ---
    with st.container(border=True):
        st.markdown("### 1. Datos de Identificación del Cliente")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("CLIENTE:")
            inmueble = st.text_input("INMUEBLE:")
        with col2:
            reporte = st.text_input("# DE TICKET:")
            titulo_cotizacion = st.text_input("TIPO DE TRABAJO:")

    # --- SECCIÓN 2: Cotizador ---
    with st.container(border=True):
        st.markdown("### 2. Datos del Cotizador")
        col3, col4 = st.columns(2)
        with col3:
            cotizador_nombre = st.text_input("ELABORÓ / COTIZÓ:")
            puesto = st.selectbox("PUESTO:", ["Gerente", "Supervisor", "Cotizador"])
        with col4:
            f_cot = st.date_input("FECHA COTIZACIÓN:")
            f_sol = st.date_input("FECHA SOLICITUD:")

    # --- SECCIÓN 3: Conceptos (separado) ---
    with st.container(border=True):
        st.markdown("### 3. Conceptos a Cotizar")
        habilitar = st.toggle("Habilitar Preciario Besco", value=True)
        
        datos_para_pdf = []
        if habilitar:
            # Aquí va tu lógica de búsqueda del preciario
            st.info("Búsqueda de preciario habilitada...")
        else:
            st.warning("Captura manual habilitada...")

    # Botón único al final del formulario
    submit = st.form_submit_button("📄 Generar PDF Formato Besco", type="primary")

    if submit:
        st.success("Generando PDF...")
