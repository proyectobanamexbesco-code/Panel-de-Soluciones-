import streamlit as st
from dataclasses import dataclass
from typing import List


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "Portal Grupo Besco"
PAGE_ICON = "🏗️"
LAYOUT = "wide"


@dataclass
class PortalModule:
    path: str
    label: str
    icon: str
    description: str
    enabled: bool = True
    status: str = "Activo"


MODULES: List[PortalModule] = [
    PortalModule(
        path="pages/01_Cotizaciones.py",
        label="Ir al Cotizador",
        icon="📄",
        description="Cálculo de presupuestos basados en preciario. Genera PDFs listos para el cliente.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/02_Reporte_General.py",
        label="Ir a Reporte Fotográfico",
        icon="📸",
        description="Generación de evidencia fotográfica general. Captura el antes y después del servicio.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/03_Nestle.py",
        label="Ir al Módulo Nestlé",
        icon="📑",
        description="Levantamiento de equipos y análisis de datos con IA y envío de correo automático.",
        enabled=True,
        status="Activo",
    ),
    PortalModule(
        path="pages/04_Proximas_Apps.py",
        label="Ir a Próximas Apps",
        icon="🚀",
        description="Espacio reservado para integraciones futuras y nuevas herramientas operativas.",
        enabled=True,
        status="Próximamente",
    ),
    PortalModule(
        path="pages/05_App_Vehicular.py",
        label="Ir a App Vehicular",
        icon="🚗",
        description="Aplicación para reporte vehicular con captura de evidencias, generación de PDF y descarga del reporte.",
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
# ESTILOS
# =========================================================
def apply_portal_styles() -> None:
    st.markdown(
        """
        <style>
        /* Fondo general del portal */
        .main > div {
            padding-top: 1.5rem;
        }

        /* Encabezado principal */
        .portal-header {
            text-align: center;
            padding: 0.5rem 0 1rem 0;
        }

        .portal-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E3A5F;
            margin-bottom: 0.2rem;
        }

        .portal-subtitle {
            font-size: 1rem;
            color: #5B6573;
            margin-bottom: 1rem;
        }

        /* Caja de resumen */
        .portal-summary {
            background: linear-gradient(135deg, #F7F9FC 0%, #EEF3F8 100%);
            border: 1px solid #D9E2EC;
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 1.25rem;
        }

        .portal-summary p {
            margin: 0;
            color: #334E68;
            font-size: 0.95rem;
        }

        /* Estilo del page_link */
        [data-testid="stPageLink-NavLink"] {
            background-color: #1E3A5F !important;
            padding: 24px !important;
            border-radius: 14px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.10);
            transition: all 0.25s ease-in-out;
            width: 100% !important;
            text-decoration: none !important;
            min-height: 92px !important;
            border: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stPageLink-NavLink"]:hover {
            background-color: #284B7A !important;
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.16);
            transform: translateY(-2px);
        }

        [data-testid="stPageLink-NavLink"] p {
            color: white !important;
            font-size: 21px !important;
            font-weight: 700 !important;
            margin: 0 !important;
            text-align: center !important;
        }

        /* Tarjeta auxiliar */
        .module-description {
            text-align: center;
            color: #5B6573;
            font-size: 14px;
            line-height: 1.5;
            margin-top: 10px;
            margin-bottom: 8px;
            min-height: 48px;
        }

        .module-status {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            margin-top: 4px;
            margin-bottom: 14px;
        }

        .status-active {
            background-color: #E3FCEF;
            color: #127C56;
            border: 1px solid #B7E4C7;
        }

        .status-soon {
            background-color: #FFF4E5;
            color: #9A6700;
            border: 1px solid #F3D19C;
        }

        /* Separación visual entre módulos */
        .module-block {
            background-color: #FFFFFF;
            border: 1px solid #E6ECF2;
            border-radius: 16px;
            padding: 16px 14px 12px 14px;
            margin-bottom: 14px;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        }

        /* Footer */
        .portal-footer {
            text-align: center;
            color: #7B8794;
            font-size: 0.85rem;
            padding-top: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# RENDER HELPERS
# =========================================================
def render_header() -> None:
    st.markdown(
        """
        <div class="portal-header">
            <div class="portal-title">🏗️ Portal de Soluciones Operativas</div>
            <div class="portal-subtitle">
                Selecciona una herramienta para comenzar y accede rápidamente a los módulos operativos.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(modules: List[PortalModule]) -> None:
    total_modules = len(modules)
    active_modules = len([m for m in modules if m.enabled])

    st.markdown(
        f"""
        <div class="portal-summary">
            <p><strong>Módulos disponibles:</strong> {active_modules} de {total_modules} |
            <strong>Portal:</strong> Grupo Besco |
            <strong>Objetivo:</strong> centralizar herramientas operativas en una sola entrada.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_status_class(status: str) -> str:
    if status.strip().lower() == "activo":
        return "status-active"
    return "status-soon"


def render_module_card(module: PortalModule) -> None:
    status_class = get_status_class(module.status)

    st.markdown('<div class="module-block">', unsafe_allow_html=True)

    if module.enabled:
        st.page_link(
            module.path,
            label=module.label,
            icon=module.icon,
            use_container_width=True
        )
    else:
        st.button(
            f"{module.icon} {module.label}",
            disabled=True,
            use_container_width=True
        )

    st.markdown(
        f"""
        <div class="module-description">
            {module.description}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="text-align:center;">
            <span class="module-status {status_class}">{module.status}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


def render_modules_grid(modules: List[PortalModule], columns_count: int = 2) -> None:
    columns = st.columns(columns_count)

    for index, module in enumerate(modules):
        with columns[index % columns_count]:
            render_module_card(module)


def render_footer() -> None:
    st.divider()
    st.markdown(
        """
        <div class="portal-footer">
            Sistema Operativo - Grupo Besco
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    apply_portal_styles()
    render_header()
    render_summary(MODULES)
    render_modules_grid(MODULES, columns_count=2)
    render_footer()


if __name__ == "__main__":
    main()
