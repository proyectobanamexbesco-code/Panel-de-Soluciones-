import datetime
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Control de Asistencia", layout="wide")

SITIOS_DISPONIBLES = ["MX10", "MX11", "MX12", "MX13"]
OPCIONES_ESTATUS = [
    "Asistencia",
    "Falta",
    "Incapacidad",
    "Vacaciones",
    "Día de descanso"
]

# --- CONEXIÓN CON GSPREAD ---
def obtener_cliente_gspread():
    """Autentica con la Service Account configurada en st.secrets."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    return gspread.authorize(creds)

def cargar_listado_maestro():
    """Lee el catálogo de personal desde 'Hoja 1' en Google Sheets."""
    try:
        client = obtener_cliente_gspread()
        sheet = client.open_by_key(st.secrets["SPREADSHEET_ID"]).worksheet("Hoja 1")
        datos = sheet.get_all_records()
        df = pd.DataFrame(datos)
        
        # Limpieza de datos
        df = df.dropna(subset=["No_Empleado"])
        df["No_Empleado"] = df["No_Empleado"].astype(str)
        return df
    except Exception as e:
        st.error(f"Error al leer la lista de personal de Google Sheets: {e}")
        return pd.DataFrame()

def guardar_registro_asistencia(df_nuevos_registros):
    """Escribe los nuevos registros en la pestaña 'Historial_Asistencia'."""
    try:
        client = obtener_cliente_gspread()
        doc = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        
        # Intentar obtener la pestaña de historial; si no existe, la crea
        try:
            hoja_historial = doc.worksheet("Historial_Asistencia")
        except gspread.exceptions.WorksheetNotFound:
            hoja_historial = doc.add_worksheet(title="Historial_Asistencia", rows="1000", cols="20")
            # Encabezados
            hoja_historial.append_row([
                "Fecha", "SITE", "No_Empleado", "Nombre Completo", 
                "PUESTO", "Estatus", "Observaciones", "Reportado_Por"
            ])

        # Convertir el DataFrame a lista de filas para anexar
        filas_a_insertar = df_nuevos_registros.values.tolist()
        hoja_historial.append_rows(filas_a_insertar)
        return True
    except Exception as e:
        st.error(f"Error al escribir en Google Sheets: {e}")
        return False

# --- INTERFAZ STREAMLIT ---
st.title("📋 Control de Asistencia por Sitio")

# Controles de encabezado
col_sitio, col_fecha, col_reporta = st.columns([1, 1, 1.5])

with col_sitio:
    sitio_seleccionado = st.selectbox("🏢 SITE:", options=SITIOS_DISPONIBLES)

with col_fecha:
    fecha_seleccionada = st.date_input("📅 Fecha a registrar:", datetime.date.today())

with col_reporta:
    reportado_por = st.text_input("✍️ Persona que reporta / Valida:", placeholder="Ej. Ing. Gerardo Méndez")

# Carga de personal
df_maestro = cargar_listado_maestro()

if not df_maestro.empty:
    # Filtrar por el SITE elegido
    df_sitio = df_maestro[df_maestro["SITE"] == sitio_seleccionado].copy()

    if df_sitio.empty:
        st.warning(f"No se encontró personal asignado al SITE **{sitio_seleccionado}**.")
    else:
        st.markdown(f"### Pase de Lista — **{sitio_seleccionado}** ({fecha_seleccionada.strftime('%d/%m/%Y')})")
        
        # Opciones por defecto para la captura
        df_sitio["Estatus"] = "Asistencia"
        df_sitio["Observaciones"] = ""

        # Tabla interactiva para modificar asistencia y observaciones
        df_editado = st.data_editor(
            df_sitio[["No_Empleado", "Nombre Completo", "PUESTO", "Estatus", "Observaciones"]],
            column_config={
                "No_Empleado": st.column_config.TextColumn("No. Empleado", disabled=True),
                "Nombre Completo": st.column_config.TextColumn("Nombre Completo", disabled=True),
                "PUESTO": st.column_config.TextColumn("Puesto", disabled=True),
                "Estatus": st.column_config.SelectboxColumn(
                    "Estatus",
                    options=OPCIONES_ESTATUS,
                    required=True
                ),
                "Observaciones": st.column_config.TextColumn("Observaciones", width="large")
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{sitio_seleccionado}_{fecha_seleccionada}"
        )

        # Botón para enviar datos directamente a Google Sheets
        if st.button("💾 Guardar y Sincronizar en Google Sheets", type="primary"):
            if not reportado_por.strip():
                st.error("⚠️ Por favor ingresa el nombre de la persona que reporta antes de guardar.")
            else:
                # Prepara el bloque de filas a enviar
                df_para_guardar = pd.DataFrame({
                    "Fecha": fecha_seleccionada.strftime("%Y-%m-%d"),
                    "SITE": sitio_seleccionado,
                    "No_Empleado": df_editado["No_Empleado"],
                    "Nombre Completo": df_editado["Nombre Completo"],
                    "PUESTO": df_editado["PUESTO"],
                    "Estatus": df_editado["Estatus"],
                    "Observaciones": df_editado["Observaciones"],
                    "Reportado_Por": reportado_por.strip()
                })

                with st.spinner("Enviando registros a Google Sheets..."):
                    exito = guardar_registro_asistencia(df_para_guardar)
                    if exito:
                        st.success(f"¡Asistencia de **{sitio_seleccionado}** registrada correctamente en Google Sheets!")
