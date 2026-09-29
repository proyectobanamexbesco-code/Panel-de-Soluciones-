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
# ESTILOS OSCUROS (TEMA EJECUTIVO ALTO CONTRASTE)
# ==========================================
def apply_dark_styles():
    st.markdown(
        """
        <style>
        /* Fondo principal de la aplicación */
        .stApp {
            background-color: #0B1421 !important;
        }
        
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* Márgenes del contenedor principal */
        .block-container {
            padding-top: 2rem; 
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Textos, títulos y etiquetas */
        h1, h2, h3, h4, p, label, .stMarkdown, .stText {
            color: #E2E8F0 !important;
        }

        /* Contenedores con borde (Tarjetas) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #162032 !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }

        /* Inputs, Textareas, Date y Selectbox */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="select"] > div, 
        div[data-baseweb="textarea"] > div {
            background-color: #1E293B !important;
            border: 1px solid #475569 !important;
            color: #F8FAFC !important;
            border-radius: 8px !important;
        }
        
        input, textarea, div[data-baseweb="select"] div {
            color: #F8FAFC !important;
        }
        
        input::placeholder, textarea::placeholder {
            color: #94A3B8 !important;
            opacity: 1 !important;
        }

        /* Fix para el menú desplegable (Popover) */
        div[data-baseweb="popover"] > div {
            background-color: #1E293B !important;
            border: 1px solid #475569 !important;
        }
        ul[role="listbox"] li {
            color: #F8FAFC !important;
            background-color: #1E293B !important;
        }
        ul[role="listbox"] li:hover {
            background-color: #334155 !important;
        }

        /* Botones estándar */
        div.stButton > button {
            background-color: #5B9BD5 !important;
            color: white !important;
            border: 1px solid #1F497D !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #41719C !important;
            border: 1px solid #0F243E !important;
            transform: translateY(-2px);
        }
        
        /* Botones Primarios (Añadir / Generar PDF) */
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #2563EB !important;
            border: 1px solid #1D4ED8 !important;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.4);
        }
        div.stButton > button[data-testid="baseButton-primary"]:hover {
            background-color: #1D4ED8 !important;
        }

        /* Dataframes (Tablas) */
        [data-testid="stDataFrame"] {
            background-color: #1E293B !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
        }

        /* Métricas (Dinero / Totales) */
        [data-testid="stMetricValue"] {
            color: #38BDF8 !important;
            font-weight: 800 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ==========================================
# CONSTANTES Y CONFIGURACIONES INICIALES
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

MANUAL_TIPOS_SERVICIO = ["Aire Acondicionado", "Servicio", "Producto", "Instalación", "Mantenimiento", "Obra Civil", "Otro"]
MANUAL_UNIDADES = ["PZA", "SERVICIO", "LOTE", "M2", "M3", "HORA", "DÍA", "MES", "KG", "OTRA"]
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
}

# ==========================================
# FUNCIONES AUXILIARES Y ESTADO DE SESIÓN
# ==========================================
def get_default_datos_cotizacion():
    return {
        "folio": "",
        "fecha": date.today(),
        "empresa_cotizadora": list(EMPRESAS_EMISORAS.keys())[0],
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
        "vigencia": "15 DÍAS HÁBILES",
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
    st.session_state.setdefault("apu_materiales", [])
    st.session_state.setdefault("apu_mano_obra", [])
    st.session_state.setdefault("apu_equipos", [])

def reset_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.datos_cotizacion = get_default_datos_cotizacion()
    st.session_state.apu_materiales = []
    st.session_state.apu_mano_obra = []
    st.session_state.apu_equipos = []

def formatear_moneda(valor):
    return f"${float(valor):,.2f}"

def parse_float(value, default=0.0):
    if value is None: return default
    if isinstance(value, (int, float)): return float(value)
    text = str(value).strip().replace("$", "").replace(",", "").replace("MXN", "").replace(" ", "")
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

def calcular_totales(conceptos):
    if not conceptos: return 0.0, 0.0, 0.0
    subtotal = round(float(pd.DataFrame(conceptos)["Importe"].sum()), 2)
    iva = round(subtotal * IVA_RATE, 2)
    return subtotal, iva, round(subtotal + iva, 2)

def get_folio_key(folio):
    return str(folio).strip().upper() if str(folio).strip() else BORRADOR_FOLIO_KEY

# ==========================================
# GENERACIÓN DE PDF (FPDF)
# ==========================================
class PDFCotizacion(FPDF):
    def __init__(self, condiciones, empresa_emisora_nombre):
        super().__init__("P", "mm", "Letter")
        self.condiciones = condiciones
        self.empresa_emisora_nombre = empresa_emisora_nombre

    def header(self):
        logo_paths = ["logo besco 2026.jpeg", "logo_besco_2026.jpeg", "logo_besco.jpeg", "logo.jpeg"]
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    self.image(logo_path, 10, 8, 45)
                    break
                except Exception: pass
        self.set_font("Arial", "", 8)
        self.set_text_color(0, 0, 0)
        self.set_xy(120, 10)
        datos_empresa = EMPRESAS_EMISORAS.get(self.empresa_emisora_nombre, EMPRESAS_EMISORAS["Grupo Besco, S.A. de C.V."])
        empresa_info = f"{self.empresa_emisora_nombre}\n{datos_empresa['direccion']}\nRFC. {datos_empresa['rfc']}"
        self.multi_cell(80, 4, limpiar_texto_pdf(empresa_info), 0, "R")
        self.ln(10)

    def footer(self):
        self.set_y(-48)
        self.set_font("Arial", "I", 7)
        self.multi_cell(0, 4, limpiar_texto_pdf(self.condiciones or DEFAULT_CONDICIONES), 0, "L")

def draw_table_header(pdf):
    pdf.set_fill_color(59, 130, 246)
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
            if pdf.get_string_width(test) <= max(width - 2, 1):
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines or [""]

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
    empresa_emisora = datos.get("empresa_cotizadora", list(EMPRESAS_EMISORAS.keys())[0])
    pdf = PDFCotizacion(condiciones, empresa_emisora)
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    folio_pdf = datos["folio"] if datos["folio"] else "COT-S-N"
    fecha_pdf = datos["fecha"].strftime("%d/%m/%Y") if datos["fecha"] else date.today().strftime("%d/%m/%Y")
    vigencia_pdf = datos.get("vigencia", "15 DÍAS HÁBILES").upper()
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("CLIENTE:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_nombre"].upper()), 0, 0, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 5, limpiar_texto_pdf("FECHA:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 5, limpiar_texto_pdf(fecha_pdf), 0, 1, "L")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("EMPRESA:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_empresa"].upper()), 0, 0, "L")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(45, 5, limpiar_texto_pdf("VIGENCIA:"), 0, 0, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(30, 5, limpiar_texto_pdf(vigencia_pdf), 0, 1, "L")
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(35, 5, limpiar_texto_pdf("FOLIO:"), 0, 0, "R")
    pdf.set_text_color(220, 38, 38)
    pdf.cell(80, 5, limpiar_texto_pdf(folio_pdf), 0, 1, "L")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)
    
    if datos.get("nombre_cotizacion"):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, limpiar_texto_pdf(datos["nombre_cotizacion"].upper()), 0, 1, "C")
        pdf.ln(4)
        
    draw_table_header(pdf)
    for concepto in conceptos: draw_table_row(pdf, concepto)
    
    pdf.ln(4)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(145, 6, limpiar_texto_pdf("SUBTOTAL"), 0, 0, "R")
    pdf.cell(15, 6, "$", 0, 0, "R")
    pdf.cell(30, 6, f"{subtotal:,.2f}", 0, 1, "R")
    pdf.cell(145, 6, limpiar_texto_pdf("IVA 16%"), 0, 0, "R")
    pdf.cell(15, 6, "$", 0, 0, "R")
    pdf.cell(30, 6, f"{iva:,.2f}", 0, 1, "R")
    pdf.cell(145, 6, limpiar_texto_pdf("TOTAL"), 0, 0, "R")
    pdf.cell(15, 6, "$", 0, 0, "R")
    pdf.cell(30, 6, f"{total:,.2f}", 0, 1, "R")

    pdf.ln(18)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto_pdf("ATENTAMENTE"), 0, 1, "C")
    pdf.ln(12)
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
    st.markdown("## 1. Identificación del cliente y empresa")
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
        with col_g3: vigencia = st.text_input("Vigencia", value=datos.get("vigencia", "15 DÍAS HÁBILES"))
        with col_g4: nombre_cotizacion = st.text_input("Nombre de Proyecto", value=datos["nombre_cotizacion"])
        
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
        with col_p1: cotiza_nombre = st.text_input("Tu Nombre", value=datos["cotiza_nombre"])
        with col_p2: cotiza_puesto = st.text_input("Tu Puesto", value=datos["cotiza_puesto"])

        st.session_state.datos_cotizacion.update({
            "empresa_cotizadora": empresa_cotizadora, "folio": folio.strip(), "fecha": fecha, "vigencia": vigencia.strip(),
            "cliente_nombre": cliente_nombre.strip(), "cliente_empresa": cliente_empresa.strip(),
            "cliente_contacto": cliente_contacto.strip(), "cliente_telefono": cliente_telefono.strip(),
            "cliente_correo": cliente_correo.strip(), "cotiza_nombre": cotiza_nombre.strip(),
            "cotiza_puesto": cotiza_puesto.strip(), "nombre_cotizacion": nombre_cotizacion.strip(),
        })

def render_modulo_apu():
    st.markdown("### 🛠️ Análisis de Precios Unitarios (APU)")
    st.caption("Desglosa costos directos para determinar automáticamente el Precio Unitario Final.")
    
    st.markdown("##### 1. Materiales e Insumos")
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns([2, 1, 1, 1, 1])
    with col_m1: mat_desc = st.text_input("Material / Insumo", key="apu_mat_desc")
    with col_m2: mat_unid = st.selectbox("Unidad", MANUAL_UNIDADES, key="apu_mat_unid")
    with col_m3: mat_cant = st.number_input("Cantidad / Rend.", min_value=0.0, value=1.0, step=0.1, key="apu_mat_cant")
    with col_m4: mat_costo = st.number_input("Costo Unit. ($)", min_value=0.0, value=0.0, step=10.0, key="apu_mat_costo")
    with col_m5:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Añadir Mat.") and mat_desc:
            st.session_state.apu_materiales.append({
                "Concepto": mat_desc, "Unidad": mat_unid, "Cantidad": mat_cant,
                "CostoUnit": mat_costo, "Importe": round(mat_cant * mat_costo, 2)
            })
            st.rerun()
    if st.session_state.apu_materiales:
        st.dataframe(pd.DataFrame(st.session_state.apu_materiales), use_container_width=True)
        if st.button("🗑️ Limpiar Materiales"): st.session_state.apu_materiales = []; st.rerun()

    st.markdown("##### 2. Mano de Obra")
    col_mo1, col_mo2, col_mo3, col_mo4, col_mo5 = st.columns([2, 1, 1, 1, 1])
    with col_mo1: mo_desc = st.text_input("Categoría / Personal", key="apu_mo_desc")
    with col_mo2: mo_unid = st.selectbox("Unidad ", ["HORA", "DÍA", "JORNAL", "SERVICIO"], key="apu_mo_unid")
    with col_mo3: mo_cant = st.number_input("Cantidad / Tiempo", min_value=0.0, value=1.0, step=0.1, key="apu_mo_cant")
    with col_mo4: mo_costo = st.number_input("Costo/Salario ($)", min_value=0.0, value=0.0, step=50.0, key="apu_mo_costo")
    with col_mo5:
        st.write(" ")
        st.write(" ")
        if st.button("➕ Añadir MO") and mo_desc:
            st.session_state.apu_mano_obra.append({
                "Concepto": mo_desc, "Unidad": mo_unid, "Cantidad": mo_cant,
                "CostoUnit": mo_costo, "Importe": round(mo_cant * mo_costo, 2)
            })
            st.rerun()
    if st.session_state.apu_mano_obra:
        st.dataframe(pd.DataFrame(st.session_state.apu_mano_obra), use_container_width=True)
        if st.button("🗑️ Limpiar Mano de Obra"): st.session_state.apu_mano_obra = []; st.rerun()

    costo_dir = sum(i["Importe"] for i in st.session_state.apu_materiales) + sum(i["Importe"] for i in st.session_state.apu_mano_obra)
    
    st.markdown("##### 3. Utilidad sobre APU")
    col_ind1, col_ind2, col_ind3 = st.columns(3)
    with col_ind1: pct_ind = st.number_input("% Costo Indirecto", min_value=0.0, value=10.0, step=0.5)
    with col_ind2: pct_ut = st.number_input("% Utilidad", min_value=0.0, value=15.0, step=0.5)
    with col_ind3:
        sub_ind = costo_dir + (costo_dir * pct_ind / 100)
        pu_calc = round(sub_ind + (sub_ind * pct_ut / 100), 2)
        
    st.info(f"**PRECIO UNITARIO FINAL CALCULADO:** **${pu_calc:,.2f}**")
    return pu_calc

def render_captura_conceptos():
    st.markdown("## 2. Captura de Conceptos")
    modo = st.radio("Modalidad:", ["Captura Directa", "Análisis APU"], horizontal=True)
    
    with st.container(border=True):
        if modo == "Captura Directa":
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1: clave = st.text_input("Clave", placeholder="Ej. SERV-01")
            with col2: tipo = st.selectbox("Tipo de Servicio", MANUAL_TIPOS_SERVICIO)
            with col3: unidad = st.selectbox("Unidad", MANUAL_UNIDADES)
            desc = st.text_input("Descripción del concepto")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1: cant = st.number_input("Cantidad", min_value=0.01, value=1.0)
            with col_c2: pu = st.number_input("Precio Unitario Venta ($)", min_value=0.0, value=0.0)
            with col_c3:
                st.write(" ")
                st.write(" ")
                if st.button("➕ Agregar Concepto Directo", type="primary", use_container_width=True) and desc:
                    st.session_state.conceptos_cotizacion.append({
                        "Item": len(st.session_state.conceptos_cotizacion)+1, "Clave": clave or "S-C",
                        "Concepto": desc, "Unidad": unidad, "Cantidad": cant, "Precio Venta": pu,
                        "Importe": cant * pu, "Modalidad": "Directa"
                    })
                    st.rerun()
        else:
            col_a1, col_a2, col_a3 = st.columns([1, 2, 1])
            with col_a1: clave_apu = st.text_input("Clave APU")
            with col_a2: desc_apu = st.text_input("Descripción del Trabajo APU")
            with col_a3: unid_apu = st.selectbox("Unidad APU", MANUAL_UNIDADES)
            
            pu_calculado = render_modulo_apu()
            st.markdown("---")
            col_ap1, col_ap2 = st.columns(2)
            with col_ap1: cant_apu = st.number_input("Cantidad de este concepto", min_value=0.01, value=1.0)
            with col_ap2:
                st.write(" ")
                st.write(" ")
                if st.button("➕ Agregar APU a Cotización", type="primary", use_container_width=True) and desc_apu:
                    st.session_state.conceptos_cotizacion.append({
                        "Item": len(st.session_state.conceptos_cotizacion)+1, "Clave": clave_apu or "APU-X",
                        "Concepto": desc_apu, "Unidad": unid_apu, "Cantidad": cant_apu, "Precio Venta": pu_calculado,
                        "Importe": cant_apu * pu_calculado, "Modalidad": "APU"
                    })
                    st.session_state.apu_materiales = []
                    st.session_state.apu_mano_obra = []
                    st.rerun()

def render_tabla_conceptos():
    st.markdown("## 3. Resumen de Cotización")
    if not st.session_state.conceptos_cotizacion:
        st.info("Aún no has agregado conceptos a la cotización.")
        return 0.0, 0.0, 0.0

    df = pd.DataFrame(st.session_state.conceptos_cotizacion)
    df_display = df[["Item", "Clave", "Concepto", "Unidad", "Cantidad", "Precio Venta", "Importe"]].copy()
    df_display["Precio Venta"] = df_display["Precio Venta"].apply(formatear_moneda)
    df_display["Importe"] = df_display["Importe"].apply(formatear_moneda)
    st.dataframe(df_display, use_container_width=True)

    if st.button("🗑️ Eliminar Último Concepto"):
        st.session_state.conceptos_cotizacion.pop()
        st.rerun()

    subtotal, iva, total = calcular_totales(st.session_state.conceptos_cotizacion)
    st.markdown("---")
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Subtotal", formatear_moneda(subtotal))
    col_t2.metric("IVA (16%)", formatear_moneda(iva))
    col_t3.metric("TOTAL PRESUPUESTADO", formatear_moneda(total))
    return subtotal, iva, total

def render_generacion(subtotal, iva, total):
    st.markdown("## 4. Exportar Cotización")
    condiciones = st.text_area("Condiciones Comerciales", value=st.session_state.editor_condiciones, height=120)
    st.session_state.editor_condiciones = condiciones
    
    if st.button("📄 Generar PDF de Cotización", type="primary", use_container_width=True):
        if not st.session_state.conceptos_cotizacion:
            st.error("Agrega al menos un concepto a la cotización antes de generar.")
        else:
            pdf_bytes = generar_pdf_cotizacion(
                st.session_state.datos_cotizacion, st.session_state.conceptos_cotizacion, 
                subtotal, iva, total, st.session_state.editor_condiciones
            )
            folio_str = st.session_state.datos_cotizacion['folio'] or "S-N"
            st.download_button(
                label="⬇️ Descargar PDF", data=pdf_bytes, file_name=f"Cotizacion_{folio_str}.pdf",
                mime="application/pdf", use_container_width=True
            )
            
    st.markdown("---")
    if st.button("🔄 Reiniciar / Nueva Cotización"):
        reset_cotizacion()
        st.rerun()

# ==========================================
# MAIN
# ==========================================
def main():
    apply_dark_styles()
    init_session_state()
    
    # 1. Logo centrado en la cabecera
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if os.path.exists("logo besco 2026.jpeg"):
            st.image("logo besco 2026.jpeg", use_container_width=True)
            
    # 2. Títulos integrados con diseño ejecutivo
    st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>💰 Sistema de Cotizaciones | Grupo BESCO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94A3B8; margin-bottom: 2rem;'>Crea cotizaciones directas o basadas en Análisis de Precios Unitarios (APU).</p>", unsafe_allow_html=True)
    
    render_seccion_identificacion()
    render_captura_conceptos()
    subtotal, iva, total = render_tabla_conceptos()
    render_generacion(subtotal, iva, total)

if __name__ == "__main__":
    main()
