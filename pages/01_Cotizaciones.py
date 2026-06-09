import os
import re
from datetime import date, timedelta
from io import BytesIO
from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

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
    layout="wide",
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
# ESTILOS
# =========================================================
def apply_styles() -> None:
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1rem;
        }

        .section-card {
            border: 1px solid #E6ECF2;
            border-radius: 14px;
            padding: 0.5rem 0.5rem 0.75rem 0.5rem;
            background-color: #FFFFFF;
        }

        .summary-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            background-color: #EAF2FF;
            color: #1E3A5F;
            border: 1px solid #B6CAE3;
        }

        .helper-note {
            font-size: 0.92rem;
            color: #5B6573;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HELPERS DE ESTADO
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

    if "ultimo_registro_historial" not in st.session_state:
        st.session_state.ultimo_registro_historial = ""


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

    # Elimina símbolos comunes
    text = (
        text.replace("$", "")
        .replace(",", "")
        .replace("MXN", "")
        .replace("mxn", "")
        .replace(" ", "")
    )

    # Conserva solo números, punto y signo
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

    return texto


def sanitize_filename(texto: str) -> str:
    if not texto:
        return ""
    texto = "".join(c for c in texto if c.isalnum() or c in " -_")
    texto = texto.strip().replace(" ", "_")
    return texto


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
    errores = []

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
    errores = []

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
# GOOGLE SHEETS / GSPREAD
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


def abrir_spreadsheet_preciario():
    gc = obtener_cliente_gspread()

    preciario_url = st.secrets.get("PRECIARIO_BESCO_URL", "").strip()
    preciario_key = st.secrets.get("PRECIARIO_BESCO_KEY", "").strip()
    preciario_title = st.secrets.get("PRECIARIO_BESCO_TITLE", "Preciario Besco").strip()

    if preciario_url:
        return gc.open_by_url(preciario_url)

    if preciario_key:
        return gc.open_by_key(preciario_key)

    return gc.open(preciario_title)


def detectar_columnas_base(df: pd.DataFrame) -> Dict[str, str]:
    columnas = [str(c).strip() for c in df.columns]
    columnas_upper = {str(c).strip().upper(): str(c).strip() for c in df.columns}

    def buscar_candidata(candidatas, default=""):
        for candidata in candidatas:
            if candidata in columnas_upper:
                return columnas_upper[candidata]
        return default

    col_clave = buscar_candidata(["CLAVE", "ITEM", "CODIGO", "CÓDIGO", "SKU"], "")
    col_desc = buscar_candidata(
        [
            "CONCEPTO",
            "DESCRIPCION",
            "DESCRIPCIÓN",
            "PRODUCTO",
            "DESCRIPCION DE PRODUCTO O SERVICIO",
            "DESCRIPCIÓN DE PRODUCTO O SERVICIO",
        ],
        "",
    )
    col_unidad = buscar_candidata(["UNIDAD", "UOM", "UM"], "")
    col_tipo = buscar_candidata(["TIPO DE SERVICIO", "TIPO_SERVICIO", "TIPO", "SERVICIO"], "")

    if not col_clave and len(columnas) >= 1:
        col_clave = columnas[0]
    if not col_desc and len(columnas) >= 2:
        col_desc = columnas[1]

    return {
        "clave": col_clave,
        "descripcion": col_desc,
        "unidad": col_unidad,
        "tipo_servicio": col_tipo,
    }


def detectar_columnas_region(df: pd.DataFrame) -> List[str]:
    columnas_region = []

    for col in df.columns:
        col_up = str(col).strip().upper()

        if any(keyword in col_up for keyword in REGION_EXCLUDE_KEYWORDS):
            continue

        if (
            "PU" in col_up
            or "PRECIO" in col_up
            or "$" in col_up
            or "TARIFA" in col_up
            or "CENTRO" in col_up
            or "SUR" in col_up
            or "NORTE" in col_up
            or "ORIENTE" in col_up
            or "PONIENTE" in col_up
            or "OCCIDENTE" in col_up
            or "PENINSULA" in col_up
            or "PENÍNSULA" in col_up
        ):
            columnas_region.append(col)

    # fallback razonable
    if not columnas_region:
        for posible in ["PRECIO UNITARIO", "PRECIO", "PU", "TARIFA"]:
            for col in df.columns:
                if str(col).strip().upper() == posible:
                    columnas_region.append(col)

    # eliminar duplicados manteniendo orden
    columnas_region = list(dict.fromkeys(columnas_region))

    return columnas_region


@st.cache_data(show_spinner=False, ttl=300)
def obtener_preciario_besco() -> pd.DataFrame:
    spreadsheet = abrir_spreadsheet_preciario()

    worksheet_name = st.secrets.get("PRECIARIO_BESCO_WORKSHEET", "").strip()
    if worksheet_name:
        ws = spreadsheet.worksheet(worksheet_name)
    else:
        ws = spreadsheet.get_worksheet(0)

    records = ws.get_all_records()

    if not records:
        return pd.DataFrame()

    df_raw = pd.DataFrame(records)
    if df_raw.empty:
        return pd.DataFrame()

    mapeo = detectar_columnas_base(df_raw)

    # Construcción de dataframe normalizado, preservando columnas regionales
    df = df_raw.copy()

    if mapeo["clave"]:
        df = df.rename(columns={mapeo["clave"]: "clave"})
    else:
        df["clave"] = ""

    if mapeo["descripcion"]:
        df = df.rename(columns={mapeo["descripcion"]: "descripcion"})
    else:
        raise RuntimeError(
            "No se encontró una columna de descripción válida en el Preciario BESCO."
        )

    if mapeo["unidad"]:
        df = df.rename(columns={mapeo["unidad"]: "unidad"})
    else:
        df["unidad"] = "S/C"

    if mapeo["tipo_servicio"]:
        df = df.rename(columns={mapeo["tipo_servicio"]: "tipo_servicio"})
    else:
        df["tipo_servicio"] = "Servicio"

    df["clave"] = df["clave"].fillna("").astype(str).str.strip()
    df["descripcion"] = df["descripcion"].fillna("").astype(str).str.strip()
    df["unidad"] = df["unidad"].fillna("S/C").astype(str).str.strip()
    df["tipo_servicio"] = df["tipo_servicio"].fillna("Servicio").astype(str).str.strip()

    df = df[df["descripcion"] != ""].copy()
    df.reset_index(drop=True, inplace=True)

    return df


def abrir_spreadsheet_historial():
    gc = obtener_cliente_gspread()

    historial_url = st.secrets.get("HISTORIAL_COTIZACIONES_URL", "").strip()
    historial_key = st.secrets.get("HISTORIAL_COTIZACIONES_KEY", "").strip()
    historial_title = st.secrets.get("HISTORIAL_COTIZACIONES_TITLE", "Historial Cotizaciones Besco").strip()

    if historial_url:
        return gc.open_by_url(historial_url)

    if historial_key:
        return gc.open_by_key(historial_key)

    return gc.open(historial_title)


def obtener_worksheet_historial():
    spreadsheet = abrir_spreadsheet_historial()
    worksheet_name = st.secrets.get("HISTORIAL_COTIZACIONES_WORKSHEET", "Hoja 1").strip()

    try:
        ws = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=worksheet_name, rows="100", cols="10")
        ws.append_row(
            [
                "FOLIO",
                "FECHA",
                "CLIENTE",
                "EMPRESA / INMUEBLE",
                "NOMBRE COTIZACION",
                "TOTAL PRESUPUESTADO",
                "COTIZADOR",
            ]
        )
    return ws


