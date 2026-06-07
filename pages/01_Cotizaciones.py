import streamlit as st
import pandas as pd
import sys
import os
from fpdf import FPDF
from datetime import date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client

st.set_page_config(page_title="Cotizaciones | Besco", page_icon="📄", layout="wide")

st.title("📄 Generador de Cotizaciones")
st.markdown("---")

@st.cache_data(ttl=600)
def cargar_preciario():
    try:
        client = obtener_gspread_client()
        sheet = client.open("Preciario Besco").sheet1
        df = pd.DataFrame(sheet.get_all_records())
        df.columns = [str(c).strip().upper() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df_precios = cargar_preciario()

if not df_precios.empty:
    columna_conceptos = "CONCEPTO" if "CONCEPTO" in df_precios.columns else df_precios.columns[1]
    columna_codigo = "ITEM" if "ITEM" in df_precios.columns else df_precios.columns[0]
    columnas_pu = [col for col in df_precios.columns if "PU " in col] or ["PU"]
        
    with st.form("cotizador_form"):
        st.markdown("### 1. Datos de Identificación del Cliente")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("CLIENTE:", placeholder="Ej. SMARTFIT")
            inmueble = st.text_input("INMUEBLE:", placeholder="Ej. EDIFICIO CORPORATIVO")
        with col2:
            reporte = st.text_input("# DE TICKET / REPORTE CLIENTE:", placeholder="Ej. OC-0002")
            atencion = st.text_input("ATENCIÓN:", value="A QUIEN CORRESPONDA")
            titulo_cotizacion = st.text_input("TIPO DE TRABAJO / TÍTULO:", placeholder="Ej. REPARACIÓN DE FUGA")

        st.markdown("### 2. Datos del Cotizador")
        col3, col4 = st.columns(2)
        with col3:
            cotizador_nombre = st.text_input("ELABORÓ / COTIZÓ:", value="")
            cotizador_puesto = st.selectbox("PUESTO:", ["Gerente Regional", "Gerente de Servicio", "Supervisor", "Jefe de Oficina", "Cotizador"])
        with col4:
            fecha_cotizacion = st.date_input("FECHA DE COTIZACIÓN:", date.today())
            fecha_solicitud = st.date_input("FECHA SOLICITUD DE COTIZACIÓN:", date.today())

        st.markdown("### 3. Conceptos a Cotizar")
        region_precio = st.selectbox("Región de Precios (PU):", columnas_pu)
        conceptos_seleccionados = st.multiselect("Busca y selecciona los servicios:", df_precios[columna_conceptos].tolist())
        
        datos_para_pdf = []
        if conceptos_seleccionados:
            for concepto in conceptos_seleccionados:
                fila = df_precios[df_precios[columna_conceptos] == concepto].iloc[0]
                codigo = fila.get(columna_codigo, "S/C")
                unidad = fila.get("UNIDAD", "PZA")
                precio_str = str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip()
                pu = float(precio_str) if precio_str else 0.0
                cant = st.number_input(f"Cantidad: {concepto[:30]}...", min_value=0.1, value=1.0, key=f"cant_{codigo}")
                datos_para_pdf.append({"codigo": codigo, "concepto": concepto, "unidad": unidad, "cantidad": cant, "pu": pu})
        
        submit = st.form_submit_button("📄 Generar PDF Formato Besco", type="primary")

        if submit and cliente and titulo_cotizacion and cotizador_nombre:
            folio = f"{''.join([p[0] for p in cotizador_nombre.split()]).upper()}-{date.today().strftime('%d%m%y')}-{cliente[:8].upper()}"
            
            class PDF(FPDF):
                def header(self):
                    # Inserción del logo
                    if os.path.exists("logo besco 2026.jpeg"):
                        self.image("logo besco 2026.jpeg", 10, 8, 30)
                    self.set_font('Arial', 'B', 12)
                    self.cell(0, 10, "GRUPO BESCO SA DE CV", 0, 1, 'R')
                    self.ln(10)

            pdf = PDF()
            pdf.add_page()
            # Datos al PDF
            pdf.set_font('Arial', '', 9)
            pdf.cell(0, 5, f"Fecha Cotizacion: {fecha_cotizacion.strftime('%d/%m/%Y')}", ln=True)
            pdf.cell(0, 5, f"Fecha Solicitud: {fecha_solicitud.strftime('%d/%m/%Y')}", ln=True)
            # ... (continúa con tu lógica de tabla y footer)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Descargar PDF", pdf_bytes, f"{folio}.pdf", "application/pdf")
