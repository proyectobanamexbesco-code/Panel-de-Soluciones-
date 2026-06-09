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
