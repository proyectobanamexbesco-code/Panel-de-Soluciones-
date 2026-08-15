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
        if "google_credentials" not in st.secrets:
            st.error("❌ No se encontró la sección [google_credentials] en st.secrets.")
            return None

        creds_dict = dict(st.secrets["google_credentials"])
        
        # Sanitizar saltos de línea en la llave privada PEM
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"❌ Error de autenticación en init_gspread_client: {type(e).__name__} - {str(e)}")
        return None

@st.cache_data(ttl=300)
def cargar_personal_desde_sheets(spreadsheet_id):
    """Obtiene los datos del personal cargados en la primera pestaña del libro."""
    gc = init_gspread_client()
    if not gc:
        return pd.DataFrame()
    
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)  # Lee la primera pestaña de la plantilla
        datos = worksheet.get_all_records()
        return pd.DataFrame(datos)
    except Exception as e:
        st.error(f"❌ Error al leer la lista de personal de Google Sheets: {type(e).__name__} - {str(e)}")
        return pd.DataFrame()

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

# ID del libro configurado en tus Secrets
spreadsheet_id = st.secrets.get("SPREADSHEET_ID", "12Hehx2g0vZNS0FmXMeBlcF9JRstS2CZnVknItFjI7sM")

df_personal = cargar_personal_desde_sheets(spreadsheet_id)

if not df_personal.empty:
    # Filtrar por la columna SITE si existe
    if "SITE" in df_personal.columns:
        df_sitio = df_personal[df_personal["SITE"] == sitio_seleccionado].copy()
    else:
        df_sitio = df_personal.copy()

    if df_sitio.empty:
        st.warning(f"No se encontró personal asignado al sitio **{sitio_seleccionado}**.")
    else:
        st.markdown(f"### Personal asignado — **{sitio_seleccionado}** ({fecha_registro.strftime('%d/%m/%Y')})")
        
        estatus_opciones = ["Asistencia", "Falta", "Incapacidad", "Vacaciones", "Permiso"]
        
        if "Estatus" not in df_sitio.columns:
            df_sitio["Estatus"] = "Asistencia"
        if "Observaciones" not in df_sitio.columns:
            df_sitio["Observaciones"] = ""

        df_editado = st.data_editor(
            df_sitio,
            column_config={
                "Estatus": st.column_config.SelectboxColumn(
                    "Estatus de Asistencia",
                    options=estatus_opciones,
                    required=True
                ),
                "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
            },
            use_container_width=True,
            hide_index=True,
            key=f"editor_{sitio_seleccionado}"
        )

        if st.button("💾 Guardar Registro de Asistencia", type="primary"):
            if not persona_reporta.strip():
                st.error("⚠️ Ingrese el nombre de la persona que valida antes de guardar.")
            else:
                gc = init_gspread_client()
                if gc:
                    try:
                        sh = gc.open_by_key(spreadsheet_id)
                        
                        # Intenta abrir la pestaña 'Historial_Asistencia' o la crea automáticamente
                        try:
                            ws_historial = sh.worksheet("Historial_Asistencia")
                        except gspread.exceptions.WorksheetNotFound:
                            ws_historial = sh.add_worksheet(title="Historial_Asistencia", rows="1000", cols="10")
                            ws_historial.append_row(["Fecha", "SITE", "No_Empleado", "Nombre", "Puesto", "Estatus", "Observaciones", "Reportado_Por"])

                        # Construcción de filas a enviar a Sheets
                        filas_a_insertar = []
                        for _, row in df_editado.iterrows():
                            filas_a_insertar.append([
                                fecha_registro.strftime("%Y-%m-%d"),
                                sitio_seleccionado,
                                str(row.get("No_Empleado", "")),
                                str(row.get("Nombre Completo", row.get("Nombre", ""))),
                                str(row.get("PUESTO", row.get("Puesto", ""))),
                                str(row.get("Estatus", "Asistencia")),
                                str(row.get("Observaciones", "")),
                                persona_reporta.strip()
                            ])
                            
                        ws_historial.append_rows(filas_a_insertar)
                        st.success(f"¡Asistencia de **{sitio_seleccionado}** registrada exitosamente en Google Sheets!")
                    except Exception as e:
                        st.error(f"Error al escribir en Google Sheets: {type(e).__name__} - {str(e)}")
