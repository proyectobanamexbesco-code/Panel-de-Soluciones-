import streamlit as st

# Configuración global del portal
st.set_page_config(
    page_title="Portal Grupo Besco",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Portal de Soluciones Operativas")
st.markdown("---")

st.markdown("### Selecciona una herramienta para comenzar:")

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/01_Cotizaciones.py", label="Ir al Cotizador", icon="📄")
    st.info("Cálculo de presupuestos basados en preciario.")
    st.write("") # Espaciador
    
    st.page_link("pages/02_Reporte_General.py", label="Ir a Reporte Fotográfico", icon="📸")
    st.info("Generación de evidencia fotográfica general.")

with col2:
    st.page_link("pages/03_Nestle.py", label="Ir al Módulo Nestlé", icon="📑")
    st.success("Levantamiento de equipos y análisis de datos.")
    st.write("") # Espaciador
    
    st.page_link("pages/04_Proximas_Apps.py", label="Ir a Próximas Apps", icon="🚀")
    st.warning("Espacio reservado para integraciones futuras.")

st.divider()
st.caption("Sistema Operativo - Grupo Besco")
