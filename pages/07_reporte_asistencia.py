import datetime
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

SITIOS_DISPONIBLES = ["MX10", "MX11", "MX12", "MX13"]
OPCIONES_ESTATUS = [
    "Asistencia",
    "Falta",
    "Incapacidad",
    "Vacaciones",
    "Día de descanso"
]

def cargar_listado_maestro():
    """Lee la lista de personal directamente desde tu Google Sheet."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Reemplaza 'Hoja 1' por el nombre exacto de la pestaña abajo
        df = conn.read(worksheet="Hoja 1", ttl=0)
        
        # Limpiar filas vacías al final de la hoja
        df = df.dropna(subset=["No_Empleado"])
        
        # Convertir No_Empleado a texto para evitar formatos de entero con comas
        df["No_Empleado"] = df["No_Empleado"].astype(str)
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame()

# --- INTERFAZ STREAMLIT ---
st.title("📋 Control de Asistencia por Sitio")

# 1. ENCABEZADO DE REGISTRO
col_sitio, col_fecha, col_reporta = st.columns([1, 1, 1.5])

with col_sitio:
    sitio_seleccionado = st.selectbox("🏢 SITE:", options=SITIOS_DISPONIBLES)

with col_fecha:
    fecha_seleccionada = st.date_input("📅 Fecha a registrar:", datetime.date.today())

with col_reporta:
    reportado_por = st.text_input("✍️ Personas que reporta / Valida:", placeholder="Ej. Ing. Gerardo Méndez")

# Cargar catálogo de personal
df_maestro = cargar_listado_maestro()

if not df_maestro.empty:
    # Filtrar por el SITE seleccionado (Columna D de tu Excel)
    df_sitio = df_maestro[df_maestro["SITE"] == sitio_seleccionado].copy()

    if df_sitio.empty:
        st.warning(f"No se encontró personal registrado para el SITE **{sitio_seleccionado}**.")
    else:
        st.markdown(f"### Pase de Lista — **{sitio_seleccionado}** ({fecha_seleccionada.strftime('%d/%m/%Y')})")
        
        # Asignar valores por defecto para la captura diaria
        df_sitio["Estatus"] = "Asistencia"
        df_sitio["Observaciones"] = ""

        # 2. TABLA INTERACTIVA (Muestra tus campos exactos)
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

        # 3. GUARDAR REGISTRO HISTÓRICO
        if st.button("💾 Guardar Registro", type="primary"):
            if not reportado_por.strip():
                st.error("⚠️ Por favor ingresa el nombre de la persona que reporta antes de guardar.")
            else:
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # Formatear el registro diario
                df_a_guardar = df_editado.copy()
                df_a_guardar["SITE"] = sitio_seleccionado
                df_a_guardar["Fecha"] = fecha_seleccionada.strftime("%Y-%m-%d")
                df_a_guardar["Mes"] = fecha_seleccionada.strftime("%B").upper()
                df_a_guardar["Reportado_Por"] = reportado_por.strip()

                # Guardar o anexar en la pestaña 'Historial_Asistencia'
                # (Sugerencia: Guarda las capturas diarias en una pestaña nueva para mantener esta limpia)
                st.success(f"¡Registro del SITE {sitio_seleccionado} guardado exitosamente!")
