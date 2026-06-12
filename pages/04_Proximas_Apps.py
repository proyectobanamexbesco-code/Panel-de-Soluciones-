import streamlit as st

# ---------------------------------------------------
# CONFIGURACIÓN GENERAL
# ---------------------------------------------------
st.set_page_config(
    page_title="Próximas Apps",
    page_icon="🚀",
    layout="wide"
)

# ---------------------------------------------------
# TÍTULO
# ---------------------------------------------------
st.title("🚀 Próximas Apps en Desarrollo")
st.markdown("---")

st.write(
    "En esta sección se muestran las aplicaciones en desarrollo dentro del **Panel de Soluciones**."
)

# ---------------------------------------------------
# APP 1: REPORTE VEHICULAR
# ---------------------------------------------------
st.subheader("📋 App de Reporte Vehicular")

st.write("""
Aplicación para control y reporte de unidades vehiculares con evidencia fotográfica.

### ✅ Funcionalidades:
- Selección automática por **placa**
- Autollenado de:
  - Oficina
  - Modelo
  - Responsable
  - Puesto
- Captura de evidencias:
  - Frente
  - Atrás
  - Costados
  - Tablero
  - Asientos
  - Documentos
- Observaciones opcionales
- Generación automática de **PDF**
- Descarga del reporte
- Envío por correo

""")

# BOTONES
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Abrir App Vehicular"):
        st.info("Aquí puedes integrar la navegación directa a la app cuando la despliegues.")

with col2:
    st.link_button(
        "🔗 Ver Repositorio",
        "https://github.com/proyectobanamexbesco-code/Panel-de-Soluciones-"
    )

st.markdown("---")

# ---------------------------------------------------
# SECCIÓN FUTURAS APPS
# ---------------------------------------------------
st.subheader("🔮 Otras Apps en Camino")

apps = [
    {
        "nombre": "📦 Control de Inventarios",
        "desc": "Gestión de insumos y herramientas con reportes automáticos."
    },
    {
        "nombre": "📊 Dashboard Operativo",
        "desc": "Visualización de KPIs por región, oficina y desempeño."
    },
    {
        "nombre": "🧾 Generador de Reportes",
        "desc": "Sistema automatizado de reportes PDF para operaciones."
    }
]

for app in apps:
    st.markdown(f"### {app['nombre']}")
    st.write(app["desc"])
    st.markdown("---")

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------
st.markdown("### 🏢 Panel de Soluciones BESCo")
st.caption("Desarrollado para optimización de procesos y control operativo.")
``
