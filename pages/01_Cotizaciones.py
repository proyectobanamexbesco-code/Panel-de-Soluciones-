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
    col_c = "CONCEPTO" if "CONCEPTO" in df_precios.columns else df_precios.columns[1]
    col_i = "ITEM" if "ITEM" in df_precios.columns else df_precios.columns[0]
    col_u = "UNIDAD" if "UNIDAD" in df_precios.columns else df_precios.columns[2]
    columnas_pu = [col for col in df_precios.columns if "PU " in col] or ["PU"]
        
    with st.form("cotizador_form"):
        # SECCIONES 1 y 2 (Datos de Cliente y Cotizador)
        st.markdown("### 1. Datos de Identificación del Cliente")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("CLIENTE:")
            inmueble = st.text_input("INMUEBLE:")
        with col2:
            reporte = st.text_input("# DE TICKET:")
            titulo_cotizacion = st.text_input("TIPO DE TRABAJO:")

        st.markdown("### 2. Datos del Cotizador")
        col3, col4 = st.columns(2)
        with col3:
            cotizador_nombre = st.text_input("ELABORÓ:")
        with col4:
            cotizador_puesto = st.selectbox("PUESTO:", ["Gerente Regional", "Gerente de Servicio", "Supervisor", "Jefe de Oficina", "Cotizador"])

        # SECCIÓN 3: Búsqueda Avanzada en 3 campos
        st.markdown("### 3. Conceptos a Cotizar")
        region_precio = st.selectbox("Región de Precios (PU):", columnas_pu)
        
        # Buscador inteligente
        busqueda = st.text_input("🔍 Buscar por ITEM, CONCEPTO o UNIDAD:")
        
        filtro = df_precios.copy()
        if busqueda:
            filtro = df_precios[
                df_precios[col_i].astype(str).str.contains(busqueda, case=False) |
                df_precios[col_c].astype(str).str.contains(busqueda, case=False) |
                df_precios[col_u].astype(str).str.contains(busqueda, case=False)
            ]

        # Selector de conceptos filtrados
        opciones = filtro[col_c].tolist()
        seleccionados = st.multiselect("Selecciona los servicios filtrados:", opciones)
        
        datos_para_pdf = []
        if seleccionados:
            st.markdown("---")
            for concepto in seleccionados:
                fila = df_precios[df_precios[col_c] == concepto].iloc[0]
                
                c1, c2, c3, c4 = st.columns([1, 4, 1, 1])
                with c1:
                    st.text("ITEM")
                    st.code(fila.get(col_i))
                with c2:
                    st.text("CONCEPTO")
                    st.info(concepto)
                with c3:
                    st.text("UNIDAD")
                    st.text(fila.get(col_u))
                with c4:
                    st.text("CANTIDAD")
                    cantidad = st.number_input(f"C_{fila.get(col_i)}", min_value=0.1, value=1.0, label_visibility="collapsed")

                pu = float(str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip() or 0)
                datos_para_pdf.append({"codigo": fila.get(col_i), "concepto": concepto, "unidad": fila.get(col_u), "cantidad": cantidad, "pu": pu})
        
        submit = st.form_submit_button("📄 Generar PDF Formato Besco", type="primary")

        if submit and cliente and titulo_cotizacion:
            st.success("PDF generado exitosamente.")
            # ... (Lógica de PDF)
