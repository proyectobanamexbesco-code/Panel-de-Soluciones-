"""
cotizaciones.py — Módulo de Cotizaciones · Grupo Besco S.A. de C.V.
Versión consolidada: captura manual + Preciario (Sodexo/BESCO),
generación de PDF con FPDF y persistencia en Google Sheets.
"""

import io
import json
import os
import unicodedata
from datetime import date

import pandas as pd
import streamlit as st

try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_DISPONIBLE = True
except ImportError:
    gspread = None
    Credentials = None
    GSPREAD_DISPONIBLE = False


# ══════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Cotizaciones · Besco",
    page_icon="📋",
    layout="wide"
)


# ══════════════════════════════════════════
# CONSTANTES
# ══════════════════════════════════════════
EMPRESA_NOMBRE = "Grupo Besco S.A. de C.V."
EMPRESA_DIRECCION = "Jose Ignacio Bartolache 1910, CDMX"
EMPRESA_EMAIL = "contacto@besco.mx"

IVA = 0.16

TIPOS_SERVICIO = [
    "Aire Acondicionado", "Eléctrico", "Luminarias",
    "Hidrosanitario", "Acabados", "Otros"
]

OPCIONES_UNIDAD = [
    "Pieza", "Caja", "Metro", "Metro Lineal", "Kilo",
    "Metro Cuadrado (m2)", "Litro", "Servicio", "Hora", "Lote"
]

REGIONES_PRECIARIO = [
    "PU BAJÍO", "PU NOROESTE", "PU PENINSULAR",
    "PU METRO NORTE & SUR", "PU OCCIDENTE",
    "PU SUR", "PU NORTE", "PU CENTRO"
]

PUESTOS_COTIZADOR = [
    "Gerente Regional", "Gerente de Servicio",
    "Jefe de Oficina", "Supervisor", "Otro"
]

OPCIONES_PAGO = [
    "30% Anticipo / 70% al término",
    "50% Anticipo / 50% al término",
    "100% al término",
    "A convenir"
]

CLAVES_URL_PRECIARIO = [
    "BESCO_PRECIARIO_URL", "PRECIARIO_BESCO_URL",
    "SODEXO_PRECIARIO_URL", "GOOGLE_SHEETS_URL"
]
CLAVES_KEY_PRECIARIO = [
    "BESCO_PRECIARIO_KEY", "PRECIARIO_BESCO_KEY",
    "SODEXO_PRECIARIO_KEY", "GOOGLE_SHEETS_KEY"
]
CLAVES_WORKSHEET_PRECIARIO = [
    "BESCO_PRECIARIO_WORKSHEET", "PRECIARIO_BESCO_WORKSHEET",
    "SODEXO_WORKSHEET", "GOOGLE_SHEETS_WORKSHEET"
]
CLAVES_HISTORIAL_WORKSHEET = [
    "HISTORIAL_WORKSHEET", "BESCO_HISTORIAL_WORKSHEET"
]

LOGO_PATH = "logo_besco.png"


