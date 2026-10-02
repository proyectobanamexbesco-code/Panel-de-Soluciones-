import os
import re
import requests
from datetime import date
import pandas as pd
import streamlit as st
from fpdf import FPDF

try:
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import Request
except ImportError:
    Credentials = None
    Request = None

st.set_page_config(page_title="Cotizaciones | Besco", page_icon="💰", layout="wide")

# ==========================================
# ESTILOS OSCUROS (TEMA EJECUTIVO BESCO)
# ==========================================
def apply_dark_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0B1421 !important;
        }
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* ===== FIX: BARRA LATERAL IZQUIERDA (SIDEBAR) ===== */
        [data-testid="stSidebar"] {
            background-color: #162032 !important;
            border-right: 1px solid #334155 !important;
        }
        [data-testid="stSidebarNav"] {
            background-color: #162032 !important;
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }
        [data-testid="stSidebarNav"] span {
            color: #F8FAFC !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebarNav"] li:hover {
            background-color: #1E293B !important;
        }
        [data-testid="stSidebarNav"] [aria-current="page"] {
            background-color: #363C98 !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebarNav"] [aria-current="page"] span {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }

        .block-container {
            padding-top: 2rem; 
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        h1, h2, h3, h4, p, label, .stMarkdown, .stText {
            color: #E2E8F0 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #162032 !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        }

        /* FIX DE CONTRASTE ESTRICTO: FONDO BLANCO Y LETRA NEGRA */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="select"] > div:focus-within {
            background-color: #FFFFFF !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
        }
        input, textarea, 
        div[data-baseweb="select"] span, 
        div[data-baseweb="select"] div {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            font-weight: 500 !important;
        }
        input::placeholder, textarea::placeholder {
            color: #64748B !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #64748B !important;
        }
        div[data-baseweb="popover"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #475569 !important;
        }
        ul[role="listbox"] li {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        ul[role="listbox"] li:hover {
            background-color: #E2E8F0 !important;
        }

        /* Botones estándar (Azul Besco) */
        div.stButton > button {
            background-color: #363C98 !important; 
            color: white !important;
            border: 1px solid #282D75 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #4C52BC !important;
            border: 1px solid #363C98 !important;
            transform: translateY(-2px);
        }
        
        /* Botones Primarios (Rojo Besco) */
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #E31837 !important; 
            border: 1px solid #B01028 !important;
            box-shadow: 0 4px 6px -1px rgba(227, 24, 55, 0.4);
        }
        div.stButton > button[data-testid="baseButton-primary"]:hover {
            background-color: #FA2A4A !important;
            border: 1px solid #E31837 !important;
        }
        [data-testid="stDataFrame"] {
            background-color: #1E293B !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
        }
        [data-testid="stMetricValue"] {
            color: #E31837 !important;
            font-weight: 800 !important;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# CONSTANTES Y ESTADO DE SESIÓN
# ==========================================
IVA_RATE = 0.16
DEFAULT_UTILIDAD_MANUAL = 23.55
UTILIDAD_PRECIARIO = 0.0
DEFAULT_CANTIDAD = 1.0
DEFAULT_PRECIO = 0.0
BORRADOR_FOLIO_KEY = "__BORRADOR__"

EMPRESAS_EMISORAS = {
    "Grupo Besco, S.A. de C.V.": {
        "nombre_corto": "GRUPO BESCO",
        "rfc": "GBE101207523",
        "direccion": "JOSE IGNACIO BARTOLOACHE # 1910 Col. Acacias, CDMX\nTel. 01 55 55 15 08 65"
    },
    "Besco ASM, S.A. de C.V.": {
        "nombre_corto": "BESCO ASM",
        "rfc": "BAS210714RV4",
        "direccion": "JOSE IGNACIO BARTOLOACHE # 1910 Col. Acacias, CDMX\nTel. 01 55 55 15 08 65"
    }
}

MANUAL_TIPOS_SERVICIO = ["Aire Acondicionado", "Servicio", "Producto", "Instalación", "Mantenimiento", "Preventivo", "Correctivo", "Obra Civil", "Otro"]
MANUAL_UNIDADES = ["PZA", "SERVICIO", "LOTE", "METRO", "METRO LINEAL", "M2", "M3", "HORA", "DÍA", "MES", "KG", "OTRA"]
REGION_EXCLUDE_KEYWORDS = ["METRO NORTE"]

TABLE_COLS = {"codigo": 28, "concepto": 84, "unidad": 16, "cantidad": 18, "pu": 20, "importe": 24}
TABLE_LINE_HEIGHT = 4.2
TABLE_MIN_ROW_HEIGHT = 10

DEFAULT_CONDICIONES = (
    "- TIEMPO DE ENTREGA DE MATERIAL DE 15 DÍAS HÁBILES.\n"
    "- SE REQUIERE ORDEN DE COMPRA, CORREO DE AUTORIZACION, PEDIDO O CONTRATO, PARA INICIAR LAS ACTIVIDADES.\n"
    "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
    "- EL PRECIO QUE SE OFERTA ES POR EL TOTAL DE LOS TRABAJOS, TRABAJOS ADICIONALES SERAN COTIZADOS POR SEPARADO."
)
PLANTILLAS_CONDICIONES = {"Base Besco": DEFAULT_CONDICIONES}

def get_default_datos_cotizacion():
    return {
        "folio": "", "fecha": date.today(), "empresa_cotizadora": list(EMPRESAS_EMISORAS.keys())[0],
        "cliente_nombre": "", "cliente_empresa": "", "cliente_contacto": "", "cliente_telefono": "",
        "cliente_correo": "", "cotiza_nombre": "", "cotiza_puesto": "", "cotiza_telefono": "",
        "cotiza_correo": "", "nombre_cotizacion": "", "vigencia": "15 DÍAS",
    }

def init_session_state():
    st.session_state.setdefault("conceptos_cotizacion", [])
    st.session_state.setdefault("toggle_preciario_besco", False)
    st.session_state.setdefault("datos_cotizacion", get_default_datos_cotizacion())
    st.session_state.setdefault("condiciones_por_folio", {BORRADOR_FOLIO_KEY: DEFAULT_CONDICIONES})
    st.session_state.setdefault("plantilla_por_folio", {BORRADOR_FOLIO_KEY: "Base Besco"})
    st.session_state.setdefault("folio_condiciones_cargado", BORRADOR_FOLIO_KEY)
    st.session_state.setdefault("editor_condiciones", DEFAULT_CONDICIONES)
    st.session_state.setdefault("selector_plantilla_condiciones", "Base Besco")
    st.session_state.setdefault("mensaje_exito", "")
    st.session_state.setdefault("mensaje_error", "")
    st.session_state.setdefault("apu_materiales", [])
    st.session_state.setdefault("apu_mano_obra", [])
    st.session_state.setdefault("apu_equipos", [])

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

def formatear_moneda(valor):
    return f"${float(valor):,.2f}"

def parse_float(value, default=0.0):
    if value is None: return default
    if isinstance(value, (int, float)): return float(value)
    text = str(value).strip().replace("$", "").replace(",", "").replace("MXN", "").replace("mxn", "").replace(" ", "")
    text = re.sub(r"[^0-9\.\-]", "", text)
    try: return float(text)
    except ValueError: return default

def limpiar_texto_pdf(texto):
    if not texto: return ""
    texto = str(texto)
    reemplazos = {"•": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "\u200b": "", "\r": "", "°": " grados"}
    for k, v in reemplazos.items(): texto = texto.replace(k, v)
    return texto.encode("latin-1", "replace").decode("latin-1")

def sanitize_filename(texto):
    texto = "".join(c for c in str(texto or "") if c.isalnum() or c in " -_")
    return texto.strip().replace(" ", "_")

def calcular_precio_venta(precio_unitario, utilidad_porcentaje):
    return round(float(precio_unitario) * (1 + (float(utilidad_porcentaje) / 100)), 2)

def calcular_totales(conceptos):
    if not conceptos: return 0.0, 0.0, 0.0
    df = pd.DataFrame(conceptos)
    subtotal = round(float(df["Importe"].sum()), 2)
    iva = round(subtotal * IVA_RATE, 2)
    return subtotal, iva, round(subtotal + iva, 2)

def get_folio_key(folio):
    return str(folio).strip().upper() if str(folio).strip() else BORRADOR_FOLIO_KEY

def persistir_condiciones_folio(folio_key, condiciones, plantilla):
    st.session_state.condiciones_por_folio[folio_key] = condiciones.strip() if condiciones.strip() else DEFAULT_CONDICIONES
    st.session_state.plantilla_por_folio[folio_key] = plantilla if plantilla in PLANTILLAS_CONDICIONES else "Base Besco"

def sincronizar_condiciones_con_folio(folio_actual):
    nuevo = get_folio_key(folio_actual)
    cargado = st.session_state.folio_condiciones_cargado
    if cargado != nuevo:
        persistir_condiciones_folio(cargado, st.session_state.get("editor_condiciones", DEFAULT_CONDICIONES), st.session_state.get("selector_plantilla_condiciones", "Base Besco"))
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
    if not str(datos.get("folio", "")).strip(): errores.append("Captura el folio / OT / TK.")
    if not str(datos.get("cliente_nombre", "")).strip(): errores.append("Captura el nombre del cliente.")
    if not str(datos.get("cliente_empresa", "")).strip(): errores.append("Captura la empresa / inmueble.")
    if not str(datos.get("cotiza_nombre", "")).strip(): errores.append("Captura el nombre de quien cotiza.")
    if not str(datos.get("cotiza_puesto", "")).strip(): errores.append("Captura el puesto de quien cotiza.")
    return errores

def validar_concepto(descripcion, unidad, cantidad, precio_unitario):
    errores = []
    if not str(descripcion).strip(): errores.append("Debes capturar o seleccionar la descripción del concepto.")
    if not str(unidad).strip(): errores.append("Debes capturar la unidad.")
    if float(cantidad) <= 0: errores.append("La cantidad debe ser mayor a 0.")
    if float(precio_unitario) < 0: errores.append("El precio unitario no puede ser negativo.")
    return errores

# ==========================================
# CONEXIÓN DIRECTA GOOGLE REST API (BYPASS GSPREAD)
# ==========================================
def extract_sheet_id(url_or_id):
    if "spreadsheets/d/" in str(url_or_id):
        return str(url_or_id).split("spreadsheets/d/")[1].split("/")[0]
    return str(url_or_id).strip()

def get_google_rest_token(scopes):
    if Credentials is None or Request is None:
        raise RuntimeError("Falta la librería google-auth. Revisa el requirements.txt")
    if "gcp_service_account" not in st.secrets:
        raise RuntimeError("Faltan credenciales gcp_service_account en secrets.")
    
    info = dict(st.secrets["gcp_service_account"])
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    creds.refresh(Request())
    return creds.token

def detectar_columnas_base(df):
    columnas_upper = {str(c).strip().upper(): str(c).strip() for c in df.columns}
    def buscar(candidatas, default=""):
        for c in candidatas:
            if c in columnas_upper: return columnas_upper[c]
        return default
    col_clave = buscar(["CLAVE", "ITEM", "CODIGO", "SKU"], "")
    col_desc = buscar(["CONCEPTO", "DESCRIPCION", "PRODUCTO"], "")
    col_unidad = buscar(["UNIDAD", "UOM", "UM"], "")
    col_tipo = buscar(["TIPO DE SERVICIO", "TIPO_SERVICIO", "TIPO"], "")
    if not col_clave and len(df.columns) >= 1: col_clave = df.columns[0]
    if not col_desc and len(df.columns) >= 2: col_desc = df.columns[1]
    return {"clave": col_clave, "descripcion": col_desc, "unidad": col_unidad, "tipo_servicio": col_tipo}

def detectar_columnas_region(df):
    columnas_region = []
    for col in df.columns:
        col_up = str(col).strip().upper()
        if any(k in col_up for k in ["PU", "PRECIO", "$", "TARIFA", "CENTRO", "SUR", "NORTE"]):
            columnas_region.append(col)
    if not columnas_region:
        for p in ["PRECIO UNITARIO", "PRECIO", "PU"]:
            for col in df.columns:
                if str(col).strip().upper() == p: columnas_region.append(col)
    return list(dict.fromkeys(columnas_region))

@st.cache_data(show_spinner=False, ttl=60)
def obtener_preciario_besco():
    try:
        token = get_google_rest_token(["https://www.googleapis.com/auth/spreadsheets.readonly"])
        sheet_id = extract_sheet_id(st.secrets.get("PRECIARIO_BESCO_KEY", "12Hehx2g0vZNS0FmXMeBlcF9JRstS2CZnVknItFjI7sM"))
        worksheet = str(st.secrets.get("PRECIARIO_BESCO_WORKSHEET", "Preciario Sodexo Banamex")).strip()
        
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{worksheet}"
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Error de acceso (Código {resp.status_code}): {resp.text}")
            
        data = resp.json()
        values = data.get("values", [])
        
        if not values or len(values) < 2:
            return pd.DataFrame()
            
        header = values[0]
        max_cols = len(header)
        
        # Estabilizar matriz
        rows = []
        for r in values[1:]:
            if len(r) < max_cols:
                r = r + [""] * (max_cols - len(r))
            elif len(r) > max_cols:
                r = r[:max_cols]
            rows.append(r)
            
        df_raw = pd.DataFrame(rows, columns=header)
        mapeo = detectar_columnas_base(df_raw)
        df = df_raw.copy()
        if mapeo["clave"]: df = df.rename(columns={mapeo["clave"]: "clave"})
        else: df["clave"] = ""
        if mapeo["descripcion"]: df = df.rename(columns={mapeo["descripcion"]: "descripcion"})
        if mapeo["unidad"]: df = df.rename(columns={mapeo["unidad"]: "unidad"})
        else: df["unidad"] = "S/C"
        if mapeo["tipo_servicio"]: df = df.rename(columns={mapeo["tipo_servicio"]: "tipo_servicio"})
        else: df["tipo_servicio"] = "Servicio"
        
        df["clave"] = df["clave"].fillna("").astype(str).str.strip()
        df["descripcion"] = df["descripcion"].fillna("").astype(str).str.strip()
        df["unidad"] = df["unidad"].fillna("S/C").astype(str).str.strip()
        df = df[df["descripcion"] != ""].copy()
        df.reset_index(drop=True, inplace=True)
        return df
        
    except Exception as e:
        raise RuntimeError(str(e))

def registrar_en_historial(folio, fecha_texto, cliente, empresa, nombre_cot, total, cotizador, empresa_emisora):
    try:
        token = get_google_rest_token(["https://www.googleapis.com/auth/spreadsheets"])
        sheet_id = extract_sheet_id(st.secrets.get("HISTORIAL_COTIZACIONES_KEY", "1fgHczjNYfNxxBNEnPI7YRYTZlyru8BeZOKPy317lzew"))
        worksheet = str(st.secrets.get("HISTORIAL_COTIZACIONES_WORKSHEET", "Hoja 1")).strip()
        
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{worksheet}:append?valueInputOption=USER_ENTERED"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        body = {
            "values": [[str(folio), str(fecha_texto), str(cliente), str(empresa), str(nombre_cot), round(float(total), 2), str(cotizador), str(empresa_emisora)]]
        }
        
        resp = requests.post(url, headers=headers, json=body)
        if resp.status_code != 200:
            raise RuntimeError(f"Error (Código {resp.status_code}): {resp.text}")
            
        st.session_state.mensaje_exito = "✅ Cotización guardada en el Historial de Google Sheets."
    except Exception as e:
        st.session_state.mensaje_error = f"❌ Error al guardar en Google Sheets: {e}"

# ==========================================
# GENERACIÓN DE PDF
# ==========================================
class PDFCotizacion(FPDF):
    def __init__(self, condiciones, empresa_emisora_nombre):
        super().__init__("P", "mm", "Letter")
        self.condiciones = condiciones
        self.empresa_emisora_nombre = empresa_emisora_nombre

    def header(self):
        for logo_path in ["logo besco 2026.jpeg", "logo.jpeg"]:
            if os.path.exists(logo_path):
                try:
                    self.image(logo_path, 10, 8, 45)
                    break
                except: pass
        self.set_font("Arial", "", 8)
        self.set_xy(120, 10)
        datos_empresa = EMPRESAS_EMISORAS.get(self.empresa_emisora_nombre, EMPRESAS_EMISORAS["Grupo Besco, S.A. de C.V."])
        empresa_info = f"{self.empresa_emisora_nombre}\n{datos_empresa['direccion']}\nRFC. {datos_empresa['rfc']}"
        self.multi_cell(80, 4, limpiar_texto_pdf(empresa_info), 0, "R")
        self.ln(10)

    def footer(self):
        self.set_y(-48)
        self.set_font("Arial", "I", 7)
        self.multi_cell(0, 4, limpiar_texto_pdf(self.condiciones or DEFAULT_CONDICIONES), 0, "L")

def pdf_wrap_lines(pdf, text, width):
    text = limpiar_texto_pdf(text)
    if not text: return [""]
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            test = current + " " + word
            if pdf.get_string_width(test) <= max(width - 2, 1): current = test
            else: lines.append(current); current = word
        lines.append(current)
    return lines or [""]

def draw_table_header(pdf):
    pdf.set_fill_color(54, 60, 152) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(TABLE_COLS["codigo"], 8, "CODIGO", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["concepto"], 8, "CONCEPTO", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["unidad"], 8, "UNIDAD", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["cantidad"], 8, "CANTIDAD", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["pu"], 8, "PU", 1, 0, "C", True)
    pdf.cell(TABLE_COLS["importe"], 8, "IMPORTE", 1, 1, "C", True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 8)

def draw_table_row(pdf, concepto):
    lines = pdf_wrap_lines(pdf, concepto["Concepto"], TABLE_COLS["concepto"] - 4)
    row_height = max(TABLE_MIN_ROW_HEIGHT, len(lines) * TABLE_LINE_HEIGHT + 2)
    if pdf.get_y() + row_height > 238:
        pdf.add_page()
        draw_table_header(pdf)
    x, y = pdf.get_x(), pdf.get_y()
    widths = [TABLE_COLS["codigo"], TABLE_COLS["concepto"], TABLE_COLS["unidad"], TABLE_COLS["cantidad"], TABLE_COLS["pu"], TABLE_COLS["importe"]]
    for width in widths:
        pdf.rect(x, y, width, row_height)
        x += width
    pdf.set_xy(pdf.l_margin, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["codigo"], 4, limpiar_texto_pdf(str(concepto["Item"])), 0, 0, "C")
    y_text = y + 3.2
    for line in lines:
        pdf.set_xy(pdf.l_margin + TABLE_COLS["codigo"] + 1.5, y_text)
        pdf.cell(TABLE_COLS["concepto"] - 3, 4, line, 0, 0, "L")
        y_text += TABLE_LINE_HEIGHT
    pdf.set_xy(pdf.l_margin + TABLE_COLS["codigo"] + TABLE_COLS["concepto"], y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["unidad"], 4, limpiar_texto_pdf(str(concepto["Unidad"])), 0, 0, "C")
    pdf.set_xy(pdf.l_margin + TABLE_COLS["codigo"] + TABLE_COLS["concepto"] + TABLE_COLS["unidad"], y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["cantidad"], 4, limpiar_texto_pdf(f"{float(concepto['Cantidad']):,.2f}"), 0, 0, "C")
    x_pu = pdf.l_margin + TABLE_COLS["codigo"] + TABLE_COLS["concepto"] + TABLE_COLS["unidad"] + TABLE_COLS["cantidad"]
    pdf.set_xy(x_pu, y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["pu"] - 1.5, 4, limpiar_texto_pdf(f"$ {float(concepto['Precio Venta']):,.2f}"), 0, 0, "R")
    pdf.set_xy(x_pu + TABLE_COLS["pu"], y + (row_height / 2) - 2)
    pdf.cell(TABLE_COLS["importe"] - 1.5, 4, limpiar_texto_pdf(f"$ {float(concepto['Importe']):,.2f}"), 0, 0, "R")
    pdf.set_y(y + row_height)

def generar_pdf_cotizacion(datos, conceptos, subtotal, iva, total, condiciones):
    empresa_emisora = datos.get("empresa_cotizadora", list(EMPRESAS_EMISORAS.keys())[0])
    pdf = PDFCotizacion(condiciones, empresa_emisora)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    folio_pdf = datos["folio"] if datos["folio"] else "COT-S-N"
    fecha_pdf = datos["fecha"].strftime("%d/%m/%Y") if datos["fecha"] else date.today().strftime("%d/%m/%Y")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, "CLIENTE:", 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_nombre"].upper()), 0, 0, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 5, "FECHA DE COTIZACION:", 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 5, fecha_pdf, 0, 1, "L")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, "EMPRESA:", 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_empresa"].upper()), 0, 0, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 5, "FECHA VIGENCIA:", 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 5, limpiar_texto_pdf(datos.get("vigencia", "15 DÍAS").upper()), 0, 1, "L")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, "FOLIO BESCO:", 0, 0, "R")
    pdf.set_text_color(227, 24, 55)
    pdf.cell(80, 5, limpiar_texto_pdf(folio_pdf), 0, 1, "L")
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, "ATENCION:", 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_contacto"].upper()), 0, 1, "L")
    pdf.ln(6)
    
    pdf.multi_cell(0, 5, limpiar_texto_pdf(f"Por medio de la presente y a nombre de {empresa_emisora}, presento la siguiente cotizacion:"), 0, "L")
    pdf.ln(2)
    if datos.get("nombre_cotizacion"):
        pdf.set_font("Arial", "BI", 11)
        pdf.cell(0, 5, limpiar_texto_pdf(datos["nombre_cotizacion"].upper()), 0, 1, "C")
        pdf.ln(4)
        
    draw_table_header(pdf)
    for concepto in conceptos:
        draw_table_row(pdf, concepto)
        
    if pdf.get_y() > 225: pdf.add_page()
    pdf.ln(4)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(145, 6, "SUBTOTAL", 0, 0, "R")
    pdf.cell(15, 6, "$", 0, 0, "R")
    pdf.cell(30, 6, f"{subtotal:,.2f}", 0, 1, "R")
    pdf.cell(145, 6, "IVA 16%", 0, 0, "R")
    pdf.cell(15, 6, "$", 0, 0, "R")
    pdf.cell(30, 6, f"{iva:,.2f}", 0, 1, "R")
    pdf.cell(145, 6, "TOTAL PRESUPUESTADO", 0, 0, "R")
    pdf.cell(15, 6, "$", 0, 0, "R")
    pdf.cell(30, 6, f"{total:,.2f}", 0, 1, "R")
    
    if pdf.get_y() > 205: pdf.add_page()
    pdf.ln(18)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, "ATENTAMENTE", 0, 1, "C")
    pdf.ln(12)
    pdf.cell(0, 4, "___________________________________", 0, 1, "C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, limpiar_texto_pdf(datos["cotiza_nombre"].strip().upper()), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto_pdf(datos["cotiza_puesto"].strip().upper()), 0, 1, "C")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto_pdf(EMPRESAS_EMISORAS[empresa_emisora]["nombre_corto"]), 0, 1, "C")
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# INTERFAZ STREAMLIT
# ==========================================
def render_seccion_identificacion():
    st.markdown("## 1. Identificación del cliente y persona que cotiza")
    datos = st.session_state.datos_cotizacion
    with st.container(border=True):
        st.markdown("### 🏢 Empresa Cotizadora Emisora")
        empresa_actual = datos.get("empresa_cotizadora", list(EMPRESAS_EMISORAS.keys())[0])
        idx_empresa = list(EMPRESAS_EMISORAS.keys()).index(empresa_actual) if empresa_actual in EMPRESAS_EMISORAS else 0
        col_e1, col_e2 = st.columns([2,1])
        with col_e1:
            empresa_cotizadora = st.selectbox("Seleccione la empresa emisora:", options=list(EMPRESAS_EMISORAS.keys()), index=idx_empresa)
        with col_e2:
            st.info(f"**RFC Asignado:**\n{EMPRESAS_EMISORAS[empresa_cotizadora]['rfc']}")
        st.markdown("---")
        
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        with col_g1: folio = st.text_input("Folio / OT / TK", value=datos["folio"])
        with col_g2: fecha = st.date_input("Fecha de cotización", value=datos["fecha"])
        with col_g3: vigencia = st.text_input("Vigencia", value=datos.get("vigencia", "15 DÍAS"))
        with col_g4: nombre_cotizacion = st.text_input("Nombre de Cotización", value=datos["nombre_cotizacion"])
        
        st.markdown("### Cliente")
        col_c1, col_c2 = st.columns(2)
        with col_c1: cliente_nombre = st.text_input("Nombre del cliente", value=datos["cliente_nombre"])
        with col_c2: cliente_empresa = st.text_input("Empresa / Inmueble", value=datos["cliente_empresa"])
        col_c3, col_c4, col_c5 = st.columns(3)
        with col_c3: cliente_contacto = st.text_input("Persona de contacto (Atención)", value=datos["cliente_contacto"])
        with col_c4: cliente_telefono = st.text_input("Teléfono del cliente", value=datos["cliente_telefono"])
        with col_c5: cliente_correo = st.text_input("Correo del cliente", value=datos["cliente_correo"])
        
        st.markdown("### Persona que cotiza")
        col_p1, col_p2 = st.columns(2)
        with col_p1: cotiza_nombre = st.text_input("Nombre de quien cotiza", value=datos["cotiza_nombre"])
        with col_p2: cotiza_puesto = st.text_input("Puesto", value=datos["cotiza_puesto"])
        col_p3, col_p4 = st.columns(2)
        with col_p3: cotiza_telefono = st.text_input("Teléfono de quien cotiza", value=datos["cotiza_telefono"])
        with col_p4: cotiza_correo = st.text_input("Correo de quien cotiza", value=datos["cotiza_correo"])
        
        st.session_state.datos_cotizacion.update({
            "empresa_cotizadora": empresa_cotizadora, "folio": folio.strip(), "fecha": fecha, "vigencia": vigencia.strip(),
            "cliente_nombre": cliente_nombre.strip(), "cliente_empresa": cliente_empresa.strip(),
            "cliente_contacto": cliente_contacto.strip(), "cliente_telefono": cliente_telefono.strip(),
            "cliente_correo": cliente_correo.strip(), "cotiza_nombre": cotiza_nombre.strip(),
            "cotiza_puesto": cotiza_puesto.strip(), "cotiza_telefono": cotiza_telefono.strip(),
            "cotiza_correo": cotiza_correo.strip(), "nombre_cotizacion": nombre_cotizacion.strip(),
        })

def render_selector_preciario():
    st.markdown("## 2. Captura de Conceptos")
    with st.container(border=True):
        usar_preciario = st.toggle("🚀 Habilitar Búsqueda en Preciario BESCO (Google Sheets)", value=st.session_state.toggle_preciario_besco)
        clave_preciario, tipo_servicio, descripcion, unidad, precio_unitario = "", "Servicio", "", "PZA", DEFAULT_PRECIO

        if usar_preciario:
            try:
                df_preciario = obtener_preciario_besco()
                if df_preciario.empty: st.warning("El Preciario está vacío."); usar_preciario = False
                else:
                    columnas_region = detectar_columnas_region(df_preciario)
                    if not columnas_region: st.warning("No se detectaron columnas de precio en el Preciario."); usar_preciario = False
                    else:
                        col_reg, col_busq = st.columns([1, 2])
                        with col_reg: region_seleccionada = st.selectbox("Región", options=columnas_region)
                        with col_busq: busqueda = st.text_input("Buscador:").strip().lower()

                        df_filtrado = df_preciario.copy()
                        if busqueda:
                            mask = df_filtrado["clave"].str.lower().str.contains(busqueda, na=False) | df_filtrado["descripcion"].str.lower().str.contains(busqueda, na=False)
                            df_filtrado = df_filtrado[mask]

                        if df_filtrado.empty: st.warning("No hay coincidencias.")
                        else:
                            df_filtrado["opcion_display"] = df_filtrado["clave"] + " - " + df_filtrado["descripcion"]
                            opcion_sel = st.selectbox("Selecciona un concepto:", options=df_filtrado["opcion_display"])
                            fila = df_filtrado[df_filtrado["opcion_display"] == opcion_sel].iloc[0]
                            clave_preciario, tipo_servicio, descripcion, unidad = fila["clave"], fila["tipo_servicio"], fila["descripcion"], fila["unidad"]
                            precio_unitario = parse_float(fila.get(region_seleccionada, 0), 0)

                            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                            with col_b1: st.text_input("Clave", value=clave_preciario, disabled=True)
                            with col_b2: st.text_input("Tipo", value=tipo_servicio, disabled=True)
                            with col_b3: st.text_input("Unidad", value=unidad, disabled=True)
                            st.text_area("Descripción", value=descripcion, disabled=True)
                            precio_unitario = st.number_input("Precio Base ($)", value=float(precio_unitario))
            except Exception as e:
                st.error(f"❌ Error al cargar Preciario BESCO: {e}")
                usar_preciario = False

        if not usar_preciario:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1: clave_preciario = st.text_input("Clave / Item", placeholder="Ej. SERV-001")
            with col2: tipo_servicio = st.selectbox("Tipo de Servicio", MANUAL_TIPOS_SERVICIO, index=1)
            with col3: unidad = st.selectbox("Unidad", MANUAL_UNIDADES, index=0)
            descripcion = st.text_area("Descripción de producto o servicio")
            precio_unitario = st.number_input("Precio Unitario Base ($)", min_value=0.0, value=0.0)

        st.markdown("---")
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c1: cantidad = st.number_input("Cantidad", min_value=0.01, value=1.0)
        with col_c2: utilidad_pct = st.number_input("% Utilidad a aplicar", min_value=0.0, value=DEFAULT_UTILIDAD_MANUAL)
        with col_c3:
            precio_venta_u = calcular_precio_venta(precio_unitario, utilidad_pct)
            importe_total = round(cantidad * precio_venta_u, 2)
            st.metric("Precio Venta Unitario", formatear_moneda(precio_venta_u))
            st.metric("Importe Total Concepto", formatear_moneda(importe_total))

        if st.button("➕ Agregar Concepto a Cotización", type="primary"):
            errs = validar_concepto(descripcion, unidad, cantidad, precio_unitario)
            if errs:
                for e in errs: st.error(e)
            else:
                item_num = len(st.session_state.conceptos_cotizacion) + 1
                st.session_state.conceptos_cotizacion.append({
                    "Item": item_num, "Clave": clave_preciario or f"ITEM-{item_num:02d}",
                    "Tipo Servicio": tipo_servicio, "Concepto": descripcion, "Unidad": unidad,
                    "Cantidad": cantidad, "Precio Base": precio_unitario, "Utilidad %": utilidad_pct,
                    "Precio Venta": precio_venta_u, "Importe": importe_total
                })
                st.success("✅ Concepto agregado.")
                st.rerun()

def render_tabla_conceptos():
    st.markdown("## 3. Resumen de Conceptos Agregados")
    conceptos = st.session_state.conceptos_cotizacion
    if not conceptos:
        st.info("Aún no has agregado conceptos a la cotización.")
        return 0.0, 0.0, 0.0

    df_display = pd.DataFrame(conceptos)[["Item", "Clave", "Concepto", "Unidad", "Cantidad", "Precio Venta", "Importe"]].copy()
    df_display["Precio Venta"] = df_display["Precio Venta"].apply(formatear_moneda)
    df_display["Importe"] = df_display["Importe"].apply(formatear_moneda)
    st.dataframe(df_display, use_container_width=True)

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
    folio_key = sincronizar_condiciones_con_folio(st.session_state.datos_cotizacion.get("folio", ""))
    
    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        plantilla_sel = st.selectbox("Seleccionar plantilla", options=list(PLANTILLAS_CONDICIONES.keys()))
        if st.button("Aplicar Plantilla"):
            st.session_state.editor_condiciones = PLANTILLAS_CONDICIONES[plantilla_sel]
            st.session_state.condiciones_por_folio[folio_key] = PLANTILLAS_CONDICIONES[plantilla_sel]
            st.rerun()
    with col_p2:
        st.session_state.condiciones_por_folio[folio_key] = st.text_area(
            "Condiciones Comerciales", value=st.session_state.editor_condiciones, height=140
        )

def render_seccion_generacion(subtotal, iva, total):
    st.markdown("## 5. Exportar y Registrar Cotización")
    datos = st.session_state.datos_cotizacion
    conceptos = st.session_state.conceptos_cotizacion
    condiciones = st.session_state.condiciones_por_folio.get(get_folio_key(datos.get("folio", "")), DEFAULT_CONDICIONES)

    if st.session_state.mensaje_exito: st.success(st.session_state.mensaje_exito)
    if st.session_state.mensaje_error: st.error(st.session_state.mensaje_error)

    col_gen1, col_gen2, col_gen3 = st.columns(3)

    with col_gen1:
        if st.button("📄 Generar PDF", type="primary", use_container_width=True):
            errores = validar_datos_cotizacion(datos)
            if not conceptos: errores.append("Agrega al menos un concepto.")
            if errores:
                st.session_state.mensaje_error = "Corrige:\n" + "\n".join(f"- {e}" for e in errores)
                st.rerun()
            else:
                try:
                    pdf_bytes = generar_pdf_cotizacion(datos, conceptos, subtotal, iva, total, condiciones)
                    st.session_state.pdf_bytes = pdf_bytes
                    st.session_state.pdf_filename = f"Cotizacion_{sanitize_filename(datos['folio'])}.pdf"
                    st.session_state.mensaje_exito = "PDF generado exitosamente."
                    st.session_state.mensaje_error = ""
                    st.rerun()
                except Exception as e:
                    st.session_state.mensaje_error = f"❌ Error PDF: {e}"
                    st.rerun()

    with col_gen2:
        if "pdf_bytes" in st.session_state:
            st.download_button("⬇️ Descargar PDF", data=st.session_state.pdf_bytes, file_name=st.session_state.pdf_filename, mime="application/pdf", use_container_width=True)

    with col_gen3:
        if st.button("📊 Guardar Historial Sheets", use_container_width=True):
            if not conceptos: st.session_state.mensaje_error = "Agrega conceptos primero."; st.rerun()
            fecha_str = datos["fecha"].strftime("%Y-%m-%d")
            registrar_en_historial(datos["folio"], fecha_str, datos["cliente_nombre"], datos["cliente_empresa"], datos["nombre_cotizacion"], total, datos["cotiza_nombre"], datos["empresa_cotizadora"])

    st.markdown("---")
    if st.button("🔄 Reiniciar Cotización"):
        reset_cotizacion()
        st.rerun()

def main():
    apply_dark_styles()
    init_session_state()
    
    col_logo1, col_logo2, col_logo3 = st.columns([1, 1.5, 1])
    with col_logo2:
        if os.path.exists("logo besco 2026.jpeg"): st.image("logo besco 2026.jpeg", use_container_width=True)
            
    st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>💰 Sistema de Cotizaciones | Grupo BESCO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 2rem;'>Crea cotizaciones de captura manual directa o enlazada al Preciario BESCO.</p>", unsafe_allow_html=True)

    render_seccion_identificacion()
    render_selector_preciario()
    subtotal, iva, total = render_tabla_conceptos()
    render_seccion_condiciones()
    render_seccion_generacion(subtotal, iva, total)

if __name__ == "__main__":
    main()
