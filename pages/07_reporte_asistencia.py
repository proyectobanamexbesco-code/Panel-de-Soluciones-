import datetime
import pandas as pd
import streamlit as st
# Si usas st.connection para Google Sheets:
# from streamlit_gsheets import GSheetsConnection

def mostrar_modulo_asistencia():
    st.title("📋 Reporte Diarios de Asistencia")
    st.write("Selecciona la fecha y valida la asistencia del personal registrado en Google Sheets.")

    # 1. Controles Superiores (Fecha y Selección)
    col_fecha, col_filtro = st.columns([1, 2])
    
    with col_fecha:
        fecha_reporte = st.date_input("Fecha del Reporte", datetime.date.today())
    
    # --- SIMULACIÓN DE DATOS O CONEXIÓN A GOOGLE SHEETS ---
    # Para conectar con Google Sheets real:
    # conn = st.connection("gsheets", type=GSheetsConnection)
    # df_personal = conn.read(worksheet="Personal", ttl=0)
    
    # Datos de prueba (Sustituir por la lectura de tu Google Sheet)
    if "df_asistencia" not in st.state_dict():
        datos_ejemplo = {
            "ID": ["EMP-001", "EMP-002", "EMP-003", "EMP-004", "EMP-005"],
            "Nombre Completo": [
                "Carlos Gómez",
                "María Rodríguez",
                "Juan Pérez",
                "Ana Martínez",
                "Luis Hernández"
            ],
            "Puesto / Área": ["Técnico HVAC", "Técnico HVAC", "Líder de Cuadrilla", "Auxiliar", "Técnico HVAC"],
            "Estatus": ["Asistencia", "Asistencia", "Asistencia", "Día de descanso", "Asistencia"],
            "Observaciones": ["", "", "", "", ""]
        }
        st.session_state["df_asistencia"] = pd.DataFrame(datos_ejemplo)

    df_base = st.session_state["df_asistencia"].copy()

    # Opciones válidas de estatus
    opciones_estatus = [
        "Asistencia",
        "Falta",
        "Incapacidad",
        "Vacaciones",
        "Día de descanso"
    ]

    # 2. Configuración de la Tabla Interactiva
    st.subheader(f"Pase de Lista - {fecha_reporte.strftime('%d/%m/%Y')}")
    
    df_editado = st.data_editor(
        df_base,
        column_config={
            "ID": st.column_config.TextColumn("ID", disabled=True),
            "Nombre Completo": st.column_config.TextColumn("Nombre del Colaborador", disabled=True),
            "Puesto / Área": st.column_config.TextColumn("Puesto", disabled=True),
            "Estatus": st.column_config.SelectboxColumn(
                "Estatus de Asistencia",
                help="Selecciona la condición del trabajador hoy",
                options=opciones_estatus,
                required=True
            ),
            "Observaciones": st.column_config.TextColumn("Comentarios / Motivo", width="large")
        },
        hide_index=True,
        use_container_width=True,
        key="editor_asistencia"
    )

    # 3. Resumen Rápido (Métricas de Asistencia)
    st.markdown("---")
    st.subheader("📊 Resumen de la Jornada")
    
    conteo = df_editado["Estatus"].value_counts()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Asistencias", conteo.get("Asistencia", 0))
    col2.metric("Faltas", conteo.get("Falta", 0))
    col3.metric("Incapacidades", conteo.get("Incapacidad", 0))
    col4.metric("Vacaciones", conteo.get("Vacaciones", 0))
    col5.metric("Descansos", conteo.get("Día de descanso", 0))

    # 4. Guardar y Sincronizar
    st.markdown("---")
    col_guardar, col_info = st.columns([1, 3])

    with col_guardar:
        if st.button("💾 Guardar en Google Sheets", type="primary"):
            # Añadir la fecha al dataframe consolidado antes de enviar
            df_para_guardar = df_editado.copy()
            df_para_guardar.insert(0, "Fecha", fecha_reporte.strftime("%Y-%m-%d"))
            
            # --- CÓDIGO PARA GUARDAR EN GOOGLE SHEETS ---
            # conn.update(worksheet="Historial_Asistencia", data=df_para_guardar)
            
            st.session_state["df_asistencia"] = df_editado
            st.success("¡Reporte de asistencia guardado exitosamente en Google Sheets!")

# Ejecutar módulo
if __name__ == "__main__":
    mostrar_modulo_asistencia()
