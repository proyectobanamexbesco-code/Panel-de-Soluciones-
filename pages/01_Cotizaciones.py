import os
import re
from datetime import date

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
DEFAULT_UTILIDAD_MANUAL = 23.55
UTILIDAD_PRECIARIO = 0.00
DEFAULT_CANTIDAD = 1.0
DEFAULT_PRECIO = 0.0
BORRADOR_FOLIO_KEY = "__BORRADOR__"

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

TABLE_COLS = {
    "codigo": 28,
    "concepto": 84,
    "unidad": 16,
    "cantidad": 18,
    "pu": 20,
    "importe": 24,
}
TABLE_LINE_HEIGHT = 4.2
TABLE_MIN_ROW_HEIGHT = 10

DEFAULT_CONDICIONES = (
    "- TIEMPO DE ENTREGA DE MATERIAL DE 15 DÍAS HÁBILES.\n"
    "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACION, PEDIDO O CONTRATO, PARA INICIAR LAS ACTIVIDADES.\n"
    "- VIGENCIA DE LA COTIZACIÓN 15": "'",    "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
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


def sanitize_filename(texto):
    if not texto:
        return ""
    texto = "".join(c for c in texto if c.isalnum() or c in " -_")
    return texto.strip().replace(" ", "_")


def calcular_precio_venta(precio_unitario, utilidad_porcentaje):
    return round(float(precio_unitario) * (1 + (float(utilidad_porcentaje) / 100)), 2)


def calcular_utilidad_monto(precio_unitario, utilidad_porcentaje):
    return round(float(precio_unitario) * (float(utilidad_porcentaje) / 100), 2)


def calcular_totales(conceptos):
    if not conceptos:
        return 0.0, 0.0, 0.0

    df = pd.DataFrame(conceptos)
    subtotal = round(float(df["Importe"].sum()), 2)
    iva = round(subtotal * IVA_RATE, 2)
    total = round(subtotal + iva, 2)
    return subtotal, iva, total


def get_folio_key(folio):
    folio_txt = str(folio).strip().upper()
    return folio_txt if folio_txt else BORRADOR_FOLIO_KEY


def persistir_condiciones_folio(folio_key, condiciones, plantilla):
    st.session_state.condiciones_por_folio[folio_key] = condiciones.strip() if condiciones.strip() else DEFAULT_CONDICIONES
    st.session_state.plantilla_por_folio[folio_key] = plantilla if plantilla in PLANTILLAS_CONDICIONES else "Base Besco"
    st.session_state.condiciones_cotizacion = st.session_state.condiciones_por_folio[folio_key]


def sincronizar_condiciones_con_folio(folio_actual):
    nuevo_folio_key = get_folio_key(folio_actual)
    folio_cargado = st.session_state.folio_condiciones_cargado

    if folio_cargado != nuevo_folio_key:
        persistir_condiciones_folio(
            folio_cargado,
            st.session_state.get("editor_condiciones", DEFAULT_CONDICIONES),
            st.session_state.get("selector_plantilla_condiciones", "Base Besco"),
        )

        if nuevo_folio_key not in st.session_state.condiciones_por_folio:
            st.session_state.condiciones_por_folio[nuevo_folio_key] = DEFAULT_CONDICIONES
        if nuevo_folio_key not in st.session_state.plantilla_por_folio:
            st.session_state.plantilla_por_folio[nuevo_folio_key] = "Base Besco"

        st.session_state.editor_condiciones = st.session_state.condiciones_por_folio[nuevo_folio_key]
        st.session_state.selector_plantilla_condiciones = st.session_state.plantilla_por_folio[nuevo_folio_key]
        st.session_state.condiciones_cotizacion = st.session_state.condiciones_por_folio[nuevo_folio_key]
        st.session_state.folio_condiciones_cargado = nuevo_folio_key

    return nuevo_folio_key


# =========================================================
# VALIDACIONES
# =========================================================
def validar_datos_cotizacion(datos):
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


def validar_concepto(descripcion, unidad, cantidad, precio_unitario):
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
# GOOGLE SHEETS
# =========================================================
def validar_dependencias_google():
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

    if "private_key" in info and isinstance(info["private_key"], str):
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()

    return Credentials.from_service_account_info(info, scopes=scopes)


def obtener_cliente_gspread():
    creds = obtener_credenciales_gcp()
    return gspread.authorize(creds)


def abrir_spreadsheet_preciario():
    gc = obtener_cliente_gspread()

    preciario_url = str(st.secrets.get("PRECIARIO_BESCO_URL", "")).strip()
    preciario_key = str(st.secrets.get("PRECIARIO_BESCO_KEY", "")).strip()
    preciario_title = str(st.secrets.get("PRECIARIO_BESCO_TITLE", "Preciario Besco")).strip()

    if preciario_url:
        return gc.open_by_url(preciario_url)

    if preciario_key:
        return gc.open_by_key(preciario_key)

    return gc.open(preciario_title)


def detectar_columnas_base(df):
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


def detectar_columnas_region(df):
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

    if not columnas_region:
        for posible in ["PRECIO UNITARIO", "PRECIO", "PU", "TARIFA"]:
            for col in df.columns:
                if str(col).strip().upper() == posible:
                    columnas_region.append(col)

    return list(dict.fromkeys(columnas_region))


@st.cache_data(show_spinner=False, ttl=300)
def obtener_preciario_besco():
    spreadsheet = abrir_spreadsheet_preciario()

    worksheet_name = str(st.secrets.get("PRECIARIO_BESCO_WORKSHEET", "")).strip()
    if worksheet_name:
        try:
            ws = spreadsheet.worksheet(worksheet_name)
        except Exception:
            raise RuntimeError(
                f"No se encontró la pestaña '{worksheet_name}' en el Preciario BESCO. "
                "Deja PRECIARIO_BESCO_WORKSHEET vacío o captura el nombre exacto de la pestaña."
            )
    else:
        ws = spreadsheet.get_worksheet(0)

    records = ws.get_all_records()

    if not records:
        return pd.DataFrame()

    df_raw = pd.DataFrame(records)
    if df_raw.empty:
        return pd.DataFrame()

    mapeo = detectar_columnas_base(df_raw)
    df = df_raw.copy()

    if mapeo["clave"]:
        df = df.rename(columns={mapeo["clave"]: "clave"})
    else:
        df["clave"] = ""

    if mapeo["descripcion"]:
        df = df.rename(columns={mapeo["descripcion"]: "descripcion"})
    else:
        raise RuntimeError("No se encontró una columna de descripción válida en el Preciario BESCO.")

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

    historial_url = str(st.secrets.get("HISTORIAL_COTIZACIONES_URL", "")).strip()
    historial_key = str(st.secrets.get("HISTORIAL_COTIZACIONES_KEY", "")).strip()
    historial_title = str(st.secrets.get("HISTORIAL_COTIZACIONES_TITLE", "Historial Cotizaciones Besco")).strip()

    if historial_url:
        return gc.open_by_url(historial_url)

    if historial_key:
        return gc.open_by_key(historial_key)

    return gc.open(historial_title)


def obtener_worksheet_historial():
    spreadsheet = abrir_spreadsheet_historial()
    worksheet_name = str(st.secrets.get("HISTORIAL_COTIZACIONES_WORKSHEET", "Hoja 1")).strip()

    try:
        ws = spreadsheet.worksheet(worksheet_name)
    except Exception:
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


def folio_ya_registrado(ws, folio):
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


def registrar_en_historial(folio, fecha_texto, cliente, empresa, nombre_cot, total, cotizador):
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
class PDFCotizacion(FPDF):
    def __init__(self, condiciones):
        super().__init__("P", "mm", "Letter")
        self.condiciones = condiciones

    def header(self):
        logo_paths = [
            "logo besco 2026.jpeg",
            "logo_besco_2026.jpeg",
            "logo_besco.jpeg",
            "logo.jpeg",
        ]

        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    self.image(logo_path, 10, 8, 45)
                    break
                except Exception:
                    pass

        self.set_font("Arial", "", 8)
        self.set_text_color(0, 0, 0)
        self.set_xy(120, 10)
        empresa_info = (
            "Grupo Besco SA de CV\n"
            "JOSE IGNACIO BARTOLOACHE # 1910 Col. Acacias, CDMX\n"
            "Tel. 01 55 55 15 08 65\n"
            "RFC. GBE101207523"
        )
        self.multi_cell(80, 4, limpiar_texto_pdf(empresa_info), 0, "R")
        self.ln(10)

    def footer(self):
        self.set_y(-48)
        self.set_font("Arial", "I", 7)
        texto_footer = self.condiciones if self.condiciones else DEFAULT_CONDICIONES
        self.multi_cell(0, 4, limpiar_texto_pdf(texto_footer), 0, "L")


def pdf_wrap_lines(pdf, text, width):
    text = limpiar_texto_pdf(text)
    if not text:
        return [""]

    paragraphs = text.split("\n")
    lines = []

    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            test = current + " " + word
            if pdf.get_string_width(test) <= max(width - 2, 1):
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)

    return lines or [""]


