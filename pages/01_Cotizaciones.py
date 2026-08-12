import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from fpdf import FPDF
from datetime import datetime
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Cotizaciones y APU", layout="wide")

st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE LIMPIEZA DE CARACTERES ESPECIALES ---
def limpiar_texto(texto):
    if not isinstance(texto, str): 
        texto = str(texto)
    reemplazos = {
        '•': '-', '“': '"', '”': '"', '‘': "'", '’': "'", 
        '–': '-', '—': '-', '\u200b': '', '\r': '', '°': ' grados'
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.encode('latin-1', 'replace').decode('latin-1')

# --- CONEXIÓN A GOOGLE SHEETS ---
@st.cache_data(ttl=600)
def cargar_preciario():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(credentials)
        sheet_url = st.secrets["PRECIARIO_BESCO_URL"]
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.get_worksheet(0)
        df = pd.DataFrame(worksheet.get_all_records())
        return df, None
    except Exception as e:
        return None, str(e)

# --- CLASE PDF PARA APU Y COTIZACIÓN ---
class BESCO_APU_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo besco 2026.jpeg")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 45)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(100, 15)
        self.cell(0, 10, limpiar_texto('ANÁLISIS DE PRECIO UNITARIO (APU)'), 0, 1, 'R')
        self.set_font('Arial', '', 9)
        self.set_x(100)
        self.cell(0, 5, limpiar_texto(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}"), 0, 1, 'R')
        self.ln(15)

    def add_custom_section(self, title):
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, limpiar_texto(title.upper()), 0, 1, 'L', fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

# --- INTERFAZ PRINCIPAL ---
st.title("💰 Módulo de Cotizaciones y Análisis de Precios Unitarios")

# Cargar Preciario si la conexión PEM/GCP está activa
df_preciario, error_conexion = cargar_preciario()

# Conmutador de Modo
modo_calculo = st.radio("Selecciona el tipo de análisis:", ["Cotización Directa", "Análisis de Precio Unitario (APU)"], horizontal=True)

st.markdown("---")

st.subheader("1. Identificación del Concepto")
c1, c2, c3 = st.columns([2, 1, 1])
concepto_nombre = c1.text_input("Nombre / Clave del Concepto", "Mantenimiento Preventivo A/A 3TR")
unidad_medida = c2.selectbox("Unidad de Medida", ["PZA", "SERV", "M2", "ML", "KG", "LOTE"])
cantidad_obra = c3.number_input("Cantidad de Obra / Trabajo", min_value=1.0, value=1.0, step=1.0)

descripcion_concepto = st.text_area("Descripción Técnica Detallada del Concepto", "Suministro, aplicación y pruebas para...")

if modo_calculo == "Cotización Directa":
    st.subheader("2. Captura Directa de Precio")
    if error_conexion:
        st.warning(f"⚠️ Preciario no disponible ({error_conexion}). Modo manual activado.")
        pu_directo = st.number_input("Precio Unitario Directo ($)", min_value=0.0, value=0.0, step=50.0)
    else:
        st.success("✅ Preciario BESCO Conectado.")
        opciones = df_preciario['Descripción'].tolist() if 'Descripción' in df_preciario.columns else []
        concepto_sel = st.selectbox("Seleccionar del Preciario", opciones)
        pu_directo = st.number_input("Precio Unitario ($)", min_value=0.0, value=0.0)

    total_directo = pu_directo * cantidad_obra
    st.metric("Importe Total Cotizado", f"${total_directo:,.2f} MXN")

else:
    # -------------------------------------------------------------
    # MÓDULO DE ANÁLISIS DE PRECIO UNITARIO (APU)
    # -------------------------------------------------------------
    st.subheader("2. Matriz de Insumos (Parámetros Base de APU)")

    # A. MATERIALES
    with st.expander("📦 A. Materiales e Insumos Físicos", expanded=True):
        st.caption("Captura los materiales requeridos por cada unidad de medida del concepto.")
        df_mat = st.data_editor(
            pd.DataFrame(columns=["Descripción Material", "Unidad", "Cantidad/Rendimiento", "Costo Unitario ($)"]),
            num_rows="dynamic", key="tabla_mat"
        )
        
        # Cálculo Materiales
        costo_mat = 0.0
        if not df_mat.empty:
            df_mat["Importe ($)"] = pd.to_numeric(df_mat["Cantidad/Rendimiento"], errors='coerce').fillna(0) * pd.to_numeric(df_mat["Costo Unitario ($)"], errors='coerce').fillna(0)
            costo_mat = df_mat["Importe ($)"].sum()
        st.write(f"**Subtotal Materiales:** `${costo_mat:,.2f}`")

    # B. MANO DE OBRA
    with st.expander("👷 B. Mano de Obra (Cuadrillas)", expanded=True):
        st.caption("Especifica la cuadrilla y el rendimiento (Jornadas requeridas por unidad de medida).")
        df_mo = st.data_editor(
            pd.DataFrame(columns=["Categoría / Personal", "Jornada/Turno ($)", "Rendimiento (Jornada x Unidad)"]),
            num_rows="dynamic", key="tabla_mo"
        )
        
        # Cálculo Mano de Obra
        costo_mo = 0.0
        if not df_mo.empty:
            df_mo["Importe ($)"] = pd.to_numeric(df_mo["Jornada/Turno ($)"], errors='coerce').fillna(0) * pd.to_numeric(df_mo["Rendimiento (Jornada x Unidad)"], errors='coerce').fillna(0)
            costo_mo = df_mo["Importe ($)"].sum()
        st.write(f"**Subtotal Mano de Obra:** `${costo_mo:,.2f}`")

    # C. EQUIPO Y HERRAMIENTA
    with st.expander("🛠️ C. Equipo y Herramienta Menor", expanded=True):
        col_h1, col_h2 = st.columns(2)
        pct_herramienta = col_h1.number_input("% Herramienta Menor sobre Mano de Obra", min_value=0.0, max_value=20.0, value=5.0) / 100.0
        costo_herramienta = costo_mo * pct_herramienta
        col_h1.caption(f"Costo Herramienta Menor: ${costo_herramienta:,.2f}")

        st.caption("Equipo especializado / Maquinaria extra:")
        df_eq = st.data_editor(
            pd.DataFrame(columns=["Equipo/Maquinaria", "Costo Hora/Día ($)", "Tiempo de Uso (Horas/Días)"]),
            num_rows="dynamic", key="tabla_eq"
        )
        
        costo_eq_extra = 0.0
        if not df_eq.empty:
            df_eq["Importe ($)"] = pd.to_numeric(df_eq["Costo Hora/Día ($)"], errors='coerce').fillna(0) * pd.to_numeric(df_eq["Tiempo de Uso (Horas/Días)"], errors='coerce').fillna(0)
            costo_eq_extra = df_eq["Importe ($)"].sum()
        
        costo_equipo_total = costo_herramienta + costo_eq_extra
        st.write(f"**Subtotal Equipo y Herramienta:** `${costo_equipo_total:,.2f}`")

    # D. INDIRECTOS, FINANCIAMIENTO Y UTILIDAD
    st.subheader("3. Costos Indirectos y Margen de Utilidad")
    cd1, cd2, cd3 = st.columns(3)
    
    costo_directo_total = costo_mat + costo_mo + costo_equipo_total
    
    pct_indirectos = cd1.number_input("% Costos Indirectos (Oficina / Campo)", min_value=0.0, max_value=100.0, value=12.0) / 100.0
    monto_indirectos = costo_directo_total * pct_indirectos
    
    costo_subtotal = costo_directo_total + monto_indirectos
    
    pct_utilidad = cd2.number_input("% Utilidad Deseada", min_value=0.0, max_value=100.0, value=15.0) / 100.0
    monto_utilidad = costo_subtotal * pct_utilidad

    # PRECIO UNITARIO FINAL
    precio_unitario_apu = costo_subtotal + monto_utilidad
    importe_total_apu = precio_unitario_apu * cantidad_obra

    # RESUMEN FINANCIERO INTEGRAL
    st.markdown("---")
    st.subheader("📊 Resumen de la Matriz APU")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Costo Directo Unitario", f"${costo_directo_total:,.2f}")
    m2.metric("Indirectos", f"${monto_indirectos:,.2f}")
    m3.metric("Utilidad", f"${monto_utilidad:,.2f}")
    m4.metric("Precio Unitario Final", f"${precio_unitario_apu:,.2f}")

    st.metric("💰 Importe Total de la Propuesta", f"${importe_total_apu:,.2f} MXN")

# --- GENERACIÓN DE PDF COMPLETO ---
if st.button("🚀 Exportar Tarjeta de APU / Cotización a PDF", type="primary", use_container_width=True):
    pdf = BESCO_APU_PDF()
    pdf.add_page()
    
    # Encabezado
    pdf.add_custom_section("1. Datos Generales del Concepto")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, limpiar_texto(f"Concepto: {concepto_nombre}"), 0, 1)
    pdf.cell(0, 6, limpiar_texto(f"Unidad: {unidad_medida} | Cantidad a Ejecutar: {cantidad_obra}"), 0, 1)
    pdf.multi_cell(0, 5, limpiar_texto(f"Descripción: {descripcion_concepto}"), 1)
    pdf.ln(4)

    if modo_calculo == "Análisis de Precio Unitario (APU)":
        # Tabla Desglose APU
        pdf.add_custom_section("2. Desglose de Costo Directo e Insumos")
        pdf.set_font("Arial", "B", 9)
        pdf.cell(100, 6, "Rubro", 1, 0)
        pdf.cell(90, 6, "Subtotal por Unidad ($)", 1, 1, 'R')
        
        pdf.set_font("Arial", "", 9)
        pdf.cell(100, 6, "A. Materiales e Insumos", 1, 0)
        pdf.cell(90, 6, f"${costo_mat:,.2f}", 1, 1, 'R')
        
        pdf.cell(100, 6, "B. Mano de Obra", 1, 0)
        pdf.cell(90, 6, f"${costo_mo:,.2f}", 1, 1, 'R')
        
        pdf.cell(100, 6, "C. Equipo y Herramienta", 1, 0)
        pdf.cell(90, 6, f"${costo_equipo_total:,.2f}", 1, 1, 'R')
        
        pdf.set_font("Arial", "B", 9)
        pdf.cell(100, 6, "TOTAL COSTO DIRECTO", 1, 0)
        pdf.cell(90, 6, f"${costo_directo_total:,.2f}", 1, 1, 'R')
        pdf.ln(4)

        pdf.add_custom_section("3. Indirectos, Utilidad y Precio Unitario Final")
        pdf.set_font("Arial", "", 9)
        pdf.cell(100, 6, f"Indirectos ({pct_indirectos*100:.1f}%)", 1, 0)
        pdf.cell(90, 6, f"${monto_indirectos:,.2f}", 1, 1, 'R')
        
        pdf.cell(100, 6, f"Utilidad ({pct_utilidad*100:.1f}%)", 1, 0)
        pdf.cell(90, 6, f"${monto_utilidad:,.2f}", 1, 1, 'R')
        
        pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 7, "PRECIO UNITARIO FINAL (P.U.)", 1, 0)
        pdf.cell(90, 7, f"${precio_unitario_apu:,.2f}", 1, 1, 'R')
        
        pdf.cell(100, 7, f"TOTAL IMPORTE TRABAJOS ({cantidad_obra} {unidad_medida})", 1, 0)
        pdf.cell(90, 7, f"${importe_total_apu:,.2f}", 1, 1, 'R')
    else:
        pdf.add_custom_section("2. Resumen de Cotización Directa")
        pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 7, "Precio Unitario", 1, 0)
        pdf.cell(90, 7, f"${pu_directo:,.2f}", 1, 1, 'R')
        pdf.cell(100, 7, "Importe Total", 1, 0)
        pdf.cell(90, 7, f"${total_directo:,.2f}", 1, 1, 'R')

    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
    st.download_button("📥 Descargar Tarjeta de APU / Cotización (PDF)", data=pdf_bytes, file_name=f"APU_{concepto_nombre.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
