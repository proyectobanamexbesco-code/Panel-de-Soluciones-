import os
import streamlit as st
from dataclasses import dataclass
from typing import List

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "Portal Grupo Besco"
PAGE_ICON = "🏗️"
LAYOUT = "centered"

@dataclass
class PortalModule:
    path: str
    label: str
    icon: str
    description: str
    enabled: bool = True
    status: str = "Activo"

# =========================================================
# MÓDULOS DEL PORTAL
# =========================================================
MODULES: List[PortalModule] = [
    PortalModule(
        path="pages/01_Cotizaciones.py",
        label="Cotizador",
        icon="📄",
        description="Cálculo de presupuestos y generación de PDFs.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/02_Reporte_General.py",
        label="Reporte Fotográfico",
        icon="📸",
        description="Captura de evidencia fotográfica general.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/03_Nestle.py",
        label="Módulo Nestlé",
        icon="📑",
        description="Levantamiento de equipos, análisis y correo automático.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/04_Proximas_Apps.py",
        label="Próximas Apps",
        icon="🚀",
        description="Espacio para nuevas herramientas operativas.",
        enabled=True,
        status="Próximamente",
    ),
    PortalModule(
        path="pages/05_App_Vehicular.py",
        label="App Vehicular",
        icon="🚗",
        description="Reporte vehicular con evidencias y PDF.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/06_Reporte_Fotografico_Contratos.py",
        label="Reporte Fotográfico por Contrato",
        icon="📷",
        description="Reporte fotográfico configurable por contrato, alcance y envío.",
        enabled=True,
        status="Activo",
    ),
]

# =========================================================
# CONFIGURAR PÁGINA
# =========================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

# =========================================================
# ESTILOS OSCUROS (TEMA EJECUTIVO) Y BOTONES AZULES
# =========================================================
def apply_dark_styles() -> None:
    st.markdown(
        """
        <style>
        /* Forzar fondo oscuro en la aplicación para el tema ejecutivo */
        .stApp {
            background-color: #0B1421 !important;
        }
        
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        .block-container {
            padding-top: 3rem; 
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            max-width: 760px;
        }

        /* Títulos con colores claros para contrastar el fondo oscuro */
        .portal-title {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 800;
            color: #FFFFFF;
            margin-bottom: 0.2rem;
            margin-top: 1rem;
        }

        .portal-subtitle {
            text-align: center;
            font-size: 0.95rem;
            color: #94A3B8;
            margin-bottom: 1.5rem;
        }

        /* Caja de resumen estilizada en tono oscuro */
        .summary-box {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 2rem;
            font-size: 0.9rem;
            color: #E2E8F0;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* == CSS PARA LOS BOTONES AZULES IDÉNTICOS A LA IMAGEN == */
        div.stButton > button {
            background-color: #5B9BD5 !important;
            color: white !important;
            border: 2px solid #1F497D !important;
            border-radius: 12px !important;
            width: 100% !important;
            height: 85px !important; 
            font-weight: 700 !important;
            font-size: 16px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            white-space: normal !important;
            line-height: 1.2 !important;
            margin-bottom: 5px;
            transition: all 0.2s ease;
        }
        
        div.stButton > button:hover {
            background-color: #41719C !important;
            border: 2px solid #0F243E !important;
            transform: translateY(-2px);
        }

        div.stButton > button:disabled {
            background-color: #475569 !important;
            border: 2px solid #334155 !important;
            color: #94A3B8 !important;
            box-shadow: none;
            transform: none;
        }

        /* Descripciones de los módulos adaptadas al modo oscuro */
        .module-description {
            color: #94A3B8;
            font-size: 0.8rem;
            text-align: center;
            margin-top: -10px;
            margin-bottom: 25px;
            padding: 0 5px;
            min-height: 40px; 
        }

        .footer-text {
            text-align: center;
            color: #64748B;
            font-size: 0.8rem;
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def render_header() -> None:
    # 1. Agregar el Logo proporcionado centrado antes del título
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists("logo besco 2026.jpeg"):
            st.image("logo besco 2026.jpeg", use_container_width=True)

    # 2. Renderizar los Títulos
    st.markdown(
        """
        <div class="portal-title">🏗️ Portal Grupo Besco</div>
        <div class="portal-subtitle">
            Acceso rápido a herramientas operativas desde celular o escritorio.
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_summary(modules: List[PortalModule]) -> None:
    total_modules = len(modules)
    active_modules = len([m for m in modules if m.enabled and m.status == "Activo"])

    st.markdown(
        f"""
        <div class="summary-box">
            <strong>Módulos disponibles:</strong> {active_modules} de {total_modules}<br>
            <strong>Objetivo:</strong> centralizar herramientas operativas en una sola entrada.
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_modules(modules: List[PortalModule]) -> None:
    col1, col2 = st.columns(2)
    
    for i, module in enumerate(modules):
        target_col = col1 if i % 2 == 0 else col2
        
        with target_col:
            if module.enabled:
                if st.button(f"{module.icon} {module.label}", key=f"btn_{i}", use_container_width=True):
                    st.switch_page(module.path)
            else:
                st.button(f"{module.icon} {module.label}", key=f"btn_{i}", disabled=True, use_container_width=True)
            
            status_html = f"<br><span style='color:#F59E0B; font-weight:bold;'>({module.status})</span>" if module.status != "Activo" else ""
            st.markdown(f"<div class='module-description'>{module.description}{status_html}</div>", unsafe_allow_html=True)

def render_footer() -> None:
    st.divider()
    st.markdown(
        """
        <div class="footer-text">
            Sistema Operativo - Grupo Besco
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# MAIN
# =========================================================
def main() -> None:
    apply_dark_styles()
    render_header()
    render_summary(MODULES)
    render_modules(MODULES)
    render_footer()

if __name__ == "__main__":
    main()