def draw_table_header(pdf):
    pdf.set_fill_color(153, 194, 255)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(TABLE_COLS["codigo"], 8, "CODIGO", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["concepto"], 8, "CONCEPTO", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["unidad"], 8, "UNIDAD", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["cantidad"], 8, "CANTIDAD", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["pu"], 8, "PU", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["importe"], 8, "IMPORTE", 1, 1, "C", True)
    pdf.set_font("Arial", "", 8)


def draw_table_row(pdf, concepto):
    lines = pdf_wrap_lines(pdf, concepto["Concepto"], TABLE_COLS["concepto"] - 4)
    row_height = max(TABLE_MIN_ROW_HEIGHT, len(lines) * TABLE_LINE_HEIGHT + 2)

    if pdf.get_y() + row_height > 238:
        pdf.add_page()
        draw_table_header(pdf)

    x = pdf.get_x()
    y = pdf.get_y()

    widths = [
        TABLE_COLS["codigo"],
        TABLE_COLS["concepto"],
        TABLE_COLS["unidad"],
        TABLE_COLS["cantidad"],
        TABLE_COLS["pu"],
        TABLE_COLS["importe"],
    ]

    for width in widths:
        pdf.rect(x, y, width, row_height)
        x += width

    x_codigo = pdf.l_margin
    pdf.set_xy(x_codigo, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["codigo"], 4, limpiar_texto_pdf(str(concepto["Item"])), 0, 0, "C")

    x_concepto = pdf.l_margin + TABLE_COLS["codigo"] + 1.5
    y_text = y + 3.2
    for line in lines:
        pdf.set_xy(x_concepto, y_text)
        pdf.cell(TABLE_COLS["concepto"] - 3, 4, line, 0, 0, "L")
        y_text += TABLE_LINE_HEIGHT

    x_unidad = pdf.l_margin + TABLE_COLS["codigo"] + TABLE_COLS["concepto"]
    pdf.set_xy(x_unidad, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["unidad"], 4, limpiar_texto_pdf(str(concepto["Unidad"])), 0, 0, "C")

    x_cantidad = x_unidad + TABLE_COLS["unidad"]
    pdf.set_xy(x_cantidad, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["cantidad"], 4, limpiar_texto_pdf(f"{float(concepto['Cantidad']):,.2f}"), 0, 0, "C")

    x_pu = x_cantidad + TABLE_COLS["cantidad"]
    pdf.set_xy(x_pu, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["pu"] - 1.5, 4, limpiar_texto_pdf(f"$ {float(concepto['Precio Venta']):,.2f}"), 0, 0, "R")

    x_importe = x_pu + TABLE_COLS["pu"]
    pdf.set_xy(x_importe, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["importe"] - 1.5, 4, limpiar_texto_pdf(f"$ {float(concepto['Importe']):,.2f}"), 0, 0, "R")

    pdf.set_y(y + row_height)


