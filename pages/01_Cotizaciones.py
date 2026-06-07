import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import date

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizaciones | Besco",
    page_icon="💰",
    layout="wide"
)

# ==========================================
# LÓGICA DE CONEXIÓN A GOOGLE SHEETS
# ==========================================
def obtener_credenciales():
    """Carga credenciales desde st.secrets."""
    # Asegúrate de tener el campo 'gcp_service_account' en tu archivo .streamlit/secrets.toml
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
    return None

@st.cache_data(show_spinner=False, ttl=300)
def cargar_preciario_desde_sheets():
    """Conecta y descarga el preciario."""
    creds = obtener_credenciales()
    if not creds:
        raise ValueError("No se encontraron credenciales de Google Cloud en st.secrets.")
    
    url = st.secrets.get("PRECIARIO_BESCO_URL")
    if not url:
        raise ValueError("No se configuró 'PRECIARIO_BESCO_URL' en st.secrets.")
    
    client = gspread.authorize(creds)
    sheet = client.open_by_url(url)
    ws = sheet.get_worksheet(0)
    data = ws.get_all_records()
    return pd.DataFrame(data)

# ==========================================
# ESTADO DE LA SESIÓN
# ==========================================
def inicializar_session():
    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = {
            "folio": "", "fecha": date.today(), "cliente_nombre": "", 
            "cliente_empresa": "", "cliente_contacto": "", "cotiza_nombre": "", "cotiza_puesto": ""
        }
    if "conceptos" not in st.session_state:
        st.session_state.conceptos = []

inicializar_session()

# ==========================================
# UI: SECCIÓN 1 - IDENTIFICACIÓN
# ==========================================
st.title("💰 Cotizaciones - Grupo Besco")

with st.container(border=True):
    st.markdown("### 1. Identificación")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.datos_cotizacion["folio"] = st.text_input("Folio:", value=st.session_state.datos_cotizacion["folio"])
        st.session_state.datos_cotizacion["cliente_nombre"] = st.text_input("Cliente:", value=st.session_state.datos_cotizacion["cliente_nombre"])
    with col2:
        st.session_state.datos_cotizacion["fecha"] = st.date_input("Fecha:", value=st.session_state.datos_cotizacion["fecha"])
        st.session_state.datos_cotizacion["cliente_empresa"] = st.text_input("Empresa:", value=st.session_state.datos_cotizacion["cliente_empresa"])

# ==========================================
# UI: SECCIÓN 2 - PRECIARIO (GOOGLE SHEETS)
# ==========================================
with st.container(border=True):
    st.markdown("### 2. Selección de Conceptos")
    
    modo = st.radio("Modo de entrada:", ["Captura Manual", "Preciario Google Sheets"], horizontal=True)
    
    descripcion = ""
    precio_unitario = 0.0
    
    if modo == "Preciario Google Sheets":
        try:
            df = cargar_preciario_desde_sheets()
            # Asumiendo columnas: 'clave', 'descripcion', 'precio'
            busqueda = st.text_input("Buscar concepto...")
            if busqueda:
                df = df[df['descripcion'].str.contains(busqueda, case=False, na=False)]
            
            opcion = st.selectbox("Selecciona concepto:", df['descripcion'].tolist())
            fila = df[df['descripcion'] == opcion].iloc[0]
            descripcion = fila['descripcion']
            precio_unitario = float(fila['precio'])
            st.success(f"Concepto cargado: {descripcion} | Precio: ${precio_unitario:,.2f}")
        except Exception as e:
            st.error(f"Error al conectar con el Preciario: {e}")
            st.info("Verifica que el email de tu cuenta de servicio sea 'Editor' en tu archivo de Google Sheets.")
    else:
        descripcion = st.text_area("Descripción:")
        precio_unitario = st.number_input("Precio:", min_value=0.0)

    if st.button("➕ Agregar a la cotización"):
        st.session_state.conceptos.append({"descripcion": descripcion, "precio": precio_unitario})
        st.rerun()

# ==========================================
# UI: SECCIÓN 3 - RESUMEN Y TOTALES
# ==========================================
with st.container(border=True):
    st.markdown("### 3. Conceptos Agregados")
    if st.session_state.conceptos:
        df_final = pd.DataFrame(st.session_state.conceptos)
        st.table(df_final)
        st.metric("TOTAL", f"${df_final['precio'].sum():,.2f}")
    else:
        st.write("No hay conceptos agregados.")
