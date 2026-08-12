import os
import re
from datetime import date

import pandas as pd
import streamlit as st
from fpdf import FPDF

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

st.set_page_config(page_title="Cotizaciones | Besco", page_icon="💰", layout="wide")

# ==========================================
# CONSTANTES Y CONFIGURACIONES INICIALES
# ==========================================
IVA_RATE = 0.16
DEFAULT_UTILIDAD_MANUAL = 23.55
UTILIDAD_PRECIARIO = 0.0
DEFAULT_CANTIDAD = 1.0
DEFAULT_PRECIO = 0.0
BORRADOR_FOLIO_KEY = "__BORRADOR__"

MANUAL_TIPOS_SERVICIO = [
    "Aire Acondicionado", "Servicio", "Producto", "Instalación",
    "Mantenimiento", "Obra Civil", "Otro"
]
MANUAL_UNIDADES = [
    "PZA", "SERVICIO", "LOTE", "M2", "M3", "HORA", "DÍA", "MES", "KG", "OTRA"
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
    "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
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

# ==========================================
# FUNCIONES AUXILIARES Y ESTADO DE SESIÓN
# ==========================================
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
    st.session_state.setdefault("conceptos_cotizacion", [])
    st.session_state.setdefault("toggle_preciario_besco", True)
    st.session_state.setdefault("datos_cotizacion", get_default_datos_cotizacion())
    st.session_state.setdefault("condiciones_por_folio", {BORRADOR_FOLIO_KEY: DEFAULT_CONDICIONES})
    st.session_state.setdefault("plantilla_por_folio", {BORRADOR_FOLIO_KEY: "Base Besco"})
    st.session_state.setdefault("folio_condiciones_cargado", BORRADOR_FOLIO_KEY)
    st.session_state.setdefault("editor_condiciones", DEFAULT_CONDICIONES)
    st.session_state.setdefault("selector_plantilla_condiciones", "Base Besco")
    st.session_state.setdefault("mensaje_exito", "")
    st.session_state.setdefault("mensaje_error", "")
    # Estado para listas de insumos APU
    st.session_state.setdefault("apu_materiales", [])
    st.session_state.setdefault("apu_mano_obra", [])
    st.session_state.setdefault("apu_equipos", [])
    st.session_state.setdefault("apu_otros", [])

def reset_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.datos_cotizacion = get_default_datos_cotizacion()
    st.session_state.condiciones_por_folio = {BORRADOR_FOLIO_KEY: DEFAULT_CONDICIONES}
    st.session_state.plantilla_por_folio = {BORRADOR_FOLIO_KEY: "Base Besco"}
    st.session_state.folio_condiciones_cargado = BORRADOR_FOLIO_KEY
    st.session_state.editor_condiciones = DEFAULT_CONDICIONES
    st.session_state.selector_plantilla_condiciones = "Base Besco"
    st.session_state.mensaje_exito = ""
    st.session_state.mensaje_error = ""
    st.session_state.apu_materiales = []
    st.session_state.apu_mano_obra = []
    st.session_state.apu_equipos = []
    st.session_state.apu_otros = []

def formatear_moneda(valor):
    return f"${float(valor):,.2f}"

def parse_float(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return default
    text = text.replace("$", "").replace(",", "").replace("MXN", "").replace("mxn", "").replace(" ", "")
    text = re.sub(r"[^0-9\.\-]", "", text)
    try:
        return float(text)
    except ValueError:
        return default

def limpiar_texto_pdf(texto):
    if not texto:
        return ""
    texto = str(texto)
    reemplazos = {
        "•": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "–": "-", "—": "-", "\u200b": "", "\r": "", "°": " grados",
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.encode("latin-1", "replace").decode("latin-1")

def sanitize_filename(texto):
    texto = str(texto or "")
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
    txt = str(folio).strip().upper()
    return txt if txt else BORRADOR_FOLIO_KEY

def persistir_condiciones_folio(folio_key, condiciones, plantilla):
    st.session_state.condiciones_por_folio[folio_key] = condiciones.strip() if condiciones.strip() else DEFAULT_CONDICIONES
    st.session_state.plantilla_por_folio[folio_key] = plantilla if plantilla in PLANTILLAS_CONDICIONES else "Base Besco"

def sincronizar_condiciones_con_folio(folio_actual):
    nuevo = get_folio_key(folio_actual)
    cargado = st.session_state.folio_condiciones_cargado
    if cargado != nuevo:
        persistir_condiciones_folio(
            cargado,
            st.session_state.get("editor_condiciones", DEFAULT_CONDICIONES),
            st.session_state.get("selector_plantilla_condiciones", "Base Besco"),
        )
        if nuevo not in st.session_state.condiciones_por_folio:
            st.session_state.condiciones_por_folio[nuevo] = DEFAULT_CONDICIONES
        if nuevo not in st.session_state.plantilla_por_folio:
            st.session_state.plantilla_por_folio[nuevo] = "Base Besco"
        st.session_state.editor_condiciones = st.session_state.condiciones_por_folio[nuevo]
        st.session_state.selector_plantilla_condiciones = st.session_state.plantilla_por_folio[nuevo]
        st.session_state.folio_condiciones_cargado = nuevo
    return nuevo

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

# ==========================================
# CONEXIÓN GOOGLE SHEETS
# ==========================================
def validar_dependencias_google():
    if gspread is None or Credentials is None:
        raise RuntimeError("Faltan dependencias. Agrega en requirements.txt: gspread y google-auth")

def obtener_credenciales_gcp():
    validar_dependencias_google()
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("No se encontraron credenciales en st.secrets['gcp_service_account'].")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive",
    ]
    info = dict(st.secrets["gcp_service_account"])
    if "private_key" in info and isinstance(info["private_key"], str):
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
    return Credentials.from_service_account_info(info, scopes=scopes)

def obtener_cliente_gspread():
    return gspread.authorize(obtener_credenciales_gcp())

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
    def buscar(candidatas, default=""):
        for c in candidatas:
            if c in columnas_upper:
                return columnas_upper[c]
        return default
    col_clave = buscar(["CLAVE", "ITEM", "CODIGO", "CÓDIGO", "SKU"], "")
    col_desc = buscar([
        "CONCEPTO", "DESCRIPCION", "DESCRIPCIÓN", "PRODUCTO",
        "DESCRIPCION DE PRODUCTO O SERVICIO", "DESCRIPCIÓN DE PRODUCTO O SERVICIO"
    ], "")
    col_unidad = buscar(["UNIDAD", "UOM", "UM"], "")
    col_tipo = buscar(["TIPO DE SERVICIO", "TIPO_SERVICIO", "TIPO", "SERVICIO"], "")
    if not col_clave and len(columnas) >= 1:
        col_clave = columnas[0]
    if not col_desc and len(columnas) >= 2:
        col_desc = columnas[1]
    return {"clave": col_clave, "descripcion": col_desc, "unidad": col_unidad, "tipo_servicio": col_tipo}

def detectar_columnas_region(df):
    columnas_region = []
    for col in df.columns:
        col_up = str(col).strip().upper()
        if any(keyword in col_up for keyword in REGION_EXCLUDE_KEYWORDS):
            continue
        if any(k in col_up for k in ["PU", "PRECIO", "$", "TARIFA", "CENTRO", "SUR", "NORTE", "ORIENTE", "PONIENTE", "OCCIDENTE", "PENINSULA", "PENÍNSULA"]):
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
                f"No se encontró la pestaña '{worksheet_name}' en el Preciario BESCO. Deja PRECIARIO_BESCO_WORKSHEET vacío o captura el nombre exacto de la pestaña."
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
        ws.append_row(["FOLIO", "FECHA", "CLIENTE", "EMPRESA / INMUEBLE", "NOMBRE COTIZACION", "TOTAL PRESUPUESTADO", "COTIZADOR"])
    return ws

def folio_ya_registrado(ws, folio):
    try:
        records = ws.get_all_records()
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
            st.session_state.mensaje_exito = f"ℹ️ La cotización con folio '{folio}' ya estaba registrada en el historial."
            return
        ws.append_row([folio, fecha_texto, cliente, empresa, nombre_cot, round(float(total), 2), cotizador])
        st.session_state.mensaje_exito = "✅ Cotización registrada y guardada en 'Historial Cotizaciones Besco'."
    except Exception as e:
        st.session_state.mensaje_error = f"❌ Error al guardar en Google Sheets: {e}. Verifica permisos del archivo y el nombre del documento compartido con el bot."

# ==========================================
# GENERACIÓN DE PDF (FPDF)
# ==========================================
class PDFCotizacion(FPDF):
    def __init__(self, condiciones):
        super().__init__("P", "mm", "Letter")
        self.condiciones = condiciones

    def header(self):
        logo_paths = ["logo besco 2026.jpeg", "logo_besco_2026.jpeg", "logo_besco.jpeg", "logo.jpeg"]
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
        self.multi_cell(0, 4, limpiar_texto_pdf(self.condiciones or DEFAULT_CONDICIONES), 0, "L")

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
    widths = [TABLE_COLS["codigo"], TABLE_COLS["concepto"], TABLE_COLS["unidad"], TABLE_COLS["cantidad"], TABLE_COLS["pu"], TABLE_COLS["importe"]]
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
    pdf = PDFCotizacion(condiciones)
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
    pdf.multi_cell(0, 5, limpiar_texto_pdf("Por medio de la presente y a nombre de Grupo Besco SA de CV, presento la siguiente cotizacion:"), 0, "L")
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

# ==========================================
# SECCIONES DE LA INTERFAZ STREAMLIT
# ==========================================
def render_seccion_identificacion():
    st.markdown("## 1. Identificación del cliente y persona que cotiza")
    datos = st.session_state.datos_cotizacion
    with st.container(border=True):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            folio = st.text_input("Folio / OT / TK", value=datos["folio"], placeholder="Ej. COT-001", max_chars=40)
        with col_g2:
            fecha = st.date_input("Fecha de cotización", value=datos["fecha"])
        with col_g3:
            nombre_cotizacion = st.text_input("Nombre de Cotización / Proyecto", value=datos["nombre_cotizacion"], placeholder="Ej. Reparación de Chiller")
        st.markdown("### Cliente")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            cliente_nombre = st.text_input("Nombre del cliente", value=datos["cliente_nombre"])
        with col_c2:
            cliente_empresa = st.text_input("Empresa / Inmueble", value=datos["cliente_empresa"])
        col_c3, col_c4, col_c5 = st.columns(3)
        with col_c3:
            cliente_contacto = st.text_input("Persona de contacto (Atención)", value=datos["cliente_contacto"])
        with col_c4:
            cliente_telefono = st.text_input("Teléfono del cliente", value=datos["cliente_telefono"])
        with col_c5:
            cliente_correo = st.text_input("Correo del cliente", value=datos["cliente_correo"])
        st.markdown("### Persona que cotiza")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            cotiza_nombre = st.text_input("Nombre de quien cotiza", value=datos["cotiza_nombre"])
        with col_p2:
            cotiza_puesto = st.text_input("Puesto", value=datos["cotiza_puesto"])
        col_p3, col_p4 = st.columns(2)
        with col_p3:
            cotiza_telefono = st.text_input("Teléfono de quien cotiza", value=datos["cotiza_telefono"])
        with col_p4:
            cotiza_correo = st.text_input("Correo de quien cotiza", value=datos["cotiza_correo"])
        st.session_state.datos_cotizacion.update({
            "folio": folio.strip(), "fecha": fecha,
            "cliente_nombre": cliente_nombre.strip(), "cliente_empresa": cliente_empresa.strip(),
            "cliente_contacto": cliente_contacto.strip(), "cliente_telefono": cliente_telefono.strip(),
            "cliente_correo": cliente_correo.strip(), "cotiza_nombre": cotiza_nombre.strip(),
            "cotiza_puesto": cotiza_puesto.strip(), "cotiza_telefono": cotiza_telefono.strip(),
            "cotiza_correo": cotiza_correo.strip(), "nombre_cotizacion": nombre_cotizacion.strip(),
        })


def render_modulo_apu():
    """Módulo secundario para calcular PU basándose en Análisis de Precios Unitarios"""
    st.markdown("### 🛠️ Análisis de Precios Unitarios (APU)")
    st.caption("Desglosa los costos directos para determinar automáticamente el Precio Unitario Final del concepto.")

    # 1. Materiales
    st.markdown("##### 1. Materiales e Insumos")
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([2, 1, 1, 1, 1])
    with col_m1:
        mat_desc = st.text_input("Material / Insumo", key="apu_mat_desc")
    with col_m2:
        mat_unid = st.selectbox("Unidad", MANUAL_UNIDADES, key="apu_mat_unid")
    with col_m3:
        mat_cant = st.number_input("Cantidad / Rend.", min_value=0.0, value=1.0, step=0.1, key="apu_mat_cant")
    with col_m4:
        mat_costo = st.number_input("Costo Unit. ($)", min_value=0.0, value=0.0, step=10.0, key="apu_mat_costo")
    with col_m5:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Añadir Mat.", key="btn_add_mat"):
            if mat_desc:
                st.session_state.apu_materiales.append({
                    "Concepto": mat_desc, "Unidad": mat_unid, "Cantidad": mat_cant,
                    "CostoUnit": mat_costo, "Importe": round(mat_cant * mat_costo, 2)
                })
                st.rerun()

    if st.session_state.apu_materiales:
        df_mat = pd.DataFrame(st.session_state.apu_materiales)
        st.dataframe(df_mat, use_container_width=True)
        if st.button("🗑️ Limpiar Materiales", key="clean_mat"):
            st.session_state.apu_materiales = []
            st.rerun()

    # 2. Mano de Obra
    st.markdown("##### 2. Mano de Obra")
    col_mo1, col_mo2, col_mo3, col_mo4, col_mo5 = st.columns([2, 1, 1, 1, 1])
    with col_mo1:
        mo_desc = st.text_input("Categoría / Personal", key="apu_mo_desc")
    with col_mo2:
        mo_unid = st.selectbox("Unidad ", ["HORA", "DÍA", "JORNAL", "SERVICIO"], key="apu_mo_unid")
    with col_mo3:
        mo_cant = st.number_input("Cantidad / Tiempo", min_value=0.0, value=1.0, step=0.1, key="apu_mo_cant")
    with col_mo4:
        mo_costo = st.number_input("Costo/Salario ($)", min_value=0.0, value=0.0, step=50.0, key="apu_mo_costo")
    with col_mo5:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Añadir MO", key="btn_add_mo"):
            if mo_desc:
                st.session_state.apu_mano_obra.append({
                    "Concepto": mo_desc, "Unidad": mo_unid, "Cantidad": mo_cant,
                    "CostoUnit": mo_costo, "Importe": round(mo_cant * mo_costo, 2)
                })
                st.rerun()

    if st.session_state.apu_mano_obra:
        df_mo = pd.DataFrame(st.session_state.apu_mano_obra)
        st.dataframe(df_mo, use_container_width=True)
        if st.button("🗑️ Limpiar Mano de Obra", key="clean_mo"):
            st.session_state.apu_mano_obra = []
            st.rerun()

    # 3. Herramienta y Equipo / Otros
    st.markdown("##### 3. Equipo, Herramienta y Otros Costos Directos")
    col_eq1, col_eq2, col_eq3, col_eq4, col_eq5 = st.columns([2, 1, 1, 1, 1])
    with col_eq1:
        eq_desc = st.text_input("Equipo / Concepto Adicional", key="apu_eq_desc")
    with col_eq2:
        eq_unid = st.selectbox("Unidad  ", ["HORA", "DÍA", "LOTE", "PZA"], key="apu_eq_unid")
    with col_eq3:
        eq_cant = st.number_input("Cantidad / Uso", min_value=0.0, value=1.0, step=0.1, key="apu_eq_cant")
    with col_eq4:
        eq_costo = st.number_input("Costo Unit. ($) ", min_value=0.0, value=0.0, step=50.0, key="apu_eq_costo")
    with col_eq5:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Añadir Equipo", key="btn_add_eq"):
            if eq_desc:
                st.session_state.apu_equipos.append({
                    "Concepto": eq_desc, "Unidad": eq_unid, "Cantidad": eq_cant,
                    "CostoUnit": eq_costo, "Importe": round(eq_cant * eq_costo, 2)
                })
                st.rerun()

    if st.session_state.apu_equipos:
        df_eq = pd.DataFrame(st.session_state.apu_equipos)
        st.dataframe(df_eq, use_container_width=True)
        if st.button("🗑️ Limpiar Equipo", key="clean_eq"):
            st.session_state.apu_equipos = []
            st.rerun()

    # Cálculo de Totales Directos e Indirectos
    costo_materiales = sum(item["Importe"] for item in st.session_state.apu_materiales)
    costo_mo = sum(item["Importe"] for item in st.session_state.apu_mano_obra)
    costo_equipo = sum(item["Importe"] for item in st.session_state.apu_equipos)

    costo_directo_total = costo_materiales + costo_mo + costo_equipo

    st.markdown("---")
    st.markdown("##### 4. Indirectos y Utilidad sobre APU")
    col_ind1, col_ind2, col_ind3 = st.columns(3)
    with col_ind1:
        pct_indirectos = st.number_input(" % Costo Indirecto / Operación", min_value=0.0, value=10.0, step=0.5)
    with col_ind2:
        pct_utilidad_apu = st.number_input(" % Utilidad Pretendida", min_value=0.0, value=15.0, step=0.5)
    with col_ind3:
        monto_indirectos = costo_directo_total * (pct_indirectos / 100)
        subtotal_con_indirectos = costo_directo_total + monto_indirectos
        monto_utilidad_apu = subtotal_con_indirectos * (pct_utilidad_apu / 100)
        precio_unitario_calculado = round(subtotal_con_indirectos + monto_utilidad_apu, 2)

    st.info(f"""
    **Resumen del Análisis de Precio Unitario (APU):**
    - **Costo Directo:** ${costo_directo_total:,.2f}
    - **Indirectos ({pct_indirectos}%):** ${monto_indirectos:,.2f}
    - **Utilidad ({pct_utilidad_apu}%):** ${monto_utilidad_apu:,.2f}
    - **PRECIO UNITARIO FINAL:** **${precio_unitario_calculado:,.2f}**
    """)

    return precio_unitario_calculado


def render_selector_preciario():
    st.markdown("## 2. Captura de Conceptos")

    modalidad_cotizacion = st.radio(
        "Selecciona la Modalidad de Cotización para agregar conceptos:",
        ["Cotización Directa (Preciario / Manual)", "Cotización con Análisis de Precios Unitarios (APU)"],
        horizontal=True
    )

    if modalidad_cotizacion == "Cotización Directa (Preciario / Manual)":
        with st.container(border=True):
            usar_preciario_besco = st.toggle(
                "Habilitar Preciario BESCO",
                value=st.session_state.toggle_preciario_besco,
                key="toggle_preciario_besco",
                help="Activa esta opción para seleccionar conceptos directamente del Preciario BESCO.",
            )
            origen_concepto = "Captura manual"
            clave_preciario = ""
            tipo_servicio = "Servicio"
            descripcion = ""
            unidad = "PZA"
            precio_unitario = DEFAULT_PRECIO

            if usar_preciario_besco:
                try:
                    df_preciario = obtener_preciario_besco()
                    if df_preciario.empty:
                        st.warning("El Preciario BESCO está vacío.")
                        usar_preciario_besco = False
                    else:
                        columnas_region = detectar_columnas_region(df_preciario)
                        if not columnas_region:
                            st.warning("No se detectaron columnas de precio o región en el Preciario BESCO. Se habilitará captura manual.")
                            usar_preciario_besco = False
                        else:
                            origen_concepto = "Preciario BESCO"
                            centro_idx = 0
                            for i, col in enumerate(columnas_region):
                                if "CENTRO" in str(col).upper():
                                    centro_idx = i
                                    break
                            col_reg, col_busq = st.columns([1, 2])
                            with col_reg:
                                region_seleccionada = st.selectbox("Región de Tarifas", options=columnas_region, index=centro_idx if centro_idx < len(columnas_region) else 0)
                            with col_busq:
                                busqueda = st.text_input("Buscador (escribe clave o concepto):").strip().lower()

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
                                df_filtrado["opcion_display"] = df_filtrado["clave"].astype(str).str.strip() + " - " + df_filtrado["descripcion"].astype(str).str.strip()
                                opcion_seleccionada = st.selectbox("Selecciona un concepto:", options=df_filtrado["opcion_display"].tolist())
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
                                st.text_area("Descripción de producto o servicio", value=descripcion, height=90, disabled=True)
                                precio_unitario = st.number_input(
                                    "Precio Unitario Base ($)", min_value=0.00, value=float(precio_unitario), step=0.01, format="%.2f",
                                    help="Puedes ajustar manualmente el precio base antes de agregar el concepto.",
                                )
                except Exception as e:
                    st.error(f"Error al cargar el Preciario BESCO: {e}")
                    st.info("Se habilitará automáticamente el modo de captura manual.")
                    usar_preciario_besco = False
                    origen_concepto = "Captura manual"

            if not usar_preciario_besco:
                origen_concepto = "Captura manual"
                st.info("Modo de captura manual habilitado.")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    clave_preciario = st.text_input("Clave / Item", value="", placeholder="Ej. SERV-001")
                with col2:
                    tipo_servicio = st.selectbox("Tipo de Servicio", MANUAL_TIPOS_SERVICIO, index=1)
                with col3:
                    unidad = st.selectbox("Unidad", MANUAL_UNIDADES, index=0)
                descripcion = st.text_area("Descripción de producto o servicio", value="", placeholder="Escribe el concepto detallado...")
                precio_unitario = st.number_input("Precio Unitario Base ($)", min_value=0.0, value=0.0, step=10.0, format="%.2f")

            st.markdown("---")
            col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
            with col_c1:
                cantidad = st.number_input("Cantidad", min_value=0.01, value=DEFAULT_CANTIDAD, step=1.0, format="%.2f")
            with col_c2:
                utilidad_pct = st.number_input(
                    "% Utilidad a aplicar",
                    min_value=0.0,
                    value=UTILIDAD_PRECIARIO if usar_preciario_besco else DEFAULT_UTILIDAD_MANUAL,
                    step=0.5,
                    format="%.2f",
                )
            with col_c3:
                precio_venta_u = calcular_precio_venta(precio_unitario, utilidad_pct)
                importe_total = round(cantidad * precio_venta_u, 2)
                st.metric("Precio Venta Unitario", formatear_moneda(precio_venta_u))
                st.metric("Importe Total Concepto", formatear_moneda(importe_total))

            if st.button("➕ Agregar Concepto a Cotización", type="primary"):
                errs = validar_concepto(descripcion, unidad, cantidad, precio_unitario)
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    item_num = len(st.session_state.conceptos_cotizacion) + 1
                    nuevo_concepto = {
                        "Item": item_num,
                        "Clave": clave_preciario if clave_preciario else f"ITEM-{item_num:02d}",
                        "Tipo Servicio": tipo_servicio,
                        "Concepto": descripcion,
                        "Unidad": unidad,
                        "Cantidad": cantidad,
                        "Precio Base": precio_unitario,
                        "Utilidad %": utilidad_pct,
                        "Precio Venta": precio_venta_u,
                        "Importe": importe_total,
                        "Origen": origen_concepto,
                        "Modalidad": "Directa"
                    }
                    st.session_state.conceptos_cotizacion.append(nuevo_concepto)
                    st.success("✅ Concepto agregado correctamente.")
                    st.rerun()

    else:
        # Modalidad APU
        with st.container(border=True):
            st.subheader("Captura de Concepto con Análisis de Precios Unitarios")
            col_a1, col_a2, col_a3 = st.columns([1, 2, 1])
            with col_a1:
                clave_apu = st.text_input("Clave / Item", value="", placeholder="Ej. APU-001")
            with col_a2:
                tipo_apu = st.selectbox("Tipo de Servicio", MANUAL_TIPOS_SERVICIO, index=3)
            with col_a3:
                unidad_apu = st.selectbox("Unidad del Concepto", MANUAL_UNIDADES, index=0)

            desc_apu = st.text_area("Descripción detallada del Trabajo / Concepto APU", placeholder="Ej. Suministro e instalación de unidad Chiller de 10 TR...")

            # Renderizamos la calculadora APU
            pu_calculado = render_modulo_apu()

            st.markdown("---")
            col_ap1, col_ap2 = st.columns(2)
            with col_ap1:
                cantidad_apu = st.number_input("Cantidad de este concepto en la obra/servicio", min_value=0.01, value=1.0, step=1.0)
            with col_ap2:
                importe_apu = round(cantidad_apu * pu_calculado, 2)
                st.metric("Importe Total del Concepto", formatear_moneda(importe_apu))

            if st.button("➕ Agregar Concepto APU a Cotización", type="primary"):
                errs = validar_concepto(desc_apu, unidad_apu, cantidad_apu, pu_calculado)
                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    item_num = len(st.session_state.conceptos_cotizacion) + 1
                    nuevo_concepto = {
                        "Item": item_num,
                        "Clave": clave_apu if clave_apu else f"APU-{item_num:02d}",
                        "Tipo Servicio": tipo_apu,
                        "Concepto": desc_apu,
                        "Unidad": unidad_apu,
                        "Cantidad": cantidad_apu,
                        "Precio Base": pu_calculado,
                        "Utilidad %": 0.0,  # Incluida internamente en el desglose APU
                        "Precio Venta": pu_calculado,
                        "Importe": importe_apu,
                        "Origen": "Análisis APU",
                        "Modalidad": "APU"
                    }
                    st.session_state.conceptos_cotizacion.append(nuevo_concepto)
                    st.success("✅ Concepto APU agregado exitosamente.")
                    # Reiniciamos las tablas de insumos APU
                    st.session_state.apu_materiales = []
                    st.session_state.apu_mano_obra = []
                    st.session_state.apu_equipos = []
                    st.rerun()


def render_tabla_conceptos():
    st.markdown("## 3. Resumen de Conceptos Agregados")
    conceptos = st.session_state.conceptos_cotizacion
    if not conceptos:
        st.info("Aún no has agregado conceptos a la cotización.")
        return 0.0, 0.0, 0.0

    df = pd.DataFrame(conceptos)
    df_display = df[[
        "Item", "Clave", "Tipo Servicio", "Concepto", "Unidad",
        "Cantidad", "Precio Venta", "Importe", "Modalidad"
    ]].copy()
    df_display["Precio Venta"] = df_display["Precio Venta"].apply(formatear_moneda)
    df_display["Importe"] = df_display["Importe"].apply(formatear_moneda)

    st.dataframe(df_display, use_container_width=True)

    col_acc1, col_acc2 = st.columns([1, 4])
    with col_acc1:
        if st.button("🗑️ Eliminar Último Concepto"):
            st.session_state.conceptos_cotizacion.pop()
            st.rerun()

    subtotal, iva, total = calcular_totales(conceptos)
    st.markdown("---")
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Subtotal", formatear_moneda(subtotal))
    col_t2.metric("IVA (16%)", formatear_moneda(iva))
    col_t3.metric("TOTAL PRESUPUESTADO", formatear_moneda(total))

    return subtotal, iva, total


def render_seccion_condiciones():
    st.markdown("## 4. Condiciones Comerciales")
    folio = st.session_state.datos_cotizacion.get("folio", "")
    folio_key = sincronizar_condiciones_con_folio(folio)

    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        plantilla_sel = st.selectbox(
            "Seleccionar plantilla de condiciones",
            options=list(PLANTILLAS_CONDICIONES.keys()),
            key="selector_plantilla_condiciones",
        )
        if st.button("Aplicar Plantilla"):
            st.session_state.editor_condiciones = PLANTILLAS_CONDICIONES[plantilla_sel]
            st.session_state.plantilla_por_folio[folio_key] = plantilla_sel
            st.session_state.condiciones_por_folio[folio_key] = PLANTILLAS_CONDICIONES[plantilla_sel]
            st.success(f"Plantilla '{plantilla_sel}' aplicada.")
            st.rerun()

    with col_p2:
        condiciones_txt = st.text_area(
            "Condiciones Comerciales de la Cotización",
            value=st.session_state.editor_condiciones,
            height=140,
            key="editor_condiciones",
        )
        st.session_state.condiciones_por_folio[folio_key] = condiciones_txt


def render_seccion_generacion(subtotal, iva, total):
    st.markdown("## 5. Exportar y Registrar Cotización")
    datos = st.session_state.datos_cotizacion
    conceptos = st.session_state.conceptos_cotizacion
    folio_key = get_folio_key(datos.get("folio", ""))
    condiciones = st.session_state.condiciones_por_folio.get(folio_key, DEFAULT_CONDICIONES)

    if st.session_state.mensaje_exito:
        st.success(st.session_state.mensaje_exito)
    if st.session_state.mensaje_error:
        st.error(st.session_state.mensaje_error)

    col_gen1, col_gen2, col_gen3 = st.columns(3)

    with col_gen1:
        if st.button("📄 Generar Cotización PDF", type="primary", use_container_width=True):
            errores = validar_datos_cotizacion(datos)
            if not conceptos:
                errores.append("Agrega al menos un concepto a la cotización.")
            if errores:
                st.session_state.mensaje_error = " Por favor corrige los siguientes datos:\n" + "\n".join(f"- {e}" for e in errores)
                st.session_state.mensaje_exito = ""
                st.rerun()
            else:
                try:
                    pdf_bytes = generar_pdf_cotizacion(datos, conceptos, subtotal, iva, total, condiciones)
                    filename = f"Cotizacion_{sanitize_filename(datos['folio'])}_{sanitize_filename(datos['cliente_empresa'])}.pdf"
                    st.session_state.pdf_bytes = pdf_bytes
                    st.session_state.pdf_filename = filename
                    st.session_state.mensaje_exito = " PDF generado exitosamente. Haz clic en 'Descargar PDF'."
                    st.session_state.mensaje_error = ""
                    st.rerun()
                except Exception as e:
                    st.session_state.mensaje_error = f"❌ Error al generar el PDF: {e}"
                    st.rerun()

    with col_gen2:
        if "pdf_bytes" in st.session_state:
            st.download_button(
                label="⬇️ Descargar PDF",
                data=st.session_state.pdf_bytes,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf",
                use_container_width=True,
            )

    with col_gen3:
        if st.button("📊 Guardar en Historial Google Sheets", use_container_width=True):
            errores = validar_datos_cotizacion(datos)
            if not conceptos:
                errores.append("Agrega al menos un concepto a la cotización.")
            if errores:
                st.session_state.mensaje_error = " Por favor corrige los siguientes datos:\n" + "\n".join(f"- {e}" for e in errores)
                st.session_state.mensaje_exito = ""
                st.rerun()
            else:
                fecha_str = datos["fecha"].strftime("%Y-%m-%d") if datos["fecha"] else date.today().strftime("%Y-%m-%d")
                registrar_en_historial(
                    datos["folio"], fecha_str, datos["cliente_nombre"],
                    datos["cliente_empresa"], datos["nombre_cotizacion"], total, datos["cotiza_nombre"]
                )
                st.rerun()

    st.markdown("---")
    if st.button("🔄 Reiniciar / Nueva Cotización"):
        reset_cotizacion()
        if "pdf_bytes" in st.session_state:
            del st.session_state["pdf_bytes"]
        if "pdf_filename" in st.session_state:
            del st.session_state["pdf_filename"]
        st.rerun()


# ==========================================
# FLUJO PRINCIPAL DE LA APLICACIÓN
# ==========================================
def main():
    init_session_state()
    st.title("💰 Sistema de Cotizaciones | Grupo BESCO")
    st.caption("Crea cotizaciones directas (preciario/manual) o basadas en Análisis de Precios Unitarios (APU).")

    render_seccion_identificacion()
    render_selector_preciario()
    subtotal, iva, total = render_tabla_conceptos()
    render_seccion_condiciones()
    render_seccion_generacion(subtotal, iva, total)


if __name__ == "__main__":
    main()