def generar_pdf_cotizacion(datos, conceptos, subtotal, iva, total, condiciones):
    pdf = PDFCotizacion(condiciones=condiciones)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    folio_pdf = datos["folio"] if datos["folio"] else "COT-S-N"
    fecha_pdf = datos["fecha"].strftime("%d/%m/%Y") if datos["fecha"] else date.today().strftime("%d/%m/%Y")
    nombre_cot = datos.get("nombre_cotizacion", "").strip()

    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("CLIENTE:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_nombre"].upper()), 0, 0, "L")

    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 5, limpiar_texto_pdf("FECHA DE COTIZACION:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 5, limpiar_texto_pdf(fecha_pdf), 0, 1, "L")

    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("EMPRESA:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_empresa"].upper()), 0, 0, "L")

    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 5, limpiar_texto_pdf("FECHA VIGENCIA:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 5, limpiar_texto_pdf("15 DIAS HABILES"), 0, 1, "L")

    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("FOLIO BESCO:"), 0, 0, "R")
    pdf.set_text_color(18, 52, 86)
    pdf.cell(80, 5, limpiar_texto_pdf(folio_pdf), 0, 1, "L")
    pdf.set_text_color(0, 0, 0)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("ATENCION:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_contacto"].upper()), 0, 1, "L")
    pdf.ln(6)

    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(
        0,
        5,
        limpiar_texto_pdf(
            "Por medio de la presente y a nombre de Grupo Besco SA de CV, presento la siguiente cotizacion:"
        ),
        0,
        "L",
    )
    pdf.ln(2)

    if nombre_cot:
        pdf.set_font("Arial", "BI", 11)
        pdf.cell(0, 5, limpiar_texto_pdf(nombre_cot.upper()), 0, 1, "C")
        pdf.ln(4)

    draw_table_header(pdf)

    for concepto in conceptos:
        draw_table_row(pdf, concepto)

    if pdf.get_y() > 225:
        pdf.add_page()

    pdf.ln(4)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(145, 6, limpiar_texto_pdf("SUBTOTAL"), 0, 0, "R")
    pdf.cell(15, 6, limpiar_texto_pdf("$"), 0, 0, "R")
    pdf.cell(30, 6, limpiar_texto_pdf(f"{subtotal:,.2f}"), 0, 1, "R")

    pdf.cell(145, 6, limpiar_texto_pdf("IVA 16%"), 0, 0, "R")
    pdf.cell(15, 6, limpiar_texto_pdf("$"), 0, 0, "R")
    pdf.cell(30, 6, limpiar_texto_pdf(f"{iva:,.2f}"), 0, 1, "R")

    pdf.cell(145, 6, limpiar_texto_pdf("TOTAL PRESUPUESTADO"), 0, 0, "R")
    pdf.cell(15, 6, limpiar_texto_pdf("$"), 0, 0, "R")
    pdf.cell(30, 6, limpiar_texto_pdf(f"{total:,.2f}"), 0, 1, "R")

    if pdf.get_y() > 205:
        pdf.add_page()

    pdf.ln(18)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto_pdf("ATENTAMENTE"), 0, 1, "C")
    pdf.ln(12)
    pdf.cell(0, 4, limpiar_texto_pdf("___________________________________"), 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, limpiar_texto_pdf(datos["cotiza_nombre"].strip().upper()), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto_pdf(datos["cotiza_puesto"].strip().upper()), 0, 1, "C")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto_pdf("GRUPO BESCO"), 0, 1, "C")

    return pdf.output(dest="S").encode("latin-1")


