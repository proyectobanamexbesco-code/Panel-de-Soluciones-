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
# ESTILOS LIGEROS PARA CELULAR
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
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #334E68;
        }

        .module-box {
            border: 1px solid #E6ECF2;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 12px;
            background-color: #FFFFFF;
        }

        .module-title {
            font-weight: 700;
            color: #1E3A5F;
            font-size: 1rem;
            margin-bottom: 4px;
        }

        .module-description {
            color: #5B6573;
            font-size: 0.85rem;
            margin-bottom: 8px;
        }

        .status-active {
            color: #127C56;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .status-soon {
            color: #9A6700;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .footer-text {
            text-align: center;
            color: #7B8794;
            font-size: 0.8rem;
            padding-top: 1rem;
        }

        div[data-testid="stPageLink"] a {
            width: 100%;
            border-radius: 10px;
        }

        button {
            border-radius: 10px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HELPERS
# =========================================================
def get_status_class(status: str) -> str:
    if status.strip().lower() == "activo":
        return "status-active"
    return "status-soon"


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
    active_modules = len([module for module in modules if module.enabled])

    st.markdown(
        f"""
        <div class="summary-box">
            <strong>Módulos disponibles:</strong> {active_modules} de {total_modules}<br>
            <strong>Objetivo:</strong> centralizar herramientas operativas en una sola entrada.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_module(module: PortalModule) -> None:
    status_class = get_status_class(module.status)

    st.markdown('<div class="module-box">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="module-title">{module.icon} {module.label}</div>
        <div class="module-description">{module.description}</div>
        <div class="{status_class}">Estado: {module.status}</div>
        """,
        unsafe_allow_html=True,
    )

    if module.enabled:
        st.page_link(
            module.path,
            label=f"Abrir {module.label}",
            icon=module.icon,
            use_container_width=True
        )
    else:
        st.button(
            f"{module.icon} No disponible",
            disabled=True,
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_modules(modules: List[PortalModule]) -> None:
    for module in modules:
        render_module(module)


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
``
