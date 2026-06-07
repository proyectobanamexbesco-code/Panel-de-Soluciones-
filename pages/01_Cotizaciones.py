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
    
    # Identificar columnas clave dinámicamente
    columna_conceptos = "CONCEPTO" if "CONCEPTO" in df_precios.columns else df_precios.columns[1]
    columna_codigo = "ITEM" if "ITEM" in df_precios.columns else df_precios.columns[0]
    
    # Extraer todas las columnas que contengan "PU" para el selector de región
    columnas_pu = [col for col in df_precios.columns if "PU " in col]
    if not columnas_pu:
        columnas_pu = ["PU"] # Respaldo por si cambian los nombres
        
    st.markdown("### 1. Datos Generales")
    col1, col2 = st.columns(2)
    
    with col1:
        cliente = st.text_input("CLIENTE:", placeholder="Ej. SMARTFIT")
        inmueble = st.text_input("INMUEBLE:", placeholder="Ej. EDIFICIO CORPORATIVO")
        region_precio = st.selectbox("Región de Precios (PU):", columnas_pu)
        
    with col2:
        reporte = st.text_input("# DE REPORTE:", placeholder="Ej. OC-0002")
        atencion = st.text_input("ATENCIÓN:", value="A QUIEN CORRESPONDA")
        titulo_cotizacion = st.text_input("TÍTULO DE COTIZACIÓN:", placeholder="Ej. REPARACIÓN DE FUGA EN TUBERÍA")

    st.markdown("### 2. Conceptos a Cotizar")
    conceptos_seleccionados = st.multiselect("Busca y selecciona los servicios:", df_precios[columna_conceptos].tolist())
    
    datos_para_pdf = []
    
    if conceptos_seleccionados:
        st.markdown("#### Define las cantidades")
        for concepto in conceptos_seleccionados:
            # Extraer los datos de la fila correspondiente
            fila = df_precios[df_precios[columna_conceptos] == concepto].iloc[0]
            codigo = fila.get(columna_codigo, "S/C")
            unidad = fila.get("UNIDAD", "PZA")
            
            # Limpiar el precio (quitar signos de pesos y comas)
            precio_str = str(fila.get(region_precio, "0")).replace('$', '').replace(',', '').strip()
            precio_unitario = float(precio_str) if precio_str else 0.0

            # Interfaz dinámica para cantidades
            c_info, c_cant = st.columns([3, 1])
            with c_info:
                st.info(f"**{codigo}** | {concepto} | PU: ${precio_unitario:,.2f}")
            with c_cant:
                cantidad = st.number_input("Cantidad", min_value=0.1, value=1.0, step=1.0, key=f"cant_{codigo}")
            
            datos_para_pdf.append({
                "codigo": codigo,
                "concepto": concepto,
                "unidad": unidad,
                "cantidad": cantidad,
                "pu": precio_unitario
            })
            
        st.markdown("---")
        if st.button("📄 Generar PDF Formato Besco", type="primary"):
            if cliente and titulo_cotizacion:
                st.success("Generando documento, por favor espera...")
                
                class PDFCotizacion(FPDF):
                    def header(self):
                        # Encabezado Izquierdo (Logo Texto Provisional)
                        self.set_font('Arial', 'B', 28)
                        self.set_text_color(30, 58, 95) # Azul Besco
                        self.cell(80, 10, "besco", 0, 0, 'L')
                        
                        # Encabezado Derecho (Datos Empresa)
                        self.set_font('Arial', '', 8)
                        self.set_text_color(0, 0, 0)
                        self.set_xy(120, 10)
                        self.multi_cell(80, 4, "Grupo Besco SA de CV\nJOSE IGNACIO BARTOLOACHE # 1910 Col. Acacias, CDMX\nTel. 01 55 55 15 08 65\nRFC. GBE101207523", 0, 'R')
                        self.ln(5)
                        
                    def footer(self):
                        self.set_y(-45)
                        self.set_font('Arial', 'I', 7)
                        terminos = (
                            "• TIEMPO DE ENTREGA DE MATERIAL DE 1 A 2 DÍAS HÁBILES.\n"
                            "• TIEMPO DE ENTREGA DEL SERVICIO DE 1 A 2 DÍAS HÁBILES.\n"
                            "• SE REQUIERE ORDEN DE COMPRA, PEDIDO, O CONTRATO.\n"
                            "• PAGO CONTRA ENTREGA DEL SERVICIO.\n"
                            "• VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
                            "• EL PRECIO QUE SE OFERTA ES POR EL TOTAL DE LOS TRABAJOS.\n"
                            "• LOS TRABAJOS SE EJECUTARÁN EN HORARIO HÁBIL, EN CASO DE QUE SE REQUIERA FUERA DEL MISMO SE TENDRÁ VARIACIÓN EN EL COSTO 35%"
                        )
                        self.multi_cell(0, 4, terminos, 0, 'L')

                # Instanciar PDF
                pdf = PDFCotizacion()
                pdf.add_page()
                
                # Bloque de Información del Cliente
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(35, 5, "CLIENTE:", 0, 0, 'R')
                pdf.set_font('Arial', '', 9)
                pdf.cell(80, 5, cliente, 0, 0, 'L')
                
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(45, 5, "FECHA DE COTIZACION:", 0, 0, 'R')
                pdf.set_font('Arial', '', 9)
                pdf.cell(30, 5, date.today().strftime('%d/%m/%Y'), 0, 1, 'L')
                
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(35, 5, "INMUEBLE:", 0, 0, 'R')
                pdf.set_font('Arial', '', 9)
                pdf.cell(80, 5, inmueble, 0, 0, 'L')
                
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(45, 5, "FECHA VIGENCIA:", 0, 0, 'R')
                pdf.set_font('Arial', '', 9)
                pdf.cell(30, 5, "15 DIAS HABILES", 0, 1, 'L')
                
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(35, 5, "# DE REPORTE:", 0, 0, 'R')
                pdf.set_font('Arial', '', 9)
                pdf.cell(80, 5, reporte, 0, 1, 'L')
                
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(35, 5, "ATENCION:", 0, 0, 'R')
                pdf.set_font('Arial', '', 9)
                pdf.cell(80, 5, atencion, 0, 1, 'L')
                pdf.ln(8)
                
                # Introducción y Título
                pdf.set_font('Arial', '', 9)
                pdf.cell(0, 5, "Por medio de la presente y a nombre de Grupo Besco SA de CV, presento la siguiente cotizacion:", 0, 1, 'L')
                pdf.ln(2)
                
                pdf.set_font('Arial', 'BI', 11)
                pdf.cell(0, 5, titulo_cotizacion.upper(), 0, 1, 'C')
                pdf.ln(4)
                
                # Dibujar Encabezado de la Tabla
                pdf.set_fill_color(153, 194, 255) # Azul claro institucional
                pdf.set_font('Arial', 'B', 8)
                pdf.cell(35, 8, "CODIGO", 1, 0, 'C', fill=True)
                pdf.cell(75, 8, "CONCEPTO", 1, 0, 'C', fill=True)
                pdf.cell(15, 8, "UNIDAD", 1, 0, 'C', fill=True)
                pdf.cell(20, 8, "CANTIDAD", 1, 0, 'C', fill=True)
                pdf.cell(20, 8, "PU", 1, 0, 'C', fill=True)
                pdf.cell(25, 8, "IMPORTE", 1, 1, 'C', fill=True)
                
                pdf.set_font('Arial', '', 8)
                subtotal = 0.0
                
                # Dibujar Filas Dinámicas
                for d in datos_para_pdf:
                    if pdf.get_y() > 240:
                        pdf.add_page()
                    
                    importe = d['cantidad'] * d['pu']
                    subtotal += importe
                    
                    x_start = pdf.get_x()
                    y_start = pdf.get_y()
                    
                    # Usamos multi_cell para el concepto por si es muy largo
                    pdf.set_xy(x_start + 35, y_start)
                    pdf.multi_cell(75, 5, d['concepto'], 0, 'L')
                    max_y = pdf.get_y()
                    h = max_y - y_start if max_y - y_start > 8 else 8
                    
                    # Dibujar los bordes y el resto de los datos usando la altura calculada
                    pdf.set_xy(x_start, y_start)
                    pdf.cell(35, h, str(d['codigo']), 1, 0, 'C')
                    pdf.set_xy(x_start + 35, y_start)
                    pdf.cell(75, h, "", 1, 0) # Borde del concepto
                    pdf.set_xy(x_start + 110, y_start)
                    pdf.cell(15, h, str(d['unidad']), 1, 0, 'C')
                    pdf.cell(20, h, f"{d['cantidad']:.2f}", 1, 0, 'C')
                    pdf.cell(20, h, f"$ {d['pu']:,.2f}", 1, 0, 'R')
                    pdf.cell(25, h, f"$ {importe:,.2f}", 1, 1, 'R')
                    
                    pdf.set_y(y_start + h)
                
                # Dibujar Totales
                iva = subtotal * 0.16
                total_presupuestado = subtotal + iva
                
                pdf.set_font('Arial', 'B', 9)
                pdf.cell(145, 6, "SUBTOTAL", 0, 0, 'R')
                pdf.cell(15, 6, "$", 0, 0, 'R')
                pdf.cell(30, 6, f"{subtotal:,.2f}", 0, 1, 'R')
                
                pdf.cell(145, 6, "IVA 16%", 0, 0, 'R')
                pdf.cell(15, 6, "$", 0, 0, 'R')
                pdf.cell(30, 6, f"{iva:,.2f}", 0, 1, 'R')
                
                pdf.cell(145, 6, "TOTAL PRESUPUESTADO", 0, 0, 'R')
                pdf.cell(15, 6, "$", 0, 0, 'R')
                pdf.cell(30, 6, f"{total_presupuestado:,.2f}", 0, 1, 'R')
                
                # Descarga
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(
                    label="📥 Descargar Documento PDF",
                    data=pdf_bytes,
                    file_name=f"Cotizacion_{cliente.replace(' ', '_')}_{reporte}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("⚠️ El Cliente y el Título de Cotización son obligatorios.")
else:
    st.info("Cargando base de datos o el preciario está vacío.")