# =========================================================
# UI - CONDICIONES EDITABLES POR FOLIO
# =========================================================
def render_condiciones_editables():
    st.markdown("## 3. Condiciones comerciales")

    folio_actual = st.session_state.datos_cotizacion.get("folio", "")
    folio_key = sincronizar_condiciones_con_folio(folio_actual)

    with st.container(border=True):
        if folio_key == BORRADOR_FOLIO_KEY:
            st.caption("Estás editando las condiciones del borrador actual. Cuando captures un folio, se guardarán para ese folio.")
        else:
            st.caption(f"Las condiciones y la plantilla se guardan automáticamente para el folio: {folio_key}")

        st.selectbox(
            "Plantilla de condiciones",
            options=list(PLANTILLAS_CONDICIONES.keys()),
            key="selector_plantilla_condiciones",
            help="Selecciona una plantilla base y luego, si lo deseas, edita el texto manualmente.",
        )

        st.text_area(
            "Condiciones de la cotización",
            key="editor_condiciones",
            height=180,
            help="Edita, agrega o elimina las condiciones comerciales que deben aparecer en el PDF.",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📥 Aplicar plantilla", use_container_width=True):
                plantilla = st.session_state.selector_plantilla_condiciones
                nuevo_texto = PLANTILLAS_CONDICIONES[plantilla]
                st.session_state.editor_condiciones = nuevo_texto
                persistir_condiciones_folio(folio_key, nuevo_texto, plantilla)
                st.success(f"Plantilla '{plantilla}' aplicada al folio {folio_key if folio_key != BORRADOR_FOLIO_KEY else 'BORRADOR'}.")
                st.rerun()

        with col_b:
            if st.button("💾 Guardar condiciones", use_container_width=True):
                persistir_condiciones_folio(
                    folio_key,
                    st.session_state.editor_condiciones,
                    st.session_state.selector_plantilla_condiciones,
                )
                st.success(f"Condiciones guardadas para el folio {folio_key if folio_key != BORRADOR_FOLIO_KEY else 'BORRADOR'}.")

        with col_c:
            if st.button("↩️ Restaurar base", use_container_width=True):
                st.session_state.selector_plantilla_condiciones = "Base Besco"
                st.session_state.editor_condiciones = DEFAULT_CONDICIONES
                persistir_condiciones_folio(folio_key, DEFAULT_CONDICIONES, "Base Besco")
                st.rerun()

        # autosave en cada rerun
        persistir_condiciones_folio(
            folio_key,
            st.session_state.editor_condiciones,
            st.session_state.selector_plantilla_condiciones,
        )

        if folio_key != BORRADOR_FOLIO_KEY and folio_key in st.session_state.plantilla_por_folio:
            st.info(
                f"Plantilla actual del folio {folio_key}: {st.session_state.plantilla_por_folio[folio_key]}"
            )


# =========================================================
# UI - RESUMEN Y PDF
# =========================================================
def render_resumen_y_documento():
    st.markdown("## 4. Resumen y Documento Final")

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
        st.warning("Antes de generar el PDF, completa estos datos:")
        for error in errores_cabecera:
            st.write(f"- {error}")
        return

    folio_pdf = datos["folio"].strip() if datos["folio"].strip() else "COT-S-N"
    fecha_pdf = datos["fecha"].strftime("%d/%m/%Y") if datos["fecha"] else date.today().strftime("%d/%m/%Y")
    nombre_cot = datos.get("nombre_cotizacion", "").strip()
    folio_key = get_folio_key(folio_pdf)
    condiciones = st.session_state.condiciones_por_folio.get(folio_key, st.session_state.editor_condiciones)
    condiciones = condiciones.strip() if condiciones.strip() else DEFAULT_CONDICIONES

    try:
        pdf_bytes = generar_pdf_cotizacion(
            datos=datos,
            conceptos=conceptos,
            subtotal=subtotal,
            iva=iva,
            total=total,
            condiciones=condiciones,
        )
    except Exception as e:
        st.error(f"No se pudo generar el PDF: {e}")
        return

    nombre_archivo_seguro = sanitize_filename(nombre_cot)
    if nombre_archivo_seguro:
        nombre_archivo = f"Cotizacion_{sanitize_filename(folio_pdf)}_{nombre_archivo_seguro}.pdf"
    else:
        nombre_archivo = f"Cotizacion_{sanitize_filename(folio_pdf)}.pdf"

    col_pdf, col_hist = st.columns(2)

    with col_pdf:
        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name=nombre_archivo,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    with col_hist:
        if st.button("☁️ Registrar en historial", use_container_width=True):
            registrar_en_historial(
                folio_pdf,
                fecha_pdf,
                datos["cliente_nombre"],
                datos["cliente_empresa"],
                nombre_cot,
                total,
                datos["cotiza_nombre"],
            )
            st.rerun()


# =========================================================
# MAIN
# =========================================================
def main():
    init_session_state()

    st.title("💰 Cotizaciones")
    st.caption("Versión corregida de Cotizaciones")

    render_seccion_identificacion()
    render_selector_preciario()
    render_condiciones_editables()
    render_resumen_y_documento()


if __name__ == "__main__":
    main()
    "- EL PRECIO QUE SE OFERTA ES POR EL TOTAL DE LOS TRABAJOS, TRABAJOS ADICIONALES SERAN COTIZADOS POR SEPARADO."
)

