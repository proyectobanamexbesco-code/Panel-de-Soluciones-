import datetime
import pandas as pd
import streamlit as st
# De necesitar la conexión real con Google Sheets:
# from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Control de Asistencia", layout="wide")

# --- OPCIONES DE ESTATUS VÁLIDOS ---
OPCIONES_ESTATUS = [
    "Asistencia",
    "Falta",
    "Incapacidad",
    "Vacaciones",
    "Día de descanso"
]

def cargar_listado_maestro():
    """Simula o lee la pestaña de 'Personal' en Google Sheets"""
    # En producción:
    # conn = st.connection("gsheets", type=GSheetsConnection)
    # return conn.read(worksheet="Personal", ttl=0)
    return pd.DataFrame({
        "ID": ["EMP-001", "EMP-002", "EMP-003", "EMP-004"],
        "Nombre": ["Carlos Gómez", "María Rodríguez", "Juan Pérez", "Ana Martínez"],
        "Puesto": ["Técnico HVAC", "Técnico HVAC", "Líder de Cuadrilla", "Auxiliar"]
    })

# Carga inicial en session_state para mantener la persistencia durante la sesión
if "historial_asistencia" not in st.session_state:
    # DataFrame vacío que simula la pestaña 'Historial_Asistencia' en Google Sheets
    st.session_state["historial_asistencia"] = pd.DataFrame(columns=[
        "ID", "Nombre", "Puesto", "Fecha", "Año", "Mes", "Estatus", "Observaciones"
    ])

# --- INTERFAZ PRINCIPAL ---
st.title("📋 Gestión Histórica de Asistencia")

tab1, tab2 = st.tabs(["📝 Registro Diario", "📊 Consulta y Resumen Mensual"])

# ==========================================
# TAB 1: REGISTRO DIARIO
# ==========================================
with tab1:
    st.subheader("Captura de Pase de Lista")
    
    col_f, col_info = st.columns([1, 2])
    with col_f:
        fecha_seleccionada = st.date_input("Fecha a registrar", datetime.date.today())
    
    # Formatear la fecha
    fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")
    anio_val = fecha_seleccionada.year
    # Guardamos el mes en texto (ej. "2026-08") o en número según prefieras
    mes_val = fecha_seleccionada.strftime("%Y-%m") 

    df_maestro = cargar_listado_maestro()
    
    # Preparamos la plantilla del día
    df_dia = df_maestro.copy()
    df_dia["Estatus"] = "Asistencia"  # Valor por defecto
    df_dia["Observaciones"] = ""

    st.info(f"Registrando asistencia para el día: **{fecha_seleccionada.strftime('%d/%m/%Y')}**")

    # Tabla interactiva para la edición rápida del día
    df_editado = st.data_editor(
        df_dia,
        column_config={
            "ID": st.column_config.TextColumn("ID", disabled=True),
            "Nombre": st.column_config.TextColumn("Nombre", disabled=True),
            "Puesto": st.column_config.TextColumn("Puesto", disabled=True),
            "Estatus": st.column_config.SelectboxColumn(
                "Estatus",
                options=OPCIONES_ESTATUS,
                required=True
            ),
            "Observaciones": st.column_config.TextColumn("Observaciones / Motivo", width="large")
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_{fecha_str}"
    )

    if st.button("💾 Guardar Registro del Día", type="primary"):
        # Construir el bloque de datos con metadatos de tiempo
        df_a_guardar = df_editado.copy()
        df_a_guardar["Fecha"] = fecha_str
        df_a_guardar["Año"] = anio_val
        df_a_guardar["Mes"] = mes_val

        # Reordenar columnas para el historial
        columnas_ordenadas = ["ID", "Nombre", "Puesto", "Fecha", "Año", "Mes", "Estatus", "Observaciones"]
        df_a_guardar = df_a_guardar[columnas_ordenadas]

        # --- LÓGICA DE SINK/GUARDADO EN HISTORIAL ---
        historial_actual = st.session_state["historial_asistencia"]
        
        # Eliminar registros previos de la misma fecha si re-guardan para evitar duplicados del mismo día
        historial_filtrado = historial_actual[historial_actual["Fecha"] != fecha_str]
        
        # Concatenar el nuevo día al historial
        st.session_state["historial_asistencia"] = pd.concat([historial_filtrado, df_a_guardar], ignore_index=True)

        # SI USAS GOOGLE SHEETS EN PRODUCCIÓN:
        # conn.append(worksheet="Historial_Asistencia", data=df_a_guardar)

        st.success(f"¡Asistencia del día {fecha_str} asentada correctamente en el historial!")

# ==========================================
# TAB 2: CONSULTA Y RESUMEN MENSUAL
# ==========================================
with tab2:
    st.subheader("📊 Historial y Consolidado Mensual")
    
    df_historial = st.session_state["historial_asistencia"]

    if df_historial.empty:
        st.warning("Aún no hay registros guardados en el historial. Captura un día en la pestaña 'Registro Diario'.")
    else:
        # Filtros de búsqueda por mes y empleado
        meses_disponibles = sorted(df_historial["Mes"].unique().tolist(), reverse=True)
        
        col_m, col_e = st.columns(2)
        with col_m:
            mes_filtro = st.selectbox("Selecciona el Mes a consultar", meses_disponibles)
        
        # Filtrar por mes
        df_mes = df_historial[df_historial["Mes"] == mes_filtro]

        st.markdown(f"### Acumulado del Mes (`{mes_filtro}`)")

        # 1. Tabla Dinámica / Pivot Table: Conteo de Incidencias por Persona
        matriz_resumen = pd.pivot_table(
            df_mes,
            index=["ID", "Nombre", "Puesto"],
            columns="Estatus",
            aggfunc="size",
            fill_value=0
        ).reset_index()

        # Asegurar que todas las columnas de estatus existan en el resumen
        for estatus in OPCIONES_ESTATUS:
            if estatus not in matriz_resumen.columns:
                matriz_resumen[estatus] = 0

        st.dataframe(matriz_resumen, use_container_width=True, hide_index=True)

        # 2. Desglose detallado día por día
        with st.expander("🔍 Ver desglose diario detallado del mes"):
            st.dataframe(df_mes.sort_values(by=["Fecha", "Nombre"]), use_container_width=True, hide_index=True)
