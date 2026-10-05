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
        # Se busca la configuración de Google 
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif "google_credentials" in st.secrets:
            creds_dict = dict(st.secrets["google_credentials"])
        else:
            st.error("❌ No se encontraron credenciales de Google en st.secrets.")
            return None
        
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"❌ Error de autenticación en init_gspread_client: {type(e).__name__} - {str(e)}")
        return None

@st.cache_data(ttl=60)
def cargar_personal_desde_sheets(spreadsheet_id):
    """Obtiene los datos y el objeto worksheet."""
    gc = init_gspread_client()
    if not gc:
        return pd.DataFrame(), None
    
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.get_worksheet(0)
        datos = worksheet.get_all_records()
        df = pd.DataFrame(datos)
        
        # Limpieza: Reemplazar 'None', nulos y strings vacíos por espacio en blanco
        df = df.fillna("")
        df = df.replace(["None", "NaN", "nan"], "")
        
        return df, worksheet
    except Exception as e:
        st.error(f"❌ Error al leer la base de datos de Google Sheets: {type(e).__name__} - {str(e)}")
        return pd.DataFrame(), None

# --- INTERFAZ PRINCIPAL ---
st.title("📋 Control de Asistencia por Sitio")

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
    st.markdown("---")
    
    # Formatear la fecha para la columna
    col_fecha = f"{fecha_registro.day}/{fecha_registro.month}/{fecha_registro.year}"
    
    # Si la columna no existe en el origen, la creamos vacía
    if col_fecha not in df_personal.columns:
        df_personal[col_fecha] = ""
        
    # Filtro de sitio
    if "SITE" in df_personal.columns:
        df_sitio = df_personal[df_personal["SITE"] == sitio_seleccionado].copy()
    else:
        df_sitio = df_personal.copy()

    if df_sitio.empty:
        st.warning(f"No se encontró personal asignado al sitio **{sitio_seleccionado}**.")
    else:
        st.markdown(f"### Módulo de Captura Rápida — **{sitio_seleccionado}**")
        
        # Opciones de asistencia
        estatus_opciones = ["", "Asistencia", "Falta", "Vacaciones", "Incapacidad", "Descanso"]
        
        # 1. Crear un selector de empleado más amigable
        df_sitio["Info_Empleado"] = df_sitio["No_Empleado"].astype(str) + " - " + df_sitio["Nombre Completo"].astype(str)
        empleado_seleccionado = st.selectbox(
            "👤 Selecciona el Empleado a registrar:",
            options=["-- Selecciona un empleado --"] + df_sitio["Info_Empleado"].tolist()
        )

        if empleado_seleccionado != "-- Selecciona un empleado --":
            # Extraer el ID del empleado seleccionado
            num_empleado_actual = empleado_seleccionado.split(" - ")[0]
            
            # Buscar el registro exacto en el dataframe filtrado
            fila_empleado = df_sitio[df_sitio["No_Empleado"].astype(str) == num_empleado_actual].iloc[0]
            estatus_actual = fila_empleado.get(col_fecha, "")
            
            # Manejo de índice para el selectbox
            idx_estatus = 0
            if estatus_actual in estatus_opciones:
                idx_estatus = estatus_opciones.index(estatus_actual)
            
            # Tarjeta de registro individual
            with st.container(border=True):
                st.markdown(f"**Registrando a:** {empleado_seleccionado}")
                st.markdown(f"**Día a registrar:** {col_fecha}")
                
                nuevo_estatus = st.selectbox(
                    f"📝 Estatus para el {col_fecha}:",
                    options=estatus_opciones,
                    index=idx_estatus
                )
                
                col_btn1, col_btn2 = st.columns([1,3])
                with col_btn1:
                    if st.button("💾 Guardar Estatus", type="primary", use_container_width=True):
                        if not persona_reporta.strip():
                            st.error("⚠️ Falta la persona que valida.")
                        else:
                            with st.spinner("Sincronizando con Google Sheets..."):
                                try:
                                    col_id = "No_Empleado"
                                    # Encontrar la fila en el dataframe general
                                    match_idx = df_personal[df_personal[col_id].astype(str) == num_empleado_actual].index
                                    if not match_idx.empty:
                                        # Sobreescribir el valor
                                        df_personal.loc[match_idx[0], col_fecha] = nuevo_estatus
                                        
                                        # Preparar datos: reemplazar NaN/Null que se hayan colado al manipular Pandas
                                        df_personal = df_personal.fillna("")
                                        datos_a_subir = [df_personal.columns.values.tolist()] + df_personal.astype(str).values.tolist()
                                        
                                        worksheet.clear()
                                        worksheet.update(values=datos_a_subir, range_name="A1")
                                        
                                        st.cache_data.clear()
                                        st.success(f"✅ Se guardó '{nuevo_estatus}' para {empleado_seleccionado}.")
                                        st.rerun() # Refresca para mostrar el cambio
                                except Exception as e:
                                    st.error(f"Error al escribir en Google Sheets: {type(e).__name__} - {str(e)}")

        # 2. Vista de sólo lectura limpia
        st.markdown("---")
        st.markdown(f"#### 👁️ Vista general de {sitio_seleccionado}")
        
        # Ocultar la columna auxiliar y mostrar el grid bloqueado
        df_mostrar = df_sitio.drop(columns=["Info_Empleado"])
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