PLANTILLAS_CONDICIONES = {
    "Base Besco": DEFAULT_CONDICIONES,
    "Suministro": (
        "- TIEMPO DE ENTREGA DE MATERIAL DE 15 DÍAS HÁBILES.\n"
        "- SE REQUIERE ORDEN DE COMPRA O CORREO DE AUTORIZACIÓN PARA PROGRAMAR EL SUMINISTRO.\n"
        "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
        "- PRECIOS SUJETOS A DISPONIBILIDAD DE INVENTARIO Y CAMBIOS DE FABRICANTE SIN PREVIO AVISO."
    ),
    "Servicio": (
        "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACIÓN, PEDIDO O CONTRATO PARA INICIAR LAS ACTIVIDADES.\n"
        "- LOS TRABAJOS SE PROGRAMARÁN DE ACUERDO CON LA DISPONIBILIDAD OPERATIVA Y DE ACCESO AL SITIO.\n"
        "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
        "- TRABAJOS ADICIONALES O FUERA DE ALCANCE SERÁN COTIZADOS POR SEPARADO."
    ),
    "Instalación": (
        "- TIEMPO DE ENTREGA DE MATERIAL DE 15 DÍAS HÁBILES, SALVO EXISTENCIA EN STOCK.\n"
        "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACIÓN, PEDIDO O CONTRATO PARA INICIAR LAS ACTIVIDADES.\n"
        "- EL CLIENTE DEBERÁ PROPORCIONAR ACCESO, ENERGÍA Y ÁREA LIBRE PARA LA EJECUCIÓN DE LOS TRABAJOS.\n"
        "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS."
    ),
    "Mantenimiento Preventivo": (
        "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACIÓN, PEDIDO O CONTRATO PARA PROGRAMAR EL SERVICIO.\n"
        "- LOS EQUIPOS DEBERÁN ESTAR DISPONIBLES Y CON ACCESO LIBRE PARA EJECUTAR LAS ACTIVIDADES.\n"
        "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
        "- REFACCIONES O CORRECTIVOS DETECTADOS DURANTE EL SERVICIO SERÁN COTIZADOS POR SEPARADO."
    ),
    "Mantenimiento Correctivo": (
        "- EL TIEMPO DE ENTREGA DE MATERIAL O REFACCIONES SERÁ DE 15 DÍAS HÁBILES, SUJETO A DISPONIBILIDAD.\n"
        "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACIÓN, PEDIDO O CONTRATO PARA INICIAR LOS TRABAJOS.\n"
        "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
        "- EL PRECIO CUBRE ÚNICAMENTE EL ALCANCE DESCRITO; TRABAJOS ADICIONALES SERÁN COTIZADOS POR SEPARADO."
    ),
    "Obra / Proyecto": (
        "- EL TIEMPO DE ENTREGA DE MATERIALES SERÁ DE 15 DÍAS HÁBILES O CONFORME A PROGRAMA APROBADO.\n"
        "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACIÓN, PEDIDO O CONTRATO PARA INICIAR LOS TRABAJOS.\n"
        "- CUALQUIER CAMBIO DE ALCANCE, VOLÚMENES O INGENIERÍA SERÁ COTIZADO POR SEPARADO.\n"
        "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS."
    ),
}