def folio_ya_registrado(ws, folio: str) -> bool:
    try:
        records = ws.get_all_records()
        if not records:
            return False

        for row in records:
            if str(row.get("FOLIO", "")).strip().upper() == str(folio).strip().upper():
                return True

        return False
    except Exception:
        return False


def registrar_en_historial(
    folio: str,
    fecha_texto: str,
    cliente: str,
    empresa: str,
    nombre_cot: str,
    total: float,
    cotizador: str,
) -> None:
    try:
        ws = obtener_worksheet_historial()

        if folio_ya_registrado(ws, folio):
            st.session_state.mensaje_exito = (
                f"ℹ️ La cotización con folio '{folio}' ya estaba registrada en el historial."
            )
            return

        ws.append_row(
            [
                folio,
                fecha_texto,
                cliente,
                empresa,
                nombre_cot,
                round(float(total), 2),
                cotizador,
            ]
        )
        st.session_state.mensaje_exito = (
            "✅ Cotización registrada y guardada en 'Historial Cotizaciones Besco'."
        )
    except Exception as e:
        st.session_state.mensaje_error = (
            f"❌ Error al guardar en Google Sheets: {e}. "
            "Verifica permisos del archivo y el nombre del documento compartido con el bot."
        )


# =========================================================
# PDF
# =========================================================
def registrar_fuente_unicode():
    """
    Intenta registrar una fuente Unicode si existe en el proyecto.
    Si no existe, usa Helvetica.
    """
    posibles_fuentes = [
        ("NotoSans", "NotoSans-Regular.ttf"),
        ("DejaVuSans", "DejaVuSans.ttf"),
        ("ArialUnicode", "Arial Unicode.ttf"),
    ]

    for font_name, font_path in posibles_fuentes:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except Exception:
                continue

    return "Helvetica"


