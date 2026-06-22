import streamlit as st
import pandas as pd
import sys
import os


# =========================================================
# RUTA PARA IMPORTAR UTILS DESDE LA RAÍZ
# =========================================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import (
    obtener_gspread_client,
    enviar_correo,
    BESCO_PDF,
    analizar_reporte_con_gemini,
)


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "Módulo Nestlé | Besco"
PAGE_ICON = "📑"
LAYOUT = "centered"

DESTINATARIOS_DEFAULT = [
    "german.constantino@besco.mx",
    "andres.mayagoitia@besco.mx",
    "gerardo.mendez@besco.mx",
]

TECNICOS_DEFAULT = [
    "Oscar Salto",
    "Germán Constantino",
    "Andrés Mayagoitia",
    "Otro",
]

MAX_FOTOS_RECOMENDADAS = 6


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
def aplicar_estilos_ligeros() -> None:
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

        .nestle-title {
            text-align: center;
            font-size: 1.65rem;
            font-weight: 800;
            color: #1E3A5F;
            margin-bottom: 0.2rem;
        }

        .nestle-subtitle {
            text-align: center;
            font-size: 0.92rem;
            color: #5B6573;
            margin-bottom: 1rem;
        }

        .info-box {
            background-color: #F7F9FC;
            border: 1px solid #D9E2EC;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 1rem;
            color: #334E68;
            font-size: 0.9rem;
        }

        .ok-box {
            background-color: #E3FCEF;
            border: 1px solid #B7E4C7;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            color: #127C56;
            font-size: 0.9rem;
        }

        .warning-box {
            background-color: #FFF4E5;
            border: 1px solid #F3D19C;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            color: #9A6700;
            font-size: 0.9rem;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 800;
            color: #1E3A5F;
            margin-top: 1.2rem;
            margin-bottom: 0.5rem;
        }

        .footer-text {
            text-align: center;
            color: #7B8794;
            font-size: 0.8rem;
            padding-top: 1rem;
        }

        button {
            border-radius: 10px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# CARGA DE DATOS NESTLÉ
# =========================================================
@st.cache_data(ttl=600, show_spinner=False)
def cargar_datos_nestle() -> pd.DataFrame:
    try:
        client = obtener_gspread_client()
        data = client.open("NESTLE").worksheet("NESTLE").get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            return pd.DataFrame()

        df.columns = [str(c).upper().strip() for c in df.columns]

        columnas_requeridas = [
            "AREA",
            "ITEM",
            "DESCRIPCION DE EQUIPOS",
        ]

        faltantes = [col for col in columnas_requeridas if col not in df.columns]

        if faltantes:
            st.error(
                "La hoja NESTLE no contiene las columnas necesarias: "
                + ", ".join(faltantes)
            )
            return pd.DataFrame()

        df["AREA"] = df["AREA"].fillna("").astype(str).str.strip()
        df["ITEM"] = df["ITEM"].fillna("").astype(str).str.strip()
        df["DESCRIPCION DE EQUIPOS"] = (
            df["DESCRIPCION DE EQUIPOS"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df = df[df["AREA"] != ""].copy()
        df = df[df["ITEM"] != ""].copy()

        return df

    except Exception as error:
        st.error(
            "Error al cargar base de Nestlé. "
            f"Verifica la conexión o el nombre de la hoja: {error}"
        )
        return pd.DataFrame()


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def render_header() -> None:
    st.markdown(
        """
        <div class="nestle-title">📑 Módulo Nestlé</div>
        <div class="nestle-subtitle">
            Levantamiento técnico ligero para celular, generación de PDF y envío opcional.
        </div>
        """,
        unsafe_allow_html=True
    )


def contar_fotos(fotos) -> int:
    if fotos is None:
        return 0

    return len(fotos)


def validar_reporte(
    area: str,
    equipo: str,
    tecnico: str,
    observaciones: str,
) -> list:
    faltantes = []

    if not area:
        faltantes.append("Área")

    if not equipo:
        faltantes.append("Equipo")

    if not tecnico:
        faltantes.append("Técnico")

    if not observaciones.strip():
        faltantes.append("Observaciones técnicas")

    return faltantes


def generar_pdf_nestle(
    area: str,
    equipo: str,
    tecnico: str,
    observaciones: str,
    fotos_antes,
    fotos_despues,
) -> bytes:
    pdf = BESCO_PDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Levantamiento Técnico Nestlé", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Área: {area}", ln=True)
    pdf.cell(0, 8, f"Equipo: {equipo}", ln=True)
    pdf.cell(0, 8, f"Técnico: {tecnico}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Observaciones técnicas:", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, observaciones)
    pdf.ln(4)

    if fotos_antes:
        pdf.photo_grid("Evidencia: Antes", fotos_antes)

    if fotos_despues:
        pdf.photo_grid("Evidencia: Después", fotos_despues)

    salida_pdf = pdf.output(dest="S")

    if isinstance(salida_pdf, bytes):
        return salida_pdf

    return salida_pdf.encode("latin-1")


def obtener_item_puro(equipo: str) -> str:
    if " - " in equipo:
        return equipo.split(" - ")[0].strip()

    return equipo.strip().replace(" ", "_")


def mostrar_estado_fotos(nombre: str, fotos) -> None:
    cantidad = contar_fotos(fotos)

    if cantidad == 0:
        st.caption(f"{nombre}: sin fotos cargadas.")
    elif cantidad <= MAX_FOTOS_RECOMENDADAS:
        st.success(f"{nombre}: {cantidad} foto(s) cargada(s).")
    else:
        st.warning(
            f"{nombre}: {cantidad} fotos cargadas. "
            f"Para celular se recomiendan máximo {MAX_FOTOS_RECOMENDADAS}."
        )


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    aplicar_estilos_ligeros()
    render_header()

    st.page_link(
        "portal.py",
        label="⬅️ Volver al portal",
        use_container_width=True
    )

    st.markdown(
        """
        <div class="info-box">
            Recomendación para celular: captura solo las fotos necesarias y evita subir imágenes repetidas.
            Primero genera el PDF; después, si hay buena conexión, envíalo por correo o solicita análisis IA.
        </div>
        """,
        unsafe_allow_html=True
    )

    df = cargar_datos_nestle()

    if df.empty:
        st.warning("No se encontraron datos en la hoja de Nestlé.")
        st.stop()

    st.markdown(
        '<div class="section-title">1. Selección del equipo</div>',
        unsafe_allow_html=True
    )

    areas_disponibles = sorted(df["AREA"].dropna().unique().tolist())

    area = st.selectbox(
        "Área",
        areas_disponibles
    )

    df_area = df[df["AREA"] == area].copy()

    if df_area.empty:
        st.warning("No hay equipos disponibles para el área seleccionada.")
        st.stop()

    df_area["EQUIPO_LABEL"] = (
        df_area["ITEM"].astype(str)
        + " - "
        + df_area["DESCRIPCION DE EQUIPOS"].astype(str)
    )

    equipos_disponibles = df_area["EQUIPO_LABEL"].dropna().tolist()

    equipo = st.selectbox(
        "Selecciona el equipo",
        equipos_disponibles
    )

    st.markdown(
        '<div class="section-title">2. Datos técnicos</div>',
        unsafe_allow_html=True
    )

    tecnico_seleccionado = st.selectbox(
        "Técnico a cargo",
        TECNICOS_DEFAULT
    )

    if tecnico_seleccionado == "Otro":
        tecnico = st.text_input(
            "Especificar nombre del técnico",
            placeholder="Nombre del técnico"
        )
    else:
        tecnico = tecnico_seleccionado

    observaciones = st.text_area(
        "Observaciones técnicas",
        placeholder="Describe el levantamiento, condición del equipo, fallas, refacciones o acciones realizadas.",
        height=130
    )

    st.markdown(
        '<div class="section-title">3. Evidencia fotográfica</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="warning-box">
            Para hacer la app más ligera en celular, no se muestran previsualizaciones grandes.
            Al cargar fotos solo se indicará cuántas imágenes fueron seleccionadas.
        </div>
        """,
        unsafe_allow_html=True
    )

    fotos_antes = st.file_uploader(
        "Fotos antes",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png"],
        help="Recomendado: máximo 6 fotos para celular."
    )

    mostrar_estado_fotos("Fotos antes", fotos_antes)

    fotos_despues = st.file_uploader(
        "Fotos después",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png"],
        help="Recomendado: máximo 6 fotos para celular."
    )

    mostrar_estado_fotos("Fotos después", fotos_despues)

    st.markdown(
        '<div class="section-title">4. Opciones del reporte</div>',
        unsafe_allow_html=True
    )

    enviar_por_correo = st.checkbox(
        "Enviar reporte por correo después de generar PDF",
        value=True
    )

    ejecutar_ia = st.checkbox(
        "Analizar reporte con IA después de generar PDF",
        value=False
    )

    with st.expander("Destinatarios de correo", expanded=False):
        destinatarios_texto = st.text_area(
            "Correos destinatarios, uno por línea",
            value="\n".join(DESTINATARIOS_DEFAULT),
            height=110
        )

    destinatarios = [
        correo.strip()
        for correo in destinatarios_texto.splitlines()
        if correo.strip()
    ]

    st.markdown(
        '<div class="section-title">5. Generar reporte</div>',
        unsafe_allow_html=True
    )

    faltantes = validar_reporte(
        area=area,
        equipo=equipo,
        tecnico=tecnico,
        observaciones=observaciones,
    )

    if faltantes:
        st.markdown(
            f"""
            <div class="warning-box">
                Faltan campos obligatorios: {", ".join(faltantes)}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="ok-box">
                Datos completos. Ya puedes generar el reporte PDF.
            </div>
            """,
            unsafe_allow_html=True
        )

    generar = st.button(
        "📄 Generar reporte PDF",
        use_container_width=True,
        disabled=bool(faltantes)
    )

    if generar:
        item_puro = obtener_item_puro(equipo)
        nombre_pdf = f"Reporte_Nestle_{item_puro}.pdf"
        nombre_pdf = (
            nombre_pdf
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        with st.spinner("Generando PDF..."):
            try:
                pdf_bytes = generar_pdf_nestle(
                    area=area,
                    equipo=equipo,
                    tecnico=tecnico,
                    observaciones=observaciones,
                    fotos_antes=fotos_antes,
                    fotos_despues=fotos_despues,
                )

                st.session_state["nestle_pdf_bytes"] = pdf_bytes
                st.session_state["nestle_nombre_pdf"] = nombre_pdf
                st.session_state["nestle_item_puro"] = item_puro
                st.session_state["nestle_contexto_ia"] = (
                    f"Equipo: {equipo}, Área: {area}, "
                    f"Técnico: {tecnico}, Observaciones: {observaciones}"
                )

                st.success("PDF generado correctamente.")

            except Exception as error:
                st.error(f"No se pudo generar el PDF: {error}")

    if "nestle_pdf_bytes" in st.session_state:
        pdf_bytes = st.session_state["nestle_pdf_bytes"]
        nombre_pdf = st.session_state["nestle_nombre_pdf"]
        item_puro = st.session_state["nestle_item_puro"]

        st.download_button(
            "⬇️ Descargar PDF",
            data=pdf_bytes,
            file_name=nombre_pdf,
            mime="application/pdf",
            use_container_width=True
        )

        if enviar_por_correo:
            if not destinatarios:
                st.warning("No hay destinatarios configurados para enviar el correo.")
            else:
                enviar = st.button(
                    "📨 Enviar correo",
                    use_container_width=True
                )

                if enviar:
                    with st.spinner("Enviando correo..."):
                        try:
                            enviado = enviar_correo(
                                pdf_bytes,
                                "Nestle",
                                item_puro,
                                nombre_pdf,
                                "",
                                destinatarios
                            )

                            if enviado:
                                st.success("Reporte enviado correctamente.")
                            else:
                                st.error("No se pudo enviar el reporte por correo.")

                        except Exception as error:
                            st.error(f"Error al enviar correo: {error}")

        if ejecutar_ia:
            analizar = st.button(
                "🤖 Analizar con IA",
                use_container_width=True
            )

            if analizar:
                with st.spinner("Analizando reporte con IA..."):
                    try:
                        resumen = analizar_reporte_con_gemini(
                            st.session_state["nestle_contexto_ia"]
                        )

                        st.markdown("### 🤖 Análisis IA del reporte")
                        st.info(resumen)

                    except Exception as error:
                        st.error(f"No se pudo analizar con IA: {error}")

    st.divider()

    st.markdown(
        """
        <div class="footer-text">
            Sistema Operativo - Grupo Besco | Módulo Nestlé
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
