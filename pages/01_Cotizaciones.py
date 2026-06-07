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
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df_precios = cargar_preciario()

# INICIO DEL FORMULARIO PRINCIPAL
with st.form("cotizador_form"):
    # SECCIÓN 1: Cliente y Proyecto
    st.markdown("### 1. Datos de Identificación del Cliente")
    col1, col2 = st.columns(2)
    with col1:
        cliente = st.text_input("CLIENTE:", placeholder="Ej. SMARTFIT")
        inmueble = st.text_input("INMUEBLE:", placeholder="Ej. EDIFICIO CORPORATIVO")
    with col2:
        reporte = st.text_input("# DE TICKET / REPORTE CLIENTE:", placeholder="Ej. OC-0002")
        atencion = st.text_input("ATENCIÓN:", value="A QUIEN CORRESPONDA")
        titulo_cotizacion = st.text_input("TIPO DE TRABAJO / TÍTULO:", placeholder="Ej. REPARACIÓN DE FUGA")

    # SECCIÓN 2: Cotizador
    st.markdown("### 2. Datos del Cotizador")
    col3, col4 = st.columns(2)
    with col3:
        cotizador_nombre = st.text_input("ELABORÓ / COTIZÓ (Tu nombre):", placeholder="Ej. GERARDO MENDEZ")
        cotizador_puesto = st.selectbox("PUESTO:", ["Gerente Regional", "Gerente de Servicio", "Supervisor", "Jefe de Oficina", "Cotizador"])
    with col4:
        fecha_cotizacion = st.date_input("FECHA DE COTIZACIÓN:", date.today())
        fecha_solicitud = st.date_input("FECHA SOLICITUD DE COTIZACIÓN:", date.today())

    # SECCIÓN 3: Conceptos a Cotizar
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
        
        # Filtro de búsqueda inteligente
        filtro = df_precios.copy()
        if busqueda:
            filtro = df_precios[
                df_precios[col_i].astype(str).str.contains(busqueda, case=False) |
                df_precios[col_c].astype(str).str.contains(busqueda, case=False) |
                df_precios[col_u].astype(str).str.contains(busqueda, case=False)
            ]
        
        seleccionados = st.multiselect("Selecciona servicios:", filtro[col_c].tolist())
        
        for concepto in seleccionados:
            fila = df_precios[df_precios[col_c] == concepto].iloc[0]
            
            c1, c2, c3, c4 = st.columns([1, 4, 1, 1])
            with c1: st.code(fila.get(col_i, "S/C"))
            with c2: st.info(concepto)
            with c3: st.text(fila.get(col_u, "PZA"))
            with c4: cant = st.number_input(f"Cant_{fila.get(col_i)}", min_value=0.1, value=1.0, label_visibility="collapsed")
            
            pu = float(str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip() or 0)
            datos_para_pdf.append({"codigo": fila.get(col_i), "concepto": concepto, "unidad": fila.get(col_u), "cantidad": cant, "pu": pu})
    
    # EL BOTÓN DE ENVÍO DEBE ESTAR DENTRO DEL WITH FORM (Última línea)
    submit = st.form_submit_button("📄 Generar PDF Formato Besco", type="primary")

    if submit:
        if cliente and titulo_cotizacion and cotizador_nombre:
            st.success("¡Formulario validado! Generando PDF...")
            # Aquí va toda tu lógica de generación de PDF con FPDF...
        else:
            st.warning("⚠️ Asegúrate de completar los campos obligatorios.")
