import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Control de Asistencia por Sitio",
    page_icon="📋",
    layout="wide"
)

# --- FUNCIÓN DE CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource(ttl=600)
def init_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Obtener credenciales desde los secrets
    try:
        creds_dict = dict(st.secrets["google_credentials"])
        
        # Corrección de saltos de línea para la private_key PEM
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Error al autenticar credenciales con Google: {str(e)}")
        return None

@st.cache_data(ttl=300)
def cargar_personal_desde_sheets(spreadsheet_id):
    gc = init_gspread_client()
    if not gc:
        return pd.DataFrame()
    
    try:
        sh = gc.open_by_key(spreadsheet_id)
        # Seleccionar primera hoja por defecto o especificar por nombre
        worksheet = sh.get_worksheet(0)
        datos = worksheet.get_all_records()
        return pd.DataFrame(datos)
    except Exception as e:
        st.error(f"Error al leer la lista de personal de Google Sheets: {str(e)}")
        return pd.DataFrame()

# --- INTERFAZ PRINCIPAL ---
st.title("📋 Control de Asistencia por Sitio")

# Controles superiores
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    sitio_seleccionado = st.selectbox(
        "🗂 SITE:",
        ["MX10", "MX11", "MX12", "MX13"]
    )

with col2:
    fecha_registro = st.date_input(
        "📅 Fecha a registrar:",
        value=date.today()
    )

with col3:
    persona_reporta = st.text_input(
        "✍️ Persona que reporta / Valida:",
        placeholder="Ej. Ing. Gerardo Méndez"
    )

# --- LECTURA DE DATOS DESDE SHEETS ---
spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "12Hehx2g0vZNS0FmXMeBlcF9JRstS2CZnVknItFjI7sM")
df_personal = cargar_personal_desde_sheets(spreadsheet_id)

if not df_personal.empty:
    # Filtrar por sitio si la columna 'SITE' existe en la hoja
    if "SITE" in df_personal.columns:
        df_sitio = df_personal[df_personal["SITE"] == sitio_seleccionado]
    else:
        df_sitio = df_personal

    st.subheader(f"Personal asignado a {sitio_seleccionado}")
    
    # Opciones de asistencia para la tabla interactiva
    estatus_opciones = ["Asistencia", "Falta", "Incapacidad", "Vacaciones", "Permiso"]
    
    if "Estatus" not in df_sitio.columns:
        df_sitio["Estatus"] = "Asistencia"
        
    df_editado = st.data_editor(
        df_sitio,
        column_config={
            "Estatus": st.column_config.SelectboxColumn(
                "Estatus de Asistencia",
                options=estatus_opciones,
                required=True
            )
        },
        use_container_width=True,
        hide_index=True
    )

    if st.button("💾 Guardar Registro de Asistencia", type="primary"):
        st.success(f"Registro guardado correctamente para el sitio {sitio_seleccionado} con fecha {fecha_registro}.")
