import os
import re
from datetime import date
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
from fpdf import FPDF

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None


# =========================================================
# CONFIGURACIÓN DE PÁGINA
# =========================================================
st.set_page_config(
    page_title="Cotizaciones | Besco",
    page_icon="💰",
    layout="wide"
)


# =========================================================
# CONSTANTES
# =========================================================
IVA_RATE = 0.16
DEFAULT_UTILIDAD = 23.55
DEFAULT_CANTIDAD = 1.0
DEFAULT_PRECIO = 0.0

MANUAL_TIPOS_SERVICIO = [
    "Aire Acondicionado",
    "Servicio",
    "Producto",
    "Instalación",
    "Mantenimiento",
    "Obra Civil",
    "Otro",
]

MANUAL_UNIDADES = [
    "PZA",
    "SERVICIO",
    "LOTE",
    "M2",
    "M3",
    "HORA",
    "DÍA",
    "MES",
    "KG",
    "OTRA",
]

REGION_EXCLUDE_KEYWORDS = ["METRO NORTE"]


# =========================================================
# ESTADO
# =========================================================
def get_default_datos_cotizacion() -> Dict:
    return {
        "folio": "",
        "fecha": date.today(),
        "cliente_nombre": "",
        "cliente_empresa": "",
        "cliente_contacto": "",
        "cliente_telefono": "",
        "cliente_correo": "",
        "cotiza_nombre": "",
        "cotiza_puesto": "",
        "cotiza_telefono": "",
        "cotiza_correo": "",
        "nombre_cotizacion": "",
    }


def init_session_state() -> None:
    if "conceptos_cotizacion" not in st.session_state:
        st.session_state.conceptos_cotizacion = []

    if "usar_preciario_besco" not in st.session_state:
        st.session_state.usar_preciario_besco = True

    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = get_default_datos_cotizacion()

    if "mensaje_exito" not in st.session_state:
        st.session_state.mensaje_exito = ""

    if "mensaje_error" not in st.session_state:
        st.session_state.mensaje_error = ""


def reset_cotizacion() -> None:
    st.session_state.conceptos_cotizacion = []
    st.session_state.datos_cotizacion = get_default_datos_cotizacion()
    st.session_state.mensaje_exito = ""
    st.session_state.mensaje_error = ""


# =========================================================
# HELPERS GENERALES
# =========================================================
def formatear_moneda(valor: float) -> str:
    return f"${float(valor):,.2f}"


def parse_float(value, default: float = 0.0) -> float:
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if text == "":
        return default

    text = (
        text.replace("$", "")
        .replace(",", "")
        .replace("MXN", "")
        .replace("mxn", "")
        .replace(" ", "")
    )

    text = re.sub(r"[^0-9\.\-]", "", text)

    try:
        return float(text)
    except ValueError:
        return default


def limpiar_texto_pdf(texto: str) -> str:
    if not texto:
        return ""

    texto = str(texto)
    reemplazos = {
        "•": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "\u200b": "",
        "\r": "",
        "°": " grados",
    }

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    return texto.encode("latin-1", "replace").decode("latin-1")


def sanitize_filename(texto: str) -> str:
    if not texto:
        return ""
    texto = "".join(c for c in texto if c.isalnum() or c in " -_")
    return texto.strip().replace(" ", "_")


def calcular_precio_venta(precio_unitario: float, utilidad_porcentaje: float) -> float:
    return round(float(precio_unitario) * (1 + (float(utilidad_porcentaje) / 100)), 2)


def calcular_utilidad_monto(precio_unitario: float, utilidad_porcentaje: float) -> float:
    return round(float(precio_unitario) * (float(utilidad_porcentaje) / 100), 2)


def calcular_totales(conceptos: List[Dict]) -> Tuple[float, float, float]:
    if not conceptos:
        return 0.0, 0.0, 0.0

    df = pd.DataFrame(conceptos)
    subtotal = round(float(df["Importe"].sum()), 2)
    iva = round(subtotal * IVA_RATE, 2)
    total = round(subtotal + iva, 2)
    return subtotal, iva, total


# =========================================================
# VALIDACIONES
# =========================================================
def validar_datos_cotizacion(datos: Dict) -> List[str]:
    errores: List[str] = []

    if not str(datos.get("folio", "")).strip():
        errores.append("Captura el folio / OT / TK.")
    if not str(datos.get("cliente_nombre", "")).strip():
        errores.append("Captura el nombre del cliente.")
    if not str(datos.get("cliente_empresa", "")).strip():
        errores.append("Captura la empresa / inmueble.")
    if not str(datos.get("cotiza_nombre", "")).strip():
        errores.append("Captura el nombre de quien cotiza.")
    if not str(datos.get("cotiza_puesto", "")).strip():
        errores.append("Captura el puesto de quien cotiza.")
    if not str(datos.get("nombre_cotizacion", "")).strip():
        errores.append("Captura el nombre de la cotización / proyecto.")

    return errores


def validar_concepto(
    descripcion: str,
    unidad: str,
    cantidad: float,
    precio_unitario: float,
) -> List[str]:
    errores: List[str] = []

    if not str(descripcion).strip():
        errores.append("Debes capturar o seleccionar la descripción del concepto.")
    if not str(unidad).strip():
        errores.append("Debes capturar la unidad.")
    if float(cantidad) <= 0:
        errores.append("La cantidad debe ser mayor a 0.")
    if float(precio_unitario) < 0:
        errores.append("El precio unitario no puede ser negativo.")

    return errores


# =========================================================
# GOOGLE SHEETS
# =========================================================
def validar_dependencias_google() -> None:
    if gspread is None or Credentials is None:
        raise RuntimeError(
            "Faltan dependencias. Agrega en requirements.txt: gspread y google-auth"
        )


def obtener_credenciales_gcp():
    validar_dependencias_google()

    if "gcp_service_account" not in st.secrets:
        raise RuntimeError(
            "No se encontraron credenciales en st.secrets['gcp_service_account']."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive",
    ]

    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=scopes)


def obtener_cliente_gspread():
    creds = obtener_credenciales_gcp()
    return gspread.authorize(creds)