# ══════════════════════════════════════════
# ESTADO INICIAL
# ══════════════════════════════════════════
def inicializar_session_state():
    defaults = {
        "conceptos": [],
        "usar_preciario": False,
        "mensaje_exito": None,
        "mensaje_error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def limpiar_conceptos():
    st.session_state.conceptos = []


# ══════════════════════════════════════════
# UTILIDADES GENERALES
# ══════════════════════════════════════════
def limpiar_texto(texto: str) -> str:
    """Elimina caracteres no Latin-1 para compatibilidad con FPDF."""
    if not isinstance(texto, str):
        texto = str(texto)
    return unicodedata.normalize("NFKD", texto).encode("latin-1", "replace").decode("latin-1")


def formatear_moneda(valor: float) -> str:
    return f"${float(valor):,.2f}"


def calcular_precio_venta(costo: float, utilidad_pct: float) -> float:
    return round(costo * (1 + utilidad_pct / 100), 2)


def generar_folio(nombre_cotizador: str, fecha: date,
                  cliente_base: str, descripcion: str) -> str:
    if nombre_cotizador and cliente_base and descripcion:
        iniciales = "".join(p[0].upper() for p in nombre_cotizador.split() if p)
        cliente_cod = cliente_base.replace(" ", "").upper()[:6]
        desc_cod = descripcion.replace(" ", "").upper()[:6]
        return f"{iniciales}-{fecha.strftime('%d%m%Y')}-{cliente_cod}-{desc_cod}"
    return "Completar datos para generar folio"


# ══════════════════════════════════════════
# ACCESO A SECRETS / ENV
# ══════════════════════════════════════════
def valor_secreto(*claves, default=None):
    for clave in claves:
        try:
            if clave in st.secrets:
                return st.secrets[clave]
        except Exception:
            pass
        valor_env = os.getenv(clave)
        if valor_env:
            return valor_env
    return default


# ══════════════════════════════════════════
# GOOGLE SHEETS — CREDENCIALES Y CLIENTE
# ══════════════════════════════════════════
def obtener_credenciales_gcp():
    if not GSPREAD_DISPONIBLE:
        raise RuntimeError("Instala 'gspread' y 'google-auth' en requirements.txt.")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    for clave in ("gcp_service_account", "GOOGLE_SERVICE_ACCOUNT"):
        try:
            if clave in st.secrets:
                info = dict(st.secrets[clave])
                return Credentials.from_service_account_info(info, scopes=scopes)
        except Exception:
            pass

    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_json:
        info = json.loads(service_json)
        return Credentials.from_service_account_info(info, scopes=scopes)

    raise RuntimeError(
        "No se encontraron credenciales de Google en st.secrets ni en variables de entorno."
    )


def construir_cliente_gspread():
    creds = obtener_credenciales_gcp()
    # gspread.authorize() deprecado desde v5; se usa Client directamente
    return gspread.Client(auth=creds)


def _abrir_spreadsheet(gc, claves_url: list, claves_key: list):
    url = valor_secreto(*claves_url, default=None)
    if url:
        return gc.open_by_url(url)
    key = valor_secreto(*claves_key, default=None)
    if key:
        return gc.open_by_key(key)
    raise RuntimeError(
        "No se encontró URL ni clave del spreadsheet en st.secrets o variables de entorno."
    )


# ══════════════════════════════════════════
# PRECIARIO — CARGA Y NORMALIZACIÓN
# ══════════════════════════════════════════
def _cargar_registros_preciario() -> list:
    gc = construir_cliente_gspread()
    spreadsheet = _abrir_spreadsheet(gc, CLAVES_URL_PRECIARIO, CLAVES_KEY_PRECIARIO)
    ws_name = valor_secreto(*CLAVES_WORKSHEET_PRECIARIO, default=None)
    worksheet = (
        spreadsheet.worksheet(ws_name)
        if ws_name
        else spreadsheet.get_worksheet(0)
    )
    return worksheet.get_all_records()


def normalizar_preciario(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza encabezados y tipos del preciario."""
    df = df.copy()
    mapa = {}
    for col in df.columns:
        cn = str(col).strip().lower()
        if cn in {"item", "id", "clave", "codigo", "código", "sku"}:
            mapa[col] = "item"
        elif cn in {"concepto", "descripcion", "descripción", "producto", "servicio"}:
            mapa[col] = "Concepto"
        elif cn in {"unidad", "uom", "um"}:
            mapa[col] = "Unidad"
    df = df.rename(columns=mapa)

    if "Concepto" not in df.columns:
        raise ValueError(
            f"El preciario no tiene columna de concepto/descripción. "
            f"Columnas detectadas: {', '.join(str(c) for c in df.columns)}"
        )
    if "item" not in df.columns:
        df["item"] = ""
    if "Unidad" not in df.columns:
        df["Unidad"] = "Pieza"

    # Limpiar columnas de precio (regiones)
    for col in df.columns:
        if col not in ("item", "Concepto", "Unidad"):
            df[col] = (
                df[col].astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df = df[df["Concepto"].astype(str).str.strip() != ""].reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False, ttl=300)
def cargar_preciario() -> pd.DataFrame:
    """Carga el preciario desde Google Sheets con caché de 5 min."""
    registros = _cargar_registros_preciario()
    if not registros:
        return pd.DataFrame()
    df = pd.DataFrame(registros)
    return normalizar_preciario(df)


# ══════════════════════════════════════════
# HISTORIAL — GUARDADO EN GOOGLE SHEETS
# ══════════════════════════════════════════
def guardar_historial(df_conceptos: pd.DataFrame, meta: dict):
    """
    Agrega filas al historial de cotizaciones en Google Sheets.
    No lanza excepción al fallar; registra el mensaje en session_state.
    """
    try:
        gc = construir_cliente_gspread()
        spreadsheet = _abrir_spreadsheet(gc, CLAVES_URL_PRECIARIO, CLAVES_KEY_PRECIARIO)

        ws_name = valor_secreto(*CLAVES_HISTORIAL_WORKSHEET, default="Historial")
        try:
            ws = spreadsheet.worksheet(ws_name)
        except Exception:
            ws = spreadsheet.add_worksheet(ws_name, rows=1000, cols=30)

        filas_existentes = ws.get_all_values()
        encabezado = [
            "Folio", "Fecha", "Cliente", "Institución", "Dirección",
            "Tel. Cliente", "Email Cliente",
            "Cotizador", "Puesto", "Email Cotizador", "Tel. Cotizador",
            "Proyecto", "Ubicación",
            "Tipo", "Concepto", "Cant.", "Unidad",
            "Costo U.", "Precio Venta", "Importe",
            "Subtotal", "IVA", "Total",
            "Moneda", "Tiempo Entrega", "Pago", "Vigencia", "Garantía"
        ]
        if not filas_existentes:
            ws.append_row(encabezado)

        filas_nuevas = []
        for _, fila in df_conceptos.iterrows():
            filas_nuevas.append([
                meta["folio"], str(meta["fecha"]),
                meta["nombre_cliente"], meta["institucion_cliente"],
                meta["direccion_cliente"], meta["telefono_cliente"],
                meta["email_cliente"],
                meta["nombre_cotizador"], meta["puesto_cotizador"],
                meta["email_cotizador"], meta["telefono_cotizador"],
                meta["descripcion_proyecto"], meta["ubicacion"],
                str(fila.get("Tipo", "")), str(fila.get("Concepto", "")),
                float(fila.get("Cant.", 0)), str(fila.get("Unidad", "")),
                float(fila.get("Costo U.", 0)), float(fila.get("Precio Venta", 0)),
                float(fila.get("Importe", 0)),
                meta["subtotal"], meta["iva"], meta["total"],
                meta["tipo_moneda"], meta["tiempo_entrega"],
                meta["condiciones_pago"], meta["vigencia"], meta["garantia"]
            ])

        if filas_nuevas:
            ws.append_rows(filas_nuevas)

        st.session_state.mensaje_exito = (
            f"✅ Historial guardado correctamente ({len(filas_nuevas)} renglones)."
        )
    except Exception as e:
        st.session_state.mensaje_error = f"⚠️ No se pudo guardar el historial: {e}"


# ══════════════════════════════════════════
# GENERACIÓN DE PDF
# ══════════════════════════════════════════
def generar_pdf(
    df_conceptos: pd.DataFrame,
    meta: dict,
    subtotal: float,
    iva: float,
    total: float
) -> bytes:
    """Genera el PDF de cotización y lo devuelve como bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Encabezado ──
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=5, w=50)

    pdf.set_fill_color(230, 230, 230)
    pdf.rect(10, 35, 190, 32, "DF")
    pdf.set_y(37)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 5, limpiar_texto(EMPRESA_NOMBRE))
    pdf.cell(80, 5, f"Fecha: {meta['fecha'].strftime('%d/%m/%Y')}", ln=True, align="R")
    pdf.cell(110, 5, limpiar_texto(EMPRESA_DIRECCION))
    pdf.cell(80, 5, f"No. Presupuesto: {limpiar_texto(meta['folio'])}", ln=True, align="R")
    pdf.cell(110, 5, limpiar_texto(f"Email: {meta['email_cotizador']}"))
    pdf.cell(80, 5, f"Cotizador: {limpiar_texto(meta['nombre_cotizador'])}", ln=True, align="R")

    # ── Datos cliente / proyecto ──
    pdf.set_y(72)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 5, "DATOS DEL CLIENTE:")
    pdf.cell(90, 5, "PROYECTO:", ln=True)
    pdf.set_font("Helvetica", size=9)

    y_inicio = pdf.get_y()
    pdf.set_xy(10, y_inicio)
    pdf.multi_cell(
        90, 4,
        f"Cliente: {limpiar_texto(meta['nombre_cliente'])}\n"
        f"Inst: {limpiar_texto(meta['institucion_cliente'])}\n"
        f"Dir: {limpiar_texto(meta['direccion_cliente'])}\n"
        f"Tel: {limpiar_texto(meta['telefono_cliente'])}\n"
        f"Email: {limpiar_texto(meta['email_cliente'])}"
    )
    y_left = pdf.get_y()
    pdf.set_xy(105, y_inicio)
    pdf.multi_cell(
        95, 4,
        f"Proyecto: {limpiar_texto(meta['descripcion_proyecto'])}\n"
        f"Ubicacion: {limpiar_texto(meta['ubicacion'])}\n"
        f"Cotizador: {limpiar_texto(meta['nombre_cotizador'])}\n"
        f"Puesto: {limpiar_texto(meta['puesto_cotizador'])}\n"
        f"Tel: {limpiar_texto(meta['telefono_cotizador'])}"
    )
    pdf.set_y(max(y_left, pdf.get_y()) + 4)

    # ── Tabla de conceptos ──
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(28, 6, "Tipo", 1, 0, "L", True)
    pdf.cell(72, 6, "Concepto", 1, 0, "L", True)
    pdf.cell(14, 6, "Cant.", 1, 0, "C", True)
    pdf.cell(18, 6, "Unidad", 1, 0, "C", True)
    pdf.cell(28, 6, "Precio Venta", 1, 0, "R", True)
    pdf.cell(30, 6, "Importe", 1, 1, "R", True)

    pdf.set_font("Helvetica", size=8)
    for _, fila in df_conceptos.iterrows():
        if pdf.get_y() > 250:
            pdf.add_page()

        y_s = pdf.get_y()
        pdf.set_xy(10, y_s + 1)
        pdf.multi_cell(28, 4, limpiar_texto(str(fila.get("Tipo", ""))))
        y_t = pdf.get_y()
        pdf.set_xy(38, y_s + 1)
        pdf.multi_cell(72, 4, limpiar_texto(str(fila.get("Concepto", ""))))
        y_c = pdf.get_y()
        pdf.set_xy(128, y_s + 1)
        pdf.multi_cell(18, 4, limpiar_texto(str(fila.get("Unidad", ""))), align="C")
        y_u = pdf.get_y()

        h = max(y_t, y_c, y_u) - y_s + 1.5
        if h < 6:
            h = 6

        pdf.set_xy(110, y_s)
        pdf.cell(18, h, f"{float(fila.get('Cant.', 0)):.2f}", 0, 0, "C")
        pdf.set_xy(146, y_s)
        pdf.cell(28, h, f"${float(fila.get('Precio Venta', 0)):,.2f}", 0, 0, "R")
        pdf.set_xy(174, y_s)
        pdf.cell(26, h, f"${float(fila.get('Importe', 0)):,.2f}", 0, 1, "R")

        pdf.rect(10, y_s, 28, h)
        pdf.rect(38, y_s, 72, h)
        pdf.rect(110, y_s, 18, h)
        pdf.rect(128, y_s, 18, h)
        pdf.rect(146, y_s, 28, h)
        pdf.rect(174, y_s, 26, h)

        pdf.set_y(y_s + h)

    # ── Totales ──
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(140, 5, "")
    pdf.cell(30, 5, "Subtotal:", 1, 0)
    pdf.cell(30, 5, f"${subtotal:,.2f}", 1, 1, "R")
    pdf.cell(140, 5, "")
    pdf.cell(30, 5, "I.V.A. 16%:", 1, 0)
    pdf.cell(30, 5, f"${iva:,.2f}", 1, 1, "R")
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(140, 5, "")
    pdf.cell(30, 5, "TOTAL:", 1, 0, "L", True)
    pdf.cell(30, 5, f"${total:,.2f}", 1, 1, "R", True)

    # ── Condiciones comerciales ──
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "CONDICIONES COMERCIALES:", ln=True)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 4, f"- Moneda: {limpiar_texto(meta['tipo_moneda'])}  |  Tiempo de ejecucion: {limpiar_texto(meta['tiempo_entrega'])}", ln=True)
    pdf.cell(0, 4, f"- Pago: {limpiar_texto(meta['condiciones_pago'])}  |  Vigencia: {limpiar_texto(meta['vigencia'])}  |  Garantia: {limpiar_texto(meta['garantia'])}", ln=True)

    # ── Firma ──
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 4, "ATENTAMENTE", ln=True, align="C")
    pdf.set_text_color(0, 100, 180)
    pdf.cell(0, 4, limpiar_texto(meta["nombre_cotizador"].upper()), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 4, limpiar_texto(meta["puesto_cotizador"]), ln=True, align="C")
    pdf.cell(0, 4, limpiar_texto(meta["email_cotizador"]), ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")


# ══════════════════════════════════════════
# INICIALIZAR ESTADO
# ══════════════════════════════════════════
inicializar_session_state()


# ══════════════════════════════════════════
# ENCABEZADO DE EMPRESA
# ══════════════════════════════════════════
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.markdown(f"### {EMPRESA_NOMBRE}")
    st.markdown(f"**Dirección:** {EMPRESA_DIRECCION}")

folio_placeholder = col_h2.empty()
st.title("📋 Cotizaciones")


# ══════════════════════════════════════════
# SECCIÓN 1 — DATOS DEL PROYECTO Y COTIZADOR
# ══════════════════════════════════════════
st.header("1. Datos del Proyecto y Cotizador")

c1, c2 = st.columns(2)

with c1:
    nombre_cotizador = st.text_input("Responsable de cotización", value="Gerardo Méndez")
    puesto_cotizador = st.selectbox("Puesto", PUESTOS_COTIZADOR)
    email_cotizador = st.text_input("E-mail cotizador", value="gerardo.mendez@besco.mx")
    descripcion_proyecto = st.text_input("Descripción del Proyecto")

with c2:
    fecha = st.date_input("Fecha", value=date.today())
    telefono_cotizador = st.text_input("Teléfono Cotizador")
    ubicacion = st.text_input("Ubicación del Servicio")


# ══════════════════════════════════════════
# SECCIÓN 2 — DATOS DEL CLIENTE
# ══════════════════════════════════════════
st.header("2. Datos del Cliente")

cc1, cc2 = st.columns(2)

with cc1:
    nombre_cliente = st.text_input("Nombre cliente")
    institucion_cliente = st.text_input("Institución")
    direccion_cliente = st.text_input("Dirección cliente")

with cc2:
    telefono_cliente = st.text_input("Teléfono cliente")
    email_cliente = st.text_input("E-mail cliente")

# Folio automático
cliente_base = institucion_cliente or nombre_cliente
folio = generar_folio(nombre_cotizador, fecha, cliente_base, descripcion_proyecto)
folio_placeholder.success(f"**Folio:** {folio}")


# ══════════════════════════════════════════
# SECCIÓN 3 — CAPTURA DE CONCEPTOS
# ══════════════════════════════════════════
st.header("3. Captura de Conceptos")

usar_preciario = st.toggle(
    "📋 Habilitar Preciario Sodexo / BESCO",
    value=st.session_state.usar_preciario,
    key="toggle_preciario"
)
st.session_state.usar_preciario = usar_preciario

# Variables del concepto con valores por defecto
concepto_val = ""
item_final = ""
unidad_val = OPCIONES_UNIDAD[0]
costo_val = 0.0
tipo_servicio = TIPOS_SERVICIO[0]
region_seleccionada = None

if usar_preciario:
    try:
        df_preciario = cargar_preciario()

        if df_preciario.empty:
            st.warning("⚠️ El preciario está vacío o no se encontraron registros.")
            raise ValueError("preciario_vacio")

        # Detectar columnas de región disponibles en el sheet
        columnas_region = [
            c for c in df_preciario.columns
            if c not in ("item", "Concepto", "Unidad")
        ]
        regiones_disponibles = (
            [r for r in REGIONES_PRECIARIO if r in columnas_region]
            or columnas_region
        )

        col_sel1, col_sel2, col_sel3 = st.columns([1.2, 0.9, 1.9])

        with col_sel1:
            tipo_servicio = st.selectbox("Tipo de Servicio", TIPOS_SERVICIO)
            if regiones_disponibles:
                region_seleccionada = st.selectbox("📍 Región de Tarifas", regiones_disponibles)
            else:
                st.info("No se detectaron columnas de región en el preciario.")

        with col_sel3:
            df_preciario["_buscador"] = (
                df_preciario["item"].astype(str) + " - " +
                df_preciario["Concepto"].astype(str)
            )
            lista_opciones = ["-- Selecciona un concepto --"] + (
                df_preciario["_buscador"].dropna().astype(str).unique().tolist()
            )
            concepto_sel = st.selectbox(
                "🔍 Buscador (escribe letra o ítem)", lista_opciones
            )

        if concepto_sel != "-- Selecciona un concepto --":
            fila_p = df_preciario[df_preciario["_buscador"] == concepto_sel].iloc[0]
            concepto_val = str(fila_p.get("Concepto", "")).strip()
            item_final = str(fila_p.get("item", "")).strip()
            unidad_val = str(fila_p.get("Unidad", OPCIONES_UNIDAD[0])).strip()

            if region_seleccionada:
                raw = (
                    str(fila_p.get(region_seleccionada, "0"))
                    .replace("$", "").replace(",", "").strip()
                )
                try:
                    costo_val = float(raw)
                except ValueError:
                    costo_val = 0.0

        with col_sel2:
            item_final = st.text_input("📦 Item", value=item_final)

    except Exception as e:
        if "preciario_vacio" not in str(e):
            st.error(f"No se pudo cargar el preciario: {e}")
            st.warning("Usando captura manual como respaldo.")
        usar_preciario = False

if not usar_preciario:
    cs1, cs2 = st.columns([1, 2])
    with cs1:
        tipo_servicio = st.selectbox("Tipo de Servicio", TIPOS_SERVICIO)
    with cs2:
        concepto_val = st.text_input("Concepto o descripción detallada")

# ── Campos comunes: cantidad, unidad, costo, utilidad ──
st.markdown("---")
cx1, cx2, cx3, cx4 = st.columns([1, 1.5, 1.2, 1.2])

cantidad = cx1.number_input(
    "Cantidad", min_value=0.01, value=1.00, step=0.50, format="%.2f"
)

opciones_unidad_dinamicas = list(OPCIONES_UNIDAD)
if unidad_val and unidad_val not in opciones_unidad_dinamicas:
    opciones_unidad_dinamicas.append(unidad_val)
idx_unidad = (
    opciones_unidad_dinamicas.index(unidad_val)
    if unidad_val in opciones_unidad_dinamicas
    else 0
)
tipo_unidad = cx2.selectbox("Unidad", opciones_unidad_dinamicas, index=idx_unidad)

costo_unitario = cx3.number_input(
    "Costo U. ($)", min_value=0.0, value=float(costo_val), step=0.01, format="%.2f"
)

utilidad_default = 0.0 if usar_preciario else 23.50
margen_utilidad = cx4.number_input(
    "Utilidad (%)", min_value=0.0, value=utilidad_default, step=0.50, format="%.2f"
)

precio_venta_u = calcular_precio_venta(costo_unitario, margen_utilidad)
importe_linea = round(precio_venta_u * cantidad, 2)

col_prev1, col_prev2 = st.columns(2)
col_prev1.metric("Precio venta unitario", formatear_moneda(precio_venta_u))
col_prev2.metric("Importe de esta línea", formatear_moneda(importe_linea))

st.markdown("")
if st.button("➕ Agregar línea a cotización", type="primary", use_container_width=True):
    errores = []
    if not concepto_val.strip() or concepto_val == "-- Selecciona un concepto --":
        errores.append("Ingresa o selecciona un concepto válido.")
    if cantidad <= 0:
        errores.append("La cantidad debe ser mayor a cero.")

    if errores:
        for e in errores:
            st.error(f"❌ {e}")
    else:
        concepto_completo = (
            f"{item_final} - {concepto_val}" if item_final else concepto_val
        )
        st.session_state.conceptos.append({
            "Tipo": tipo_servicio,
            "Concepto": concepto_completo,
            "Cant.": round(float(cantidad), 2),
            "Unidad": tipo_unidad,
            "Costo U.": round(float(costo_unitario), 2),
            "Precio Venta": round(float(precio_venta_u), 2),
            "Importe": round(float(importe_linea), 2),
        })
        st.rerun()


# ══════════════════════════════════════════
# SECCIÓN 4 — RESUMEN Y ACCIONES
# ══════════════════════════════════════════
if st.session_state.conceptos:
    st.header("4. Resumen de Cotización")

    df_editado = st.data_editor(
        pd.DataFrame(st.session_state.conceptos),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_conceptos"
    )

    # Recalcular importe tras edición manual en la tabla
    df_editado["Importe"] = (
        df_editado["Cant."].astype(float) * df_editado["Precio Venta"].astype(float)
    ).round(2)

    subtotal = float(df_editado["Importe"].sum())
    iva_monto = round(subtotal * IVA, 2)
    total = round(subtotal + iva_monto, 2)

    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Subtotal", formatear_moneda(subtotal))
    col_t2.metric(f"IVA {int(IVA*100)}%", formatear_moneda(iva_monto))
    col_t3.metric("TOTAL", formatear_moneda(total))

    # ── Condiciones comerciales ──
    st.header("5. Condiciones Comerciales")

    co1, co2 = st.columns(2)
    with co1:
        tipo_moneda = st.selectbox("Moneda", ["Pesos Mexicanos", "Dólares de Estados Unidos"])
        dias_ejecucion = st.number_input("Días de ejecución", min_value=1, value=15)
        tiempo_entrega = f"{int(dias_ejecucion)} días hábiles"
        condiciones_pago = st.selectbox("Forma de pago", OPCIONES_PAGO)
    with co2:
        dias_vigencia = st.number_input("Vigencia (días)", min_value=1, value=15)
        vigencia = f"{int(dias_vigencia)} días hábiles"
        garantia = st.text_input("Garantía", value="30 días sobre mano de obra")

    # ── Mensajes de estado ──
    if st.session_state.mensaje_exito:
        st.success(st.session_state.mensaje_exito)
        st.session_state.mensaje_exito = None
    if st.session_state.mensaje_error:
        st.warning(st.session_state.mensaje_error)
        st.session_state.mensaje_error = None

    # ── Diccionario de metadatos ──
    meta = {
        "folio": folio,
        "fecha": fecha,
        "nombre_cliente": nombre_cliente,
        "institucion_cliente": institucion_cliente,
        "direccion_cliente": direccion_cliente,
        "telefono_cliente": telefono_cliente,
        "email_cliente": email_cliente,
        "nombre_cotizador": nombre_cotizador,
        "puesto_cotizador": puesto_cotizador,
        "email_cotizador": email_cotizador,
        "telefono_cotizador": telefono_cotizador,
        "descripcion_proyecto": descripcion_proyecto,
        "ubicacion": ubicacion,
        "subtotal": subtotal,
        "iva": iva_monto,
        "total": total,
        "tipo_moneda": tipo_moneda,
        "tiempo_entrega": tiempo_entrega,
        "condiciones_pago": condiciones_pago,
        "vigencia": vigencia,
        "garantia": garantia,
    }

    # ── Botones de acción ──
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if FPDF_DISPONIBLE:
            try:
                bytes_pdf = generar_pdf(df_editado, meta, subtotal, iva_monto, total)
                st.download_button(
                    label="⚡ Guardar Historial y Descargar PDF",
                    data=bytes_pdf,
                    file_name=f"Cotizacion_{folio}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    on_click=guardar_historial,
                    args=(df_editado, meta)
                )
            except Exception as e:
                st.error(f"Error al generar el PDF: {e}")
        else:
            st.warning("Instala 'fpdf2' en requirements.txt para habilitar el PDF.")

    with col_btn2:
        csv = df_editado.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"Cotizacion_{folio}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_btn3:
        if st.button("♻️ Limpiar cotización", use_container_width=True):
            limpiar_conceptos()
            st.rerun()

else:
    st.info("Aún no hay conceptos en la cotización. Agrega al menos uno en la sección 3.")


# ══════════════════════════════════════════
# PANELES INFORMATIVOS
# ══════════════════════════════════════════
with st.expander("🔧 Diagnóstico de conexión con Google Sheets"):
    url_det = valor_secreto(*CLAVES_URL_PRECIARIO, default="")
    key_det = valor_secreto(*CLAVES_KEY_PRECIARIO, default="")
    ws_det = valor_secreto(*CLAVES_WORKSHEET_PRECIARIO, default="")
    hist_det = valor_secreto(*CLAVES_HISTORIAL_WORKSHEET, default="")

    st.write(f"**gspread disponible:** {'Sí' if GSPREAD_DISPONIBLE else 'No — instala gspread y google-auth'}")
    st.write(f"**fpdf2 disponible:** {'Sí' if FPDF_DISPONIBLE else 'No — instala fpdf2'}")
    st.write(f"**URL detectada:** {'Sí' if url_det else 'No'}")
    st.write(f"**KEY detectada:** {'Sí' if key_det else 'No'}")
    st.write(f"**Worksheet preciario:** {ws_det or 'Primera hoja (por defecto)'}")
    st.write(f"**Worksheet historial:** {hist_det or 'Historial (por defecto)'}")

    if st.button("🔄 Probar carga del Preciario", use_container_width=True):
        try:
            cargar_preciario.clear()
            df_test = cargar_preciario()
            st.success(f"Preciario cargado: {len(df_test)} registros.")
            st.dataframe(df_test.head(10), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error: {e}")

with st.expander("📐 Fórmulas utilizadas"):
    st.write("**Precio venta unitario** = Costo U. × (1 + Utilidad % / 100)")
    st.write("**Importe** = Precio venta unitario × Cantidad")
    st.write("**IVA** = Subtotal × 16%")
    st.write("**Total** = Subtotal + IVA")
