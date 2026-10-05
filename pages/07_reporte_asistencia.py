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

# --- CONFIGURACIÓN Y CONEXIÓN A GOOGLE SHEETS ---
@st.cache_resource(ttl=600)
def init_gspread_client():
    """Autentica y regresa el cliente de gspread usando la cuenta de servicio."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # Se busca la configuración de Google (sin alterar otros módulos)
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif "google_credentials" in st.secrets:
            creds_dict = dict(st.secrets["google_credentials"])
        else:
            st.error("❌ No se encontraron credenciales de Google en st.secrets.")
            return None
        
        # Sanitizar saltos de línea
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"❌ Error de autenticación en init_gspread_client: {type(e).__name__} - {str(e)}")
        return None

@st.cache_data(ttl=60) # Tiempo de caché reducido para refrescar la lista
def cargar_personal_desde_sheets(spreadsheet_id):
    """Obtiene los datos y el objeto worksheet de la primera pestaña."""
    gc = init_gspread_client()
    if not gc:
        return pd.DataFrame(), None
    
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)  # Lee la primera pestaña 
        datos = worksheet.get_all_records()
        return pd.DataFrame(datos), worksheet
    except Exception as e:
        st.error(f"❌ Error al leer la lista de personal de Google Sheets: {type(e).__name__} - {str(e)}")
        return pd.DataFrame(), None

# --- INTERFAZ PRINCIPAL ---
st.title("📋 Control de Asistencia por Sitio")

# Selector de sitio, fecha y responsable
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    sitio_seleccionado = st.selectbox(
        "🏢 SITE:",
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

# ID EXACTO DE TU HOJA DE ASISTENCIA
spreadsheet_id = "1qcvjwgbiSoCX0uvZSEv_qxlmHyrZ22B-knQGHwmkNRU"

df_personal, worksheet = cargar_personal_desde_sheets(spreadsheet_id)

if not df_personal.empty:
    # Rellenar datos vacíos para evitar fallos de lectura en Streamlit
    df_personal = df_personal.fillna("")
    
    # Formatear la fecha para que empate con el encabezado de tu Google Sheets (ej: 5/10/2026)
    col_fecha = f"{fecha_registro.day}/{fecha_registro.month}/{fecha_registro.year}"
    
    # Si la columna de ese día aún no existe en el registro general, la agregamos
    if col_fecha not in df_personal.columns:
        df_personal[col_fecha] = ""

    # Filtrar por la columna SITE
    if "SITE" in df_personal.columns:
        df_sitio = df_personal[df_personal["SITE"] == sitio_seleccionado].copy()
    else:
        df_sitio = df_personal.copy()

    if df_sitio.empty:
        st.warning(f"No se encontró personal asignado al sitio **{sitio_seleccionado}**.")
    else:
        st.markdown(f"### Personal asignado — **{sitio_seleccionado}** ({col_fecha})")
        
        # Opciones para la lista desplegable
        estatus_opciones = ["", "Asistencia", "Falta", "Vacaciones", "Incapacidad", "Descanso"]
        columnas_fijas = ["No_Empleado", "Nombre Completo", "Fecha de ingreso", "SITE", "PUESTO", "MES"]
        
        # Configuración dinámica de columnas
        configuracion_columnas = {}
        for col in df_sitio.columns:
            if col in columnas_fijas:
                # Bloquear edición de datos fijos del empleado
                configuracion_columnas[col] = st.column_config.TextColumn(col, disabled=True)
            else:
                # Convertir cualquier columna de fecha en lista desplegable
                configuracion_columnas[col] = st.column_config.SelectboxColumn(
                    col,
                    options=estatus_opciones,
                    width="small"
                )

        # Desplegar la cuadrícula de asistencia
        df_editado = st.data_editor(
            df_sitio,
            column_config=configuracion_columnas,
            use_container_width=True,
            hide_index=True,
            key=f"editor_{sitio_seleccionado}"
        )

        if st.button("💾 Guardar Registro de Asistencia", type="primary"):
            if not persona_reporta.strip():
                st.error("⚠️ Ingrese el nombre de la persona que valida antes de guardar.")
            else:
                with st.spinner("Guardando registro en la plantilla mensual..."):
                    try:
                        col_id = "No_Empleado" if "No_Empleado" in df_personal.columns else df_personal.columns[0]
                        
                        # 1. Actualizar los datos modificados del grid filtrado hacia el Dataframe General
                        for idx, row in df_editado.iterrows():
                            match_idx = df_personal[df_personal[col_id] == row[col_id]].index
                            if not match_idx.empty:
                                df_personal.loc[match_idx[0], col_fecha] = row[col_fecha]
                        
                        # 2. Transformar el dataframe completo a formato de lista para Google Sheets
                        datos_a_subir = [df_personal.columns.values.tolist()] + df_personal.astype(str).values.tolist()
                        
                        # 3. Limpiar la primera pestaña y cargar el Dataframe actualizado
                        worksheet.clear()
                        worksheet.update(values=datos_a_subir, range_name="A1")
                        
                        # Refrescar memoria caché
                        st.cache_data.clear()
                        st.success(f"¡Asistencia de **{sitio_seleccionado}** para el **{col_fecha}** registrada exitosamente!")
                        
                    except Exception as e:
                        st.error(f"Error al escribir en Google Sheets: {type(e).__name__} - {str(e)}")
