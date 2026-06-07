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
        return pd.DataFrame()

df_precios = cargar_preciario()

with st.form("cotizador_form"):
    # SECCIÓN 1 Y 2
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
        cotizador_nombre = st.text_input("ELABORÓ / COTIZÓ:")
        cotizador_puesto = st.selectbox("PUESTO:", ["Gerente Regional", "Gerente de Servicio", "Supervisor", "Jefe de Oficina", "Cotizador"])
    with col4:
        fecha_cotizacion = st.date_input("FECHA DE COTIZACIÓN:", date.today())
        fecha_solicitud = st.date_input("FECHA SOLICITUD DE COTIZACIÓN:", date.today())

    # SECCIÓN 3: PRECIARIO CON TOGGLE
    st.markdown("### 3. Conceptos a Cotizar")
    habilitar_preciario = st.toggle("Habilitar búsqueda en Preciario Besco", value=True)
    
    datos_para_pdf = []
    
    if habilitar_preciario and not df_precios.empty:
        col_c = "CONCEPTO" if "CONCEPTO" in df_precios.columns else df_precios.columns[1]
        col_i = "ITEM" if "ITEM" in df_precios.columns else df_precios.columns[0]
        col_u = "UNIDAD" if "UNIDAD" in df_precios.columns else df_precios.columns[2]
        columnas_pu = [col for col in df_precios.columns if "PU " in col] or ["PU"]
        
        region_precio = st.selectbox("Región de Precios (PU):", columnas_pu)
        busqueda = st.text_input("🔍 Buscar por ITEM, CONCEPTO o UNIDAD:")
        
        filtro = df_precios.copy()
        if busqueda:
            filtro = df_precios[
                df_precios[col_i].astype(str).str.contains(busqueda, case=False) |
                df_precios[col_c].astype(str).str.contains(busqueda, case=False) |
                df_precios[col_u].astype(str).str.contains(busqueda, case=False)
            ]
        
        seleccionados = st.multiselect("Selecciona los servicios filtrados:", filtro[col_c].tolist())
        
        for concepto in seleccionados:
            fila = df_precios[df_precios[col_c] == concepto].iloc[0]
            c1, c2, c3, c4 = st.columns([1, 4, 1, 1])
            with c1: st.code(fila.get(col_i))
            with c2: st.info(concepto)
            with c3: st.text(fila.get(col_u))
            with c4: cant = st.number_input(f"C_{fila.get(col_i)}", 0.1, 100.0, 1.0, label_visibility="collapsed")
            
            pu = float(str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip() or 0)
            datos_para_pdf.append({"codigo": fila.get(col_i), "concepto": concepto, "unidad": fila.get(col_u), "cantidad": cant, "pu": pu})
            
    else:
        st.warning("Preciario deshabilitado. Agrega conceptos manualmente:")
        num_items = st.number_input("¿Cuántos conceptos manuales agregarás?", 1, 10, 1)
        for i in range(num_items):
            c1, c2, c3, c4 = st.columns([1, 4, 1, 1])
            cod = c1.text_input("Item", key=f"m_cod_{i}")
            con = c2.text_input("Concepto", key=f"m_con_{i}")
            uni = c3.text_input("Unidad", key=f"m_uni_{i}")
            can = c4.number_input("Cant", 0.1, 100.0, 1.0, key=f"m_can_{i}")
            if cod or con:
                datos_para_pdf.append({"codigo": cod, "concepto": con, "unidad": uni, "cantidad": can, "pu": 0.0})

    submit = st.form_submit_button("📄 Generar PDF Formato Besco", type="primary")
    # ... (Resto de tu lógica PDF)
