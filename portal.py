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
# ESTILOS LIGEROS PARA CELULAR Y BOTONES AZULES (CUADRÍCULA)
# =========================================================
def apply_light_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            max-width: 760px;
        }

        .portal-title {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 800;
            color: #1E3A5F;
            margin-bottom: 0.2rem;
        }

        .portal-subtitle {
            text-align: center;
            font-size: 0.95rem;
            color: #5B6573;
            margin-bottom: 1rem;
        }

        .summary-box {
            background-color: #F7F9FC;
            border: 1px solid #D9E2EC;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 2rem;
            font-size: 0.9rem;
            color: #334E68;
            text-align: center;
        }

        /* == CSS PARA LOS BOTONES IDÉNTICOS A LA IMAGEN == */
        div.stButton > button {
            background-color: #5B9BD5 !important;
            color: white !important;
            border: 2px solid #1F497D !important;
            border-radius: 12px !important;
            width: 100% !important;
            height: 85px !important; /* Altura para hacerlos rectangulares */
            font-weight: 700 !important;
            font-size: 16px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            white-space: normal !important;
            line-height: 1.2 !important;
            margin-bottom: 5px;
        }
        
        div.stButton > button:hover {
            background-color: #41719C !important;
            border: 2px solid #0F243E !important;
        }

        div.stButton > button:disabled {
            background-color: #A6A6A6 !important;
            border: 2px solid #7F7F7F !important;
            color: #F0F0F0 !important;
        }

        .module-description {
            color: #5B6573;
            font-size: 0.8rem;
            text-align: center;
            margin-top: -10px;
            margin-bottom: 25px;
            padding: 0 5px;
            min-height: 40px; /* Alinea la cuadrícula si el texto varía en longitud */
        }

        .footer-text {
            text-align: center;
            color: #7B8794;
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
    # Creamos las dos columnas para formar la cuadrícula de 2x3
    col1, col2 = st.columns(2)
    
    for i, module in enumerate(modules):
        # Asignamos a la columna izquierda los pares (0, 2, 4) y derecha los impares (1, 3, 5)
        target_col = col1 if i % 2 == 0 else col2
        
        with target_col:
            # Creamos el botón gigante
            if module.enabled:
                if st.button(f"{module.icon} {module.label}", key=f"btn_{i}", use_container_width=True):
                    # Redirigir a la página elegida si el botón es presionado
                    st.switch_page(module.path)
            else:
                st.button(f"{module.icon} {module.label}", key=f"btn_{i}", disabled=True, use_container_width=True)
            
            # Colocamos la descripción del módulo discretamente debajo del botón
            status_html = f"<br><span style='color:#9A6700; font-weight:bold;'>({module.status})</span>" if module.status != "Activo" else ""
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
    apply_light_styles()
    render_header()
    render_summary(MODULES)
    render_modules(MODULES)
    render_footer()

if __name__ == "__main__":
    main()
