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
    # (Tus secciones 1 y 2 permanecen igual...)
    st.markdown("### 3. Conceptos a Cotizar")
    habilitar_preciario = st.toggle("Habilitar Preciario Besco", value=True)
    datos_para_pdf = []
    
    if habilitar_preciario and not df_precios.empty:
        region_precio = st.selectbox("Región de Precios (PU):", [c for c in df_precios.columns if "PU " in c] or ["PU"])
        busqueda = st.text_input("🔍 Buscar conceptos:")
        
        # Filtro de búsqueda (Item, Concepto, Unidad)
        filtro = df_precios[df_precios.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
        seleccionados = st.multiselect("Selecciona servicios:", filtro["CONCEPTO"].tolist())
        
        for concepto in seleccionados:
            fila = df_precios[df_precios["CONCEPTO"] == concepto].iloc[0]
            pu_base = float(str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip() or 0)
            
            st.markdown(f"**{concepto}**")
            c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 1, 1, 1, 1])
            
            with c1: st.text("ITEM"); st.code(fila.get("ITEM", "S/C"))
            with c2: st.text("DESCRIPCIÓN"); st.info(concepto)
            with c3: st.text("UNIDAD"); st.text(fila.get("UNIDAD", "PZA"))
            with c4: 
                pu = st.number_input(f"PU_{concepto[:5]}", value=pu_base, format="%.2f")
            with c5: 
                utilidad = st.number_input(f"Utilidad %_{concepto[:5]}", value=23.55, step=0.5, format="%.2f")
            with c6:
                precio_venta = pu * (1 + (utilidad / 100))
                st.text("PRECIO VENTA")
                st.success(f"${precio_venta:,.2f}")
            
            cant = st.number_input(f"Cantidad {concepto[:5]}", 0.1, 100.0, 1.0)
            datos_para_pdf.append({"codigo": fila.get("ITEM"), "concepto": concepto, "unidad": fila.get("UNIDAD"), "cantidad": cant, "pu": precio_venta})
    
    # ... (Resto de tu lógica para generar el PDF)
