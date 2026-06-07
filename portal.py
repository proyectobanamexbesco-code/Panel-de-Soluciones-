import streamlit as st

# Configuración global del portal
st.set_page_config(
    page_title="Portal Grupo Besco",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Portal de Soluciones Operativas")
st.markdown("---")

st.markdown("### Bienvenido al sistema central")
st.markdown("Utiliza el **menú lateral izquierdo** para navegar entre las diferentes herramientas disponibles:")

col1, col2 = st.columns(2)

with col1:
    st.info("**📄 Cotizaciones:** Cálculo de presupuestos basados en preciario.")
    st.info("**📸 Reporte General:** Generación de evidencia fotográfica.")

with col2:
    st.success("**📑 Módulo Nestlé:** Levantamiento de equipos y análisis IA.")
    st.warning("**🚀 Próximas Apps:** Espacio reservado para integraciones futuras.")

st.divider()
st.caption("👈 Expande la barra lateral si estás en un dispositivo móvil para acceder a los módulos.")
