import streamlit as st
import pandas as pd
import sys
import os
from fpdf import FPDF
from datetime import date

# Asegura que la app encuentre tu archivo utils.py
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
        st.error(f"Error de conexión con Google Sheets: {e}")
        return pd.DataFrame()

df_precios = cargar_preciario()

if not df_precios.empty:
    columna_conceptos = "CONCEPTO" if "CONCEPTO" in df_precios.columns else df_precios.columns[1]
    columna_codigo = "ITEM" if "ITEM" in df_precios.columns else df_precios.columns[0]
    
    columnas_pu = [col for col in df_precios.columns if "PU " in col]
    if not columnas_pu:
        columnas_pu = ["PU"]
        
    # INICIO DEL FORMULARIO PRINCIPAL
    with st.form("cotizador_form"):
        # SECCIÓN 1
        st.markdown("### 1. Datos de Identificación del Cliente")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("CLIENTE:", placeholder="Ej. SMARTFIT")
            inmueble = st.text_input("INMUEBLE:", placeholder="Ej. EDIFICIO CORPORATIVO")
        with col2:
            reporte = st.text_input("# DE TICKET / REPORTE CLIENTE (Opcional):", placeholder="Ej. OC-0002")
            atencion = st.text_input("ATENCIÓN:", value="A QUIEN CORRESPONDA")
            titulo_cotizacion = st.text_input("TIPO DE TRABAJO / TÍTULO:", placeholder="Ej. REPARACIÓN DE FUGA")

        st.markdown("### 2. Datos del Cotizador")
        col3, col4 = st.columns(2)
        with col3:
            cotizador_nombre = st.text_input("ELABORÓ / COTIZÓ (Tu nombre):", value="", placeholder="Ej. GERARDO MENDEZ")
        with col4:
            cotizador_puesto = st.selectbox("PUESTO:", ["Gerente Regional", "Gerente de Servicio", "Supervisor", "Jefe de Oficina", "Cotizador"])

        st.markdown("### 3. Conceptos a Cotizar")
        region_precio = st.selectbox("Región de Precios (PU):", columnas_pu)
        conceptos_seleccionados = st.multiselect("Busca y selecciona los servicios:", df_precios[columna_conceptos].tolist())
        
        datos_para_pdf = []
        
        # Lógica de cantidades (fuera de form_submit_button pero dentro del form)
        if conceptos_seleccionados:
            st.markdown("#### Define las cantidades")
            for concepto in conceptos_seleccionados:
                fila = df_precios[df_precios[columna_conceptos] == concepto].iloc[0]
                codigo = fila.get(columna_codigo, "S/C")
                unidad = fila.get("UNIDAD", "PZA")
                precio_str = str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip()
                precio_unitario = float(precio_str) if precio_str else 0.0

                c_info, c_cant = st.columns([3, 1])
                with c_info:
                    st.info(f"**{codigo}** | {concepto} | PU: ${precio_unitario:,.2f}")
                with c_cant:
                    cantidad = st.number_input("Cantidad", min_value=0.1, value=1.0, step=1.0, key=f"cant_{codigo}")
                
                datos_para_pdf.append({"codigo": codigo, "concepto": concepto, "unidad": unidad, "cantidad": cantidad, "pu": precio_unitario})
        
        # EL BOTÓN DE ENVÍO DEBE ESTAR DENTRO DEL WITH FORM
        submit = st.form_submit_button("📄 Generar PDF Formato Besco", type="primary")

        if submit:
            if cliente and titulo_cotizacion and cotizador_nombre:
                # FOLIO
                iniciales = "".join([p[0] for p in cotizador_nombre.strip().split() if p]).upper()
                fecha_str = date.today().strftime('%d%m%y')
                cliente_corto = "".join(cliente.split())[:8].upper()
                tipo_corto = "".join(titulo_cotizacion.split())[:8].upper()
                folio_generado = f"{iniciales}-{fecha_str}-{cliente_corto}-{tipo_corto}"
                
                st.success(f"Folio asignado: {folio_generado}")
                
                # PDF LOGIC... (Tu lógica de PDF aquí permanece igual)
                # [Aqui va el mismo código de generación del PDF que tenías anteriormente]
                # ...
            else:
                st.warning("⚠️ El Cliente, el Título de Cotización y tu Nombre son obligatorios.")