# =========================================================
# ESTADO
# =========================================================
def get_default_datos_cotizacion():
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


def init_session_state():
    if "conceptos_cotizacion" not in st.session_state:
        st.session_state.conceptos_cotizacion = []

    if "usar_preciario_besco" not in st.session_state:
        st.session_state.usar_preciario_besco = True

    if "toggle_preciario_besco" not in st.session_state:
        st.session_state.toggle_preciario_besco = st.session_state.usar_preciario_besco

    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = get_default_datos_cotizacion()

    if "condiciones_cotizacion" not in st.session_state:
        st.session_state.condiciones_cotizacion = DEFAULT_CONDICIONES

    if "condiciones_por_folio" not in st.session_state:
        st.session_state.condiciones_por_folio = {BORRADOR_FOLIO_KEY: DEFAULT_CONDICIONES}

    if "plantilla_por_folio" not in st.session_state:
        st.session_state.plantilla_por_folio = {BORRADOR_FOLIO_KEY: "Base Besco"}

    if "folio_condiciones_cargado" not in st.session_state:
        st.session_state.folio_condiciones_cargado = BORRADOR_FOLIO_KEY

    if "editor_condiciones" not in st.session_state:
        st.session_state.editor_condiciones = DEFAULT_CONDICIONES

    if "selector_plantilla_condiciones" not in st.session_state:
        st.session_state.selector_plantilla_condiciones = "Base Besco"

    if "mensaje_exito" not in st.session_state:
        st.session_state.mensaje_exito = ""

    if "mensaje_error" not in st.session_state:
        st.session_state.mensaje_error = ""


def reset_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.datos_cotizacion = get_default_datos_cotizacion()
    st.session_state.condiciones_cotizacion = DEFAULT_CONDICIONES
    st.session_state.condiciones_por_folio = {BORRADOR_FOLIO_KEY: DEFAULT_CONDICIONES}
    st.session_state.plantilla_por_folio = {BORRADOR_FOLIO_KEY: "Base Besco"}
    st.session_state.folio_condiciones_cargado = BORRADOR_FOLIO_KEY
    st.session_state.editor_condiciones = DEFAULT_CONDICIONES
    st.session_state.selector_plantilla_condiciones = "Base Besco"
    st.session_state.mensaje_exito = ""
    st.session_state.mensaje_error = ""


# =========================================================
# HELPERS GENERALES
# =========================================================
def formatear_moneda(valor):
    return f"${float(valor):,.2f}"


def parse_float(value, default=0.0):
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
    text = re.sub(r"[^0-9\\.\\-]", "", text)

    try:
        return float(text)
    except ValueError:
        return default


def limpiar_texto_pdf(texto):
    if not texto:
        return ""

    texto = str(texto)
    reemplazos = {
        "•": "-",
        "“": '"',
        "”": '"',