def draw_wrapped_text(c, text, x, y, max_width, line_height=11, font_name="Helvetica", font_size=8):
    c.setFont(font_name, font_size)
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        test = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(test, font_name, font_size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    for line in lines:
        c.drawString(x, y, line)
        y -= line_height

    return lines


def generar_pdf_cotizacion(
    datos: Dict,
    conceptos: List[Dict],
    subtotal: float,
    iva: float,
    total: float,
) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    font_name = registrar_fuente_unicode()

    margen_x = 12 * mm
    y_top = height - 15 * mm

    def nueva_pagina():
        c.showPage()
        return dibujar_header(), height - 65 * mm

    def dibujar_header():
        # Logo
        logo_paths = [
            "logo besco 2026.jpeg",
            "logo_besco_2026.jpeg",
            "logo_besco.jpeg",
            "logo.jpeg",
        ]
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    c.drawImage(logo_path, margen_x, height - 28 * mm, width=38 * mm, preserveAspectRatio=True, mask="auto")
                    break
                except Exception:
                    pass

        # Datos empresa
        c.setFont(font_name, 8)
        c.setFillColor(colors.black)
        empresa_info = (
            "Grupo Besco SA de CV\n"
            "JOSE IGNACIO BARTOLOACHE # 1910 Col. Acacias, CDMX\n"
            "Tel. 01 55 55 15 08 65\n"
            "RFC. GBE101207523"
        )

        text_obj = c.beginText()
        text_obj.setTextOrigin(width - 85 * mm, height - 15 * mm)
        text_obj.setFont(font_name, 8)
        for line in empresa_info.split("\n"):
            text_obj.textLine(limpiar_texto_pdf(line))
        c.drawText(text_obj)

    def dibujar_footer():
        c.setFont(font_name, 7)
        footer_y = 30 * mm
        terminos = [
            "- TIEMPO DE ENTREGA DE MATERIAL DE 1 A 2 DÍAS HÁBILES.",
            "- TIEMPO DE ENTREGA DEL SERVICIO DE 1 A 2 DÍAS HÁBILES.",
            "- SE REQUIERE ORDEN DE COMPRA, PEDIDO, O CONTRATO.",
            "- PAGO CONTRA ENTREGA DEL SERVICIO.",
            "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.",
            "- EL PRECIO QUE SE OFERTA ES POR EL TOTAL DE LOS TRABAJOS.",
            "- LOS TRABAJOS SE EJECUTARÁN EN HORARIO HÁBIL; SI SE REQUIERE FUERA DEL MISMO, HABRÁ VARIACIÓN EN EL COSTO DEL 35%.",
        ]

        y = footer_y
        for linea in terminos:
            c.drawString(margen_x, y, limpiar_texto_pdf(linea))
            y -= 4 * mm

    # Inicio PDF
    dibujar_header()
    y = y_top - 22 * mm

    fecha_pdf = datos["fecha"].strftime("%d/%m/%Y") if datos.get("fecha") else date.today().strftime("%d/%m/%Y")
    vigencia_pdf = (datos["fecha"] + timedelta(days=15)).strftime("%d/%m/%Y") if datos.get("fecha") else ""

    # Bloque cliente
    c.setFont(font_name, 9)

    def draw_label_value(label, value, x_label, x_value, y_line, label_width=40):
        c.setFont(font_name, 9)
        c.setFillColor(colors.black)
        c.drawRightString(x_label + label_width, y_line, limpiar_texto_pdf(label))
        c.drawString(x_value, y_line, limpiar_texto_pdf(value))

    draw_label_value("CLIENTE:", str(datos.get("cliente_nombre", "")).upper(), margen_x, margen_x + 45 * mm, y)
    draw_label_value("FECHA DE COTIZACIÓN:", fecha_pdf, 110 * mm, 155 * mm, y, 40)

    y -= 6 * mm
    draw_label_value("EMPRESA:", str(datos.get("cliente_empresa", "")).upper(), margen_x, margen_x + 45 * mm, y)
    draw_label_value("FECHA VIGENCIA:", vigencia_pdf, 110 * mm, 155 * mm, y, 40)

    y -= 6 * mm
    c.setFont(font_name, 9)
    c.drawRightString(margen_x + 40 * mm, y, limpiar_texto_pdf("FOLIO BESCO:"))
    c.setFillColor(colors.HexColor("#123456"))
    c.setFont(font_name, 9)
    c.drawString(margen_x + 45 * mm, y, limpiar_texto_pdf(str(datos.get("folio", "COT-S-N"))))
    c.setFillColor(colors.black)

    y -= 6 * mm
    draw_label_value("ATENCIÓN:", str(datos.get("cliente_contacto", "")).upper(), margen_x, margen_x + 45 * mm, y)

    y -= 10 * mm
    c.setFont(font_name, 9)
    c.drawString(
        margen_x,
        y,
        limpiar_texto_pdf(
            "Por medio de la presente y a nombre de Grupo Besco SA de CV, presento la siguiente cotización:"
        ),
    )

    y -= 8 * mm
    nombre_cot = str(datos.get("nombre_cotizacion", "")).strip()
    if nombre_cot:
        c.setFont(font_name, 11)
        c.drawCentredString(width / 2, y, limpiar_texto_pdf(nombre_cot.upper()))
        y -= 9 * mm

    # Encabezado tabla
    table_x = margen_x
    col_widths = [28 * mm, 78 * mm, 18 * mm, 20 * mm, 20 * mm, 26 * mm]
    headers = ["CÓDIGO", "CONCEPTO", "UNIDAD", "CANTIDAD", "PU", "IMPORTE"]

    def draw_table_header(y_pos):
        x = table_x
        c.setFillColor(colors.HexColor("#99C2FF"))
        c.setFont(font_name, 8)
        for idx, header in enumerate(headers):
            c.rect(x, y_pos - 6 * mm, col_widths[idx], 8 * mm, fill=1, stroke=1)
            c.setFillColor(colors.black)
            c.drawCentredString(x + col_widths[idx] / 2, y_pos - 3.5 * mm, limpiar_texto_pdf(header))
            c.setFillColor(colors.HexColor("#99C2FF"))
            x += col_widths[idx]
        c.setFillColor(colors.black)

    draw_table_header(y)
    y -= 9 * mm

    # Filas tabla
    c.setFont(font_name, 8)

    for concepto in conceptos:
        concepto_text = str(concepto.get("Concepto", ""))
        codigo = str(concepto.get("Item", ""))
        unidad = str(concepto.get("Unidad", ""))
        cantidad = float(concepto.get("Cantidad", 0))
        precio_venta = float(concepto.get("Precio Venta", 0))
        importe = float(concepto.get("Importe", 0))

        # Calcula altura dinámica de la celda de concepto
        lineas = []
        words = concepto_text.split()
        current = ""
        max_width = col_widths[1] - 4 * mm
        for word in words:
            test = f"{current} {word}".strip()
            if pdfmetrics.stringWidth(test, font_name, 8) <= max_width:
                current = test
            else:
                if current:
                    lineas.append(current)
                current = word
        if current:
            lineas.append(current)

        num_lineas = max(1, len(lineas))
        row_height = max(8 * mm, num_lineas * 4.5 * mm)

        # salto de página si se necesita
        if y < 60 * mm:
            dibujar_footer()
            dibujar_header()
            y = height - 75 * mm
            draw_table_header(y)
            y -= 9 * mm

        x = table_x

        # Código
        c.rect(x, y - row_height + 2 * mm, col_widths[0], row_height, stroke=1, fill=0)
        c.drawCentredString(x + col_widths[0] / 2, y - row_height / 2 + 2 * mm, limpiar_texto_pdf(codigo))
        x += col_widths[0]

        # Concepto
        c.rect(x, y - row_height + 2 * mm, col_widths[1], row_height, stroke=1, fill=0)
        text_y = y - 2 * mm
        for line in lineas:
            c.drawString(x + 2 * mm, text_y - 2 * mm, limpiar_texto_pdf(line))
            text_y -= 4.5 * mm
        x += col_widths[1]

        # Unidad
        c.rect(x, y - row_height + 2 * mm, col_widths[2], row_height, stroke=1, fill=0)
        c.drawCentredString(x + col_widths[2] / 2, y - row_height / 2 + 2 * mm, limpiar_texto_pdf(unidad))
        x += col_widths[2]

        # Cantidad
        c.rect(x, y - row_height + 2 * mm, col_widths[3], row_height, stroke=1, fill=0)
        c.drawCentredString(x + col_widths[3] / 2, y - row_height / 2 + 2 * mm, limpiar_texto_pdf(f"{cantidad:,.2f}"))
        x += col_widths[3]

        # PU
        c.rect(x, y - row_height + 2 * mm, col_widths[4], row_height, stroke=1, fill=0)
        c.drawRightString(x + col_widths[4] - 2 * mm, y - row_height / 2 + 2 * mm, limpiar_texto_pdf(f"$ {precio_venta:,.2f}"))
        x += col_widths[4]

        # Importe
        c.rect(x, y - row_height + 2 * mm, col_widths[5], row_height, stroke=1, fill=0)
        c.drawRightString(x + col_widths[5] - 2 * mm, y - row_height / 2 + 2 * mm, limpiar_texto_pdf(f"$ {importe:,.2f}"))

        y -= row_height

    # Totales
    y -= 6 * mm
    c.setFont(font_name, 9)
    c.drawRightString(160 * mm, y, "SUBTOTAL")
    c.drawRightString(198 * mm, y, limpiar_texto_pdf(f"$ {subtotal:,.2f}"))

    y -= 5 * mm
    c.drawRightString(160 * mm, y, "IVA 16%")
    c.drawRightString(198 * mm, y, limpiar_texto_pdf(f"$ {iva:,.2f}"))

    y -= 5 * mm
    c.setFont(font_name, 9)
    c.drawRightString(160 * mm, y, "TOTAL PRESUPUESTADO")
    c.drawRightString(198 * mm, y, limpiar_texto_pdf(f"$ {total:,.2f}"))

    # Firma
    if y < 70 * mm:
        dibujar_footer()
        dibujar_header()
        y = height - 90 * mm

    y -= 25 * mm
    c.setFont(font_name, 9)
    c.drawCentredString(width / 2, y, "ATENTAMENTE")

    y -= 14 * mm
    c.drawCentredString(width / 2, y, "___________________________________")

    y -= 6 * mm
    c.drawCentredString(width / 2, y, limpiar_texto_pdf(str(datos.get("cotiza_nombre", "")).strip().upper()))

    y -= 5 * mm
    c.drawCentredString(width / 2, y, limpiar_texto_pdf(str(datos.get("cotiza_puesto", "")).strip().upper()))

    y -= 5 * mm
    c.setFont(font_name, 9)
    c.drawCentredString(width / 2, y, "GRUPO BESCO")

    dibujar_footer()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# =========================================================
# UI - SECCIÓN 1
# =========================================================
def render_seccion_identificacion() -> None:
    st.markdown("## 1. Identificación del cliente y persona que cotiza")

    datos = st.session_state.datos_cotizacion

    with st.container(border=True):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            folio = st.text_input(
                "Folio / OT / TK",
                value=datos["folio"],
                placeholder="Ej. COT-001",
                max_chars=40,
            )
        with col_g2:
            fecha = st.date_input("Fecha de cotización", value=datos["fecha"])
        with col_g3:
            nombre_cotizacion = st.text_input(
                "Nombre de Cotización / Proyecto",
                value=datos["nombre_cotizacion"],
                placeholder="Ej. Reparación de Chiller",
            )

        st.markdown("### Cliente")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cliente_nombre = st.text_input(
                "Nombre del cliente",
                value=datos["cliente_nombre"],
            )
        with col_c2:
            cliente_empresa = st.text_input(
                "Empresa / Inmueble",
                value=datos["cliente_empresa"],
            )

        col_c3, col_c4, col_c5 = st.columns(3)
        with col_c3:
            cliente_contacto = st.text_input(
                "Persona de contacto (Atención)",
                value=datos["cliente_contacto"],
            )
        with col_c4:
            cliente_telefono = st.text_input(
                "Teléfono del cliente",
                value=datos["cliente_telefono"],
            )
        with col_c5:
            cliente_correo = st.text_input(
                "Correo del cliente",
                value=datos["cliente_correo"],
            )

        st.markdown("### Persona que cotiza")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            cotiza_nombre = st.text_input(
                "Nombre de quien cotiza",
                value=datos["cotiza_nombre"],
            )
        with col_p2:
            cotiza_puesto = st.text_input(
                "Puesto",
                value=datos["cotiza_puesto"],
            )

        col_p3, col_p4 = st.columns(2)
        with col_p3:
            cotiza_telefono = st.text_input(
                "Teléfono de quien cotiza",
                value=datos["cotiza_telefono"],
            )
        with col_p4:
            cotiza_correo = st.text_input(
                "Correo de quien cotiza",
                value=datos["cotiza_correo"],
            )

        st.session_state.datos_cotizacion.update(
            {
                "folio": folio.strip(),
                "fecha": fecha,
                "cliente_nombre": cliente_nombre.strip(),
                "cliente_empresa": cliente_empresa.strip(),
                "cliente_contacto": cliente_contacto.strip(),
                "cliente_telefono": cliente_telefono.strip(),
                "cliente_correo": cliente_correo.strip(),
                "cotiza_nombre": cotiza_nombre.strip(),
                "cotiza_puesto": cotiza_puesto.strip(),
                "cotiza_telefono": cotiza_telefono.strip(),
                "cotiza_correo": cotiza_correo.strip(),
                "nombre_cotizacion": nombre_cotizacion.strip(),
            }
        )


# =========================================================
# UI - PRECIARIO / CAPTURA MANUAL
# =========================================================
def render_selector_preciario():
    st.markdown("## 2. Captura de Conceptos")

    with st.container(border=True):
        st.toggle(
            "Habilitar Preciario BESCO",
            key="usar_preciario_besco",
            help="Activa esta opción para seleccionar conceptos directamente del Preciario BESCO.",
        )

        origen_concepto = "Captura manual"
        clave_preciario = ""
        tipo_servicio = "Servicio"
        descripcion = ""
        unidad = "PZA"
        precio_unitario = DEFAULT_PRECIO

        if st.session_state.usar_preciario_besco:
            origen_concepto = "Preciario BESCO"

            try:
                df_preciario = obtener_preciario_besco()

                if df_preciario.empty:
                    st.warning("El Preciario BESCO está vacío.")
                else:
                    columnas_region = detectar_columnas_region(df_preciario)

                    if not columnas_region:
                        st.warning(
                            "No se detectaron columnas de precio o región en el Preciario BESCO. "
                            "Puedes usar captura manual o revisar el archivo."
                        )
                    else:
                        centro_idx = 0
                        for i, col in enumerate(columnas_region):
                            if "CENTRO" in str(col).upper():
                                centro_idx = i
                                break

                        col_reg, col_busq = st.columns([1, 2])
                        with col_reg:
                            region_seleccionada = st.selectbox(
                                "📍 Región de Tarifas",
                                options=columnas_region,
                                index=centro_idx if centro_idx < len(columnas_region) else 0,
                            )

                        with col_busq:
                            busqueda = st.text_input(
                                "🔍 Buscador (escribe clave o concepto):"
                            ).strip().lower()

                        df_filtrado = df_preciario.copy()

                        if busqueda:
                            mascara = (
                                df_filtrado["clave"].astype(str).str.lower().str.contains(busqueda, na=False)
                                | df_filtrado["descripcion"].astype(str).str.lower().str.contains(busqueda, na=False)
                            )
                            df_filtrado = df_filtrado[mascara].copy()

                        if df_filtrado.empty:
                            st.warning("No hay coincidencias para la búsqueda ingresada.")
                        else:
                            df_filtrado["opcion_display"] = (
                                df_filtrado["clave"].astype(str).str.strip()
                                + " - "
                                + df_filtrado["descripcion"].astype(str).str.strip()
                            )

                            opcion_seleccionada = st.selectbox(
                                "Selecciona un concepto:",
                                options=df_filtrado["opcion_display"].tolist(),
                            )

                            fila = df_filtrado[df_filtrado["opcion_display"] == opcion_seleccionada].iloc[0]

                            clave_preciario = str(fila.get("clave", "S/C")).strip()
                            tipo_servicio = str(fila.get("tipo_servicio", "Servicio")).strip() or "Servicio"
                            descripcion = str(fila.get("descripcion", "")).strip()
                            unidad = str(fila.get("unidad", "S/C")).strip() or "S/C"

                            precio_unitario = parse_float(fila.get(region_seleccionada, 0), DEFAULT_PRECIO)

                            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                            with col_b1:
                                st.text_input("Clave / Item", value=clave_preciario, disabled=True)
                            with col_b2:
                                st.text_input("Tipo de servicio", value=tipo_servicio, disabled=True)
                            with col_b3:
                                st.text_input("Unidad", value=unidad, disabled=True)

                            st.text_area(
                                "Descripción de producto o servicio",
                                value=descripcion,
                                height=90,
                                disabled=True,
                            )

                            precio_unitario = st.number_input(
                                "Precio Unitario Base ($)",
                                min_value=0.00,
                                value=float(precio_unitario),
                                step=0.01,
                                format="%.2f",
                                help="Puedes ajustar manualmente el precio base antes de agregar el concepto.",
                            )

            except Exception as e:
                st.error(f"Error al cargar el Preciario BESCO: {e}")
                st.info("Se habilitará automáticamente el modo de captura manual.")
                st.session_state.usar_preciario_besco = False

        if not st.session_state.usar_preciario_besco:
            st.info("Modo de captura manual habilitado.")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                tipo_servicio = st.selectbox("Tipo de servicio", MANUAL_TIPOS_SERVICIO)
            with col2:
                descripcion = st.text_area("Descripción detallada", height=90)
            with col3:
                unidad = st.selectbox("Unidad", MANUAL_UNIDADES)

            precio_unitario = st.number_input(
                "Precio unitario ($)",
                min_value=0.00,
                value=0.00,
                step=0.01,
                format="%.2f",
            )

        st.markdown("### Cálculo Financiero")
        col4, col5, col6, col7 = st.columns([1, 1, 1, 1])

        with col4:
            cantidad = st.number_input(
                "Cantidad",
                min_value=0.1,
                value=DEFAULT_CANTIDAD,
                step=1.0,
                format="%.2f",
            )

        with col5:
            utilidad_pct = st.number_input(
                "Utilidad (%)",
                min_value=0.00,
                value=DEFAULT_UTILIDAD,
                step=0.50,
                format="%.2f",
            )

        utilidad_monto_total = calcular_utilidad_monto(precio_unitario, utilidad_pct) * cantidad
        precio_venta = calcular_precio_venta(precio_unitario, utilidad_pct)
        importe_total = round(precio_venta * cantidad, 2)

        with col6:
            st.metric("Precio Venta Unitario", formatear_moneda(precio_venta))
        with col7:
            st.metric("Importe Total", formatear_moneda(importe_total))

        cinfo1, cinfo2, cinfo3 = st.columns(3)
        with cinfo1:
            st.info(f"**Origen del concepto:** {origen_concepto}")
        with cinfo2:
            st.info(f"**Utilidad total estimada:** {formatear_moneda(utilidad_monto_total)}")
        with cinfo3:
            st.info(f"**Cantidad capturada:** {cantidad:,.2f}")

        if st.button("➕ Agregar concepto a la cotización", use_container_width=True, type="primary"):
            errores = validar_concepto(descripcion, unidad, cantidad, precio_unitario)

            if errores:
                for error in errores:
                    st.warning(error)
            else:
                nuevo_concepto = {
                    "Item": clave_preciario if clave_preciario else "S/C",
                    "Tipo de servicio": tipo_servicio,
                    "Concepto": descripcion.strip(),
                    "Unidad": unidad.strip(),
                    "Cantidad": round(float(cantidad), 2),
                    "PU Base": round(float(precio_unitario), 2),
                    "Utilidad (%)": round(float(utilidad_pct), 2),
                    "Precio Venta": round(float(precio_venta), 2),
                    "Importe": round(float(importe_total), 2),
                }
                st.session_state.conceptos_cotizacion.append(nuevo_concepto)
                st.success("Concepto agregado correctamente.")
                st.rerun()


# =========================================================
# UI - RESUMEN / PDF / HISTORIAL
# =========================================================
def render_resumen_y_documento() -> None:
    st.markdown("## 3. Resumen y Documento Final")

    if st.session_state.mensaje_exito:
        st.success(st.session_state.mensaje_exito)
        st.session_state.mensaje_exito = ""

    if st.session_state.mensaje_error:
        st.error(st.session_state.mensaje_error)
        st.session_state.mensaje_error = ""

    conceptos = st.session_state.conceptos_cotizacion

    if not conceptos:
        st.info("Agrega conceptos para generar el documento PDF.")
        return

    df = pd.DataFrame(conceptos)
    st.dataframe(df, use_container_width=True, hide_index=True)

    subtotal, iva, total = calcular_totales(conceptos)

    c1, c2, c3 = st.columns(3)
    c1.metric("SUBTOTAL", formatear_moneda(subtotal))
    c2.metric("IVA (16%)", formatear_moneda(iva))
    c3.metric("TOTAL PRESUPUESTADO", formatear_moneda(total))

    col_btn_1, col_btn_2 = st.columns(2)
    with col_btn_1:
        if st.button("🗑️ Eliminar último concepto", use_container_width=True):
            st.session_state.conceptos_cotizacion.pop()
            st.rerun()

    with col_btn_2:
        if st.button("♻️ Limpiar toda la cotización", use_container_width=True):
            reset_cotizacion()
            st.rerun()

    st.markdown("---")

    datos = st.session_state.datos_cotizacion
    errores_cabecera = validar_datos_cotizacion(datos)

    if errores_cabecera:
        st.warning("Antes de registrar y descargar, completa estos datos:")
        for error in errores_cabecera:
            st.write(f"- {error}")
        return

    folio_pdf = datos["folio"].strip() if datos["folio"].strip() else "COT-S-N"
    fecha_pdf = datos["fecha"].strftime("%d/%m/%Y") if datos["fecha"] else date.today().strftime("%d/%m/%Y")
    nombre_cot = datos.get("nombre_cotizacion", "").strip()

    try:
        pdf_bytes = generar_pdf_cotizacion(
            datos=datos,
            conceptos=conceptos,
            subtotal=subtotal,
            iva=iva,
            total=total,
        )
    except Exception as e:
        st.error(f"No se pudo generar el PDF: {e}")
        return

    nombre_archivo_seguro = sanitize_filename(nombre_cot)
    if nombre_archivo_seguro:
        nombre_archivo = f"Cotizacion_{sanitize_filename(folio_pdf)}_{nombre_archivo_seguro}.pdf"
    else:
        nombre_archivo = f"Cotizacion_{sanitize_filename(folio_pdf)}.pdf"

    st.download_button(
        label="💾 Registrar y Descargar Cotización",
        data=pdf_bytes,
        file_name=nombre_archivo,
        mime="application/pdf",
        type="primary",
        on_click=registrar_en_historial,
        args=(
            folio_pdf,
            fecha_pdf,
            datos["cliente_nombre"],
            datos["cliente_empresa"],
            nombre_cot,
            total,
            datos["cotiza_nombre"],
        ),
        use_container_width=True,
    )


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    apply_styles()
    init_session_state()

    st.title("💰 Cotizaciones")
    st.caption("Genera cotizaciones con captura manual o con Preciario BESCO, y registra el historial automáticamente.")

    render_seccion_identificacion()
    render_selector_preciario()
    render_resumen_y_documento()


if __name__ == "__main__":
    main()
