import datetime
import pandas as pd
import streamlit as st
# Si usas st.connection para Google Sheets real:
# from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Asistencia por Sitio", layout="wide")

SITIOS_DISPONIBLES = ["MX10", "MX11", "MX12", "MX13"]
OPCIONES_ESTATUS = [
    "Asistencia",
    "Falta",
    "Incapacidad",
    "Vacaciones",
    "Día de descanso"
]

def cargar_listado_maestro():
    """Simula o lee el catálogo de personal desde Google Sheets."""
    # En producción:
    # conn = st.connection("gsheets", type=GSheetsConnection)
    # return conn.read(worksheet="Personal", ttl=0)
    
    # Ejemplo de base de datos general con asignación de Sitio
    return pd.DataFrame({
        "ID": ["EMP-001", "EMP-002", "EMP-003", "EMP-004", "EMP-005", "EMP-006"],
        "Nombre": [
            "Carlos Gómez", 
            "María Rodríguez", 
            "Juan Pérez", 
            "Ana Martínez", 
            "Luis Hernández",
            "Pedro Sánchez"
        ],
        "Sitio": ["MX10", "MX10", "MX11", "MX11", "MX12", "MX13"],
        "Puesto": ["Técnico HVAC", "Técnico HVAC", "Líder de Cuadrilla", "Auxiliar", "Técnico HVAC", "Técnico HVAC"]
    })

# Inicializar historial en session_state si no existe
if "historial_asistencia" not in st.session_state:
    st.session_state["historial_asistencia"] = pd.DataFrame(columns=[
        "Sitio", "ID", "Nombre", "Puesto", "Fecha", "Año", "Mes", "Estatus", "Observaciones"
    ])

st.title("📋 Control de Asistencia por Sitio")

tab1, tab2 = st.tabs(["📝 Registro Diario", "📊 Consulta Mensual por Sitio"])

# ==========================================
# TAB 1: REGISTRO DIARIO (PRE-SITIO)
# ==========================================
with tab1:
    st.subheader("Configuración de Pase de Lista")
    
    # 1. PRE-SITIO Y FECHA DE REGISTRO
    col_sitio, col_fecha = st.columns([1, 1])
    
    with col_sitio:
        sitio_seleccionado = st.selectbox(
            "🏢 Selecciona el Sitio / Plaza:",
            options=SITIOS_DISPONIBLES,
            index=0,
            help="Filtrará únicamente al personal asignado a este sitio."
        )
    
    with col_fecha:
        fecha_seleccionada = st.date_input("📅 Fecha a registrar:", datetime.date.today())

    # Cargar y filtrar plantilla por sitio seleccionado
    df_maestro_total = cargar_listado_maestro()
    df_personal_sitio = df_maestro_total[df_maestro_total["Sitio"] == sitio_seleccionado].copy()

    if df_personal_sitio.empty:
        st.warning(f"No hay personal registrado para el sitio **{sitio_seleccionado}** en el catálogo.")
    else:
        st.markdown(f"### Pase de Lista — **{sitio_seleccionado}** ({fecha_seleccionada.strftime('%d/%m/%Y')})")
        
        # Asignar valores por defecto para la captura
        df_personal_sitio["Estatus"] = "Asistencia"
        df_personal_sitio["Observaciones"] = ""

        # Formatos de fecha y periodo
        fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
        anio_val = fecha_seleccionada.year
        mes_val = fecha_seleccionada.strftime("%Y-%m")

        # 2. TABLA INTERACTIVA DE ASISTENCIA FILTRADA
        df_editado = st.data_editor(
            df_personal_sitio[["ID", "Nombre", "Puesto", "Estatus", "Observaciones"]],
            column_config={
                "ID": st.column_config.TextColumn("ID", disabled=True),
                "Nombre": st.column_config.TextColumn("Nombre del Colaborador", disabled=True),
                "Puesto": st.column_config.TextColumn("Puesto", disabled=True),
                "Estatus": st.column_config.SelectboxColumn(
                    "Estatus",
                    options=OPCIONES_ESTATUS,
                    required=True
                ),
                "Observaciones": st.column_config.TextColumn("Comentarios / Motivo", width="large")
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{sitio_seleccionado}_{fecha_str}"
        )

        # 3. GUARDADO Y PERSISTENCIA
        if st.button(f"💾 Guardar Registro ({sitio_seleccionado})", type="primary"):
            df_a_guardar = df_editado.copy()
            df_a_guardar["Sitio"] = sitio_seleccionado
            df_a_guardar["Fecha"] = fecha_str
            df_a_guardar["Año"] = anio_val
            df_a_guardar["Mes"] = mes_val

            # Orden exacto de columnas para almacenamiento
            columnas_ordenadas = ["Sitio", "ID", "Nombre", "Puesto", "Fecha", "Año", "Mes", "Estatus", "Observaciones"]
            df_a_guardar = df_a_guardar[columnas_ordenadas]

            # Reemplazar únicamente los registros previos que coincidan en MISMO SITIO Y MISMA FECHA
            historial_actual = st.session_state["historial_asistencia"]
            
            condicion_duplicado = (historial_actual["Sitio"] == sitio_seleccionado) & (historial_actual["Fecha"] == fecha_str)
            historial_filtrado = historial_actual[~condicion_duplicado]

            # Concatenar el nuevo bloque guardado
            st.session_state["historial_asistencia"] = pd.concat([historial_filtrado, df_a_guardar], ignore_index=True)

            # EN PRODUCCIÓN (Google Sheets):
            # conn.append(worksheet="Historial_Asistencia", data=df_a_guardar)

            st.success(f"¡Asistencia de **{sitio_seleccionado}** para el día {fecha_str} guardada con éxito!")

# ==========================================
# TAB 2: CONSULTA Y RESUMEN MENSUAL POR SITIO
# ==========================================
with tab2:
    st.subheader("📊 Reportes y Consolidado")
    
    df_historial = st.session_state["historial_asistencia"]

    if df_historial.empty:
        st.info("Sin registros acumulados por el momento.")
    else:
        col_s_filtro, col_m_filtro = st.columns(2)
        
        with col_s_filtro:
            filtro_sitio_consulta = st.selectbox("Filtrar por Sitio", ["Todos"] + SITIOS_DISPONIBLES)
        
        with col_m_filtro:
            meses_disp = sorted(df_historial["Mes"].unique().tolist(), reverse=True)
            filtro_mes_consulta = st.selectbox("Filtrar por Mes", meses_disp)

        # Filtrado de la vista
        df_filtrado = df_historial[df_historial["Mes"] == filtro_mes_consulta]
        if filtro_sitio_consulta != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Sitio"] == filtro_sitio_consulta]

        st.markdown(f"#### Resumen de Incidencias (`{filtro_mes_consulta}`)")

        # Matriz dinámica resumida por persona
        if not df_filtrado.empty:
            matriz = pd.pivot_table(
                df_filtrado,
                index=["Sitio", "ID", "Nombre", "Puesto"],
                columns="Estatus",
                aggfunc="size",
                fill_value=0
            ).reset_index()

            st.dataframe(matriz, use_container_width=True, hide_index=True)
        else:
            st.warning("No hay información registrada para los filtros seleccionados.")
