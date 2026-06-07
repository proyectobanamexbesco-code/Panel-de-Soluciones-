import streamlit as st

# Configuración global del portal
st.set_page_config(
    page_title="Portal Grupo Besco",
    page_icon="🏗️",
    layout="wide"
)

# --- INYECCIÓN DE CSS PARA DISEÑO ---
st.markdown("""
<style>
/* Diseño del botón gigante Azul Besco */
[data-testid="stPageLink-NavLink"] {
    background-color: #1E3A5F !important; /* Azul corporativo de Besco */
    padding: 25px !important;
    border-radius: 12px !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    width: 100% !important;
    text-decoration: none !important;
}

/* Efecto hover (al pasar el mouse) */
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #284B7A !important;
    box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    transform: translateY(-2px);
}

/* Texto e ícono en blanco y grandes */
[data-testid="stPageLink-NavLink"] p {
    color: white !important;
    font-size: 22px !important;
    font-weight: bold !important;
    margin: 0 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Portal de Soluciones Operativas")
st.markdown("---")

st.markdown("### Selecciona una herramienta para comenzar:")
st.write("") # Espaciador

col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/01_Cotizaciones.py", label="Ir al Cotizador", icon="📄")
    st.markdown("<p style='text-align: center; color: #666; font-size: 15px;'>Cálculo de presupuestos basados en preciario. Genera PDFs listos para el cliente.</p>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    st.page_link("pages/02_Reporte_General.py", label="Ir a Reporte Fotográfico", icon="📸")
    st.markdown("<p style='text-align: center; color: #666; font-size: 15px;'>Generación de evidencia fotográfica general. Captura el antes y después del servicio.</p>", unsafe_allow_html=True)

with col2:
    st.page_link("pages/03_Nestle.py", label="Ir al Módulo Nestlé", icon="📑")
    st.markdown("<p style='text-align: center; color: #666; font-size: 15px;'>Levantamiento de equipos y análisis de datos con IA y envío de correo automático.</p>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    st.page_link("pages/04_Proximas_Apps.py", label="Ir a Próximas Apps", icon="🚀")
    st.markdown("<p style='text-align: center; color: #666; font-size: 15px;'>Espacio reservado para integraciones futuras y nuevas herramientas operativas.</p>", unsafe_allow_html=True)

st.divider()
st.caption("Sistema Operativo - Grupo Besco")
