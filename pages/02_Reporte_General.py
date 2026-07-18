import os
import io
import smtplib
import tempfile
import contextlib
from datetime import datetime
from email.message import EmailMessage

import streamlit as st
import pandas as pd
from fpdf import FPDF
from PIL import Image
from pypdf import PdfWriter


# =========================================================
# IMPORT OPCIONAL PARA REGISTRO SHAREPOINT
# Si sharepoint_registry.py no existe o no esta configurado,
# la app sigue funcionando normal.
# =========================================================
try:
    from sharepoint_registry import registrar_pdf_sharepoint, mostrar_resultado_registro
    SHAREPOINT_REGISTRY_AVAILABLE = True
except Exception:
    SHAREPOINT_REGISTRY_AVAILABLE = False


# =========================================================
# CONFIGURACION GENERAL
# =========================================================
PAGE_TITLE = "BESCO | Reporte General"
PAGE_ICON = "📑"
LAYOUT = "centered"

MAX_EQUIPOS = 10
MAX_FOTOS_RECOMENDADAS = 6

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGO_PATH = os.path.join(ROOT_DIR, "logo besco 2026.jpeg")


# =========================================================
# CONFIGURAR PAGINA
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
            max-width: 780px;
        }

        .main-title {
            text-align: center;
            color: #1E3A5F;
            font-size: 1.7rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            text-align: center;
            color: #5B6573;
            font-size: 0.92rem;
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
# UTILIDADES GENERALES
# =========================================================
def limpiar_texto(texto):
    if texto is None:
        return ""

    if not isinstance(texto, str):
        texto = str(texto)

    reemplazos = {
        "•": "-",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u200b": "",
        "\r": "",
        "\n": " ",
        "°": " grados",
        "é": "e",
        "É": "E",
        "á": "a",
        "Á": "A",
        "í": "i",
        "Í": "I",
        "ó": "o",
        "Ó": "O",
        "ú": "u",
        "Ú": "U",
        "ñ": "n",
        "Ñ": "N",
        "ü": "u",
        "Ü": "U",
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    return texto.encode("latin-1", "replace").decode("latin-1")


@contextlib.contextmanager
def archivo_temporal(suffix=".jpg"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    try:
        yield tmp.name
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp.name)


def comprimir_imagen_a_temp(file_obj, max_size=(1100, 1100), quality=65):
    """
    Comprime imagen para hacer mas ligero el PDF.
    Ideal para fotos tomadas desde celular.
    """
    file_obj.seek(0)

    img = Image.open(file_obj).convert("RGB")
    img.thumbnail(max_size)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.close()

    img.save(
        tmp.name,
        format="JPEG",
        quality=quality,
        optimize=True
    )

    return tmp.name


def contar_archivos(archivos) -> int:
    if not archivos:
        return 0

    return len(archivos)


def mostrar_estado_fotos(nombre: str, archivos) -> None:
    cantidad = contar_archivos(archivos)

    if cantidad == 0:
        st.caption(f"{nombre}: sin archivos cargados.")
    elif cantidad <= MAX_FOTOS_RECOMENDADAS:
        st.success(f"{nombre}: {cantidad} archivo(s) cargado(s).")
    else:
        st.warning(
            f"{nombre}: {cantidad} archivo(s) cargado(s). "
            f"Para celular se recomienda maximo {MAX_FOTOS_RECOMENDADAS}."
        )


def limpiar_nombre_archivo(nombre: str) -> str:
    if not nombre:
        nombre = "Reporte_BESCO.pdf"

    caracteres_invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "&"]

    limpio = l*mpiar_texto(str(nombre))

    for *aracter in caracteres_invalidos:
 *      limpio = limpio.replace(cara*ter, "_")

    limpio = limpio.rep*ace(" ", "_")

    if not limpio.l*wer().endswith(".pdf"):
        li*pio += ".pdf"

    return limpio

*def obtener_columna_descripcion(df* pd.DataFrame) -> str:
    if "Des*ripción" in df.columns:
        re*urn "Descripción"

    if "Descrip*ion" in df.columns:
        return*"Descripcion"

    return "Descrip*ión"


def normalizar_correos_extr*(correos_extra: str) -> list:
    *f not correos_extra:
        retur* []

    correos = []

    for cor*eo in correos_extra.replace(";", "*").split(","):
        correo_limp*o = correo.strip()

        if cor*eo_limpio:
            correos.app*nd(correo_limpio)

    return corr*os


# ===========================*=============================
# CL*SE PDF
# =========================*===============================
cl*ss BESCO_PDF(FPDF):
    def __init*_(self):
        super().__init__(*
        self.section_count = 1
  *     self.set_auto_page_break(auto*True, margin=25)
        self.set_*argins(left=12, top=12, right=12)
*    def header(self):
        try:*            if os.path.exists(LOGO*PATH):
                img_logo = *mage.open(LOGO_PATH).convert("RGB"*
                orig_w, orig_h = *mg_logo.size

                fina*_h = 18
                final_w = *rig_w * (final_h / orig_h)

      *         with archivo_temporal(suf*ix=".jpg") as tmp_logo:
          *         img_logo.thumbnail((900, *00))
                    img_logo.*ave(tmp_logo, format="JPEG", quali*y=80, optimize=True)
             *      self.image(tmp_logo, x=12, y*8, w=final_w, h=final_h)
        e*cept Exception:
            pass

*       self.set_font("Arial", "B",*11)
        self.set_text_color(30* 58, 95)
        self.set_xy(0, 10*
        self.cell(
            se*f.w - 12,
            6,
         *  limpiar_texto("REPORTE DE SERVIC*O TECNICO"),
            0,
      *     1,
            "R"
        )
*        self.set_font("Arial", "",*8)
        self.set_text_color(120* 120, 120)
        self.set_x(0)
 *
