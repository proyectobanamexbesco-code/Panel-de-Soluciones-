import os
from datetime import date
import pandas as pd
import streamlit as st
from fpdf import FPDF

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    gspread = None
    Credentials = None


# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizaciones | Besco",
    page_icon="💰",
    layout="wide"
)

# ==========================================
# FUNCIONES AUXILIARES Y CÁLCULOS
# ==========================================
def inicializar_session_state():
    if "conceptos_cotizacion" not in st.session_state:
        st.session_state.conceptos_cotizacion = []
    if "usar_preciario_besco" not in st.session_state:
        st.session_state.usar_preciario_besco = True
    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = {
            "folio": "", "fecha": date.today(), "cliente_nombre": "",
            "cliente_empresa": "", "cliente_contacto": "", "cliente_telefono": "",
            "cliente_correo": "", "cotiza_nombre": "", "cotiza_puesto": "",
            "cotiza_telefono": "", "cotiza_correo": ""
        }

def limpiar_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.datos_cotizacion = {k: ("" if isinstance(v, str) else date.today()) for k, v in st.session_state.datos_cotizacion.items()}

def calcular_precio_venta(precio_unitario: float, utilidad_porcentaje: float) -> float:
    return round(float(precio_unitario) * (1 + (float(utilidad_porcentaje) / 100)), 2)

def calcular_utilidad_monto(precio_unitario: float, utilidad_porcentaje: float) -> float:
    return round(float(precio_unitario) * (float(utilidad_porcentaje) / 100), 2)

def formatear_moneda(valor: float) -> str:
    return f"${float(valor):,.2f}"

def limpiar_texto_pdf(texto):
    """Limpia caracteres especiales que rompen FPDF (latin-1)"""
    if not texto:
        return ""
    texto = str(texto)
    # Reemplazar caracteres conflictivos comunes
    reemplazos = {
        '•': '-', '“': '"', '”': '"', '‘': "'", '’': "'", 
        '–': '-', '—': '-', '\u200b': '', '\r': '', '°': ' grados'
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    # Forzar codificación latin-1, reemplazando lo que no sea compatible por '?'
    return texto.encode('latin-1', 'replace').decode('latin-1')

def obtener_credenciales_gcp():
    if Credentials is None:
        raise RuntimeError("No está instalado google-auth. Agrega 'google-auth' y 'gspread' a requirements.txt.")
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly", "https://www.googleapis.com/auth/drive.readonly"]
    
    if "gcp_service_account" in st.secrets:
        return Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    raise RuntimeError("No se encontraron credenciales de Google Sheets en st.secrets.")

@st.cache_data(show_spinner=False, ttl=300)
def obtener_preciario_besco():
    creds = obtener_credenciales_gcp()
    gc = gspread.authorize(creds)
    
    url = st.secrets.get("PRECIARIO_BESCO_URL", "")
    if not url:
        raise RuntimeError("No se encontró PRECIARIO_BESCO_URL en st.secrets.")
        
    sheet = gc.open_by_url(url)
    ws = sheet.get_worksheet(0)
    records = ws.get_all_records()
    
    if not records:
        return pd.DataFrame()
        
    df = pd.DataFrame(records)
    
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    col_clave = next((c for c in df.columns if c in ["CLAVE", "ITEM", "CODIGO", "SKU"]), df.columns[0])
    col_desc = next((c for c in df.columns if c in ["CONCEPTO", "DESCRIPCION", "PRODUCTO"]), df.columns[1])
    col_unidad = next((c for c in df.columns if c in ["UNIDAD", "UOM", "UM"]), "UNIDAD")
    col_tipo = next((c for c in df.columns if "TIPO" in c or "SERVICIO" in c), "TIPO DE SERVICIO")
    
    mapa = {col_clave: "clave", col_desc: "descripcion"}
    if col_unidad in df.columns: mapa[col_unidad] = "unidad"
    if col_tipo in df.columns: mapa[col_tipo] = "tipo_servicio"
    df = df.rename(columns=mapa)
    
    for col in ["clave", "descripcion", "unidad", "tipo_servicio"]:
        if col not in df.columns:
            df[col] = "S/C"
            
    df["descripcion"] = df["descripcion"].astype(str).str.strip()
    df = df[df["descripcion"] != ""].copy()
    
    return df

# ==========================================
# INICIALIZAR ESTADO
# ==========================================
inicializar_session_state()

# ==========================================
# ENCABEZADO Y SECCIÓN 1: CLIENTE
# ==========================================
st.title("💰 Cotizaciones")
st.markdown("## 1. Identificación del cliente y persona que cotiza")

with st.container(border=True):
    col_g1, col_g2 = st.columns(2)
    with col_g1: folio = st.text_input("Folio / OT / TK", value=st.session_state.datos_cotizacion["folio"], placeholder="Ej. COT-001", max_chars=20)
    with col_g2: fecha = st.date_input("Fecha de cotización", value=st.session_state.datos_cotizacion["fecha"])

    col_c1, col_c2 = st.columns(2)
    with col_c1: cliente_nombre = st.text_input("Nombre del cliente", value=st.session_state.datos_cotizacion["cliente_nombre"])
    with col_c2: cliente_empresa = st.text_input("Empresa / Inmueble", value=st.session_state.datos_cotizacion["cliente_empresa"])

    col_c3, col_c4, col_c5 = st.columns(3)
    with col_c3: cliente_contacto = st.text_input("Persona de contacto (Atención)", value=st.session_state.datos_cotizacion["cliente_contacto"])
    with col_c4: cliente_telefono = st.text_input("Teléfono del cliente", value=st.session_state.datos_cotizacion["cliente_telefono"])
    with col_c5: cliente_correo = st.text_input("Correo del cliente", value=st.session_state.datos_cotizacion["cliente_correo"])

    col_p1, col_p2 = st.columns(2)
    with col_p1: cotiza_nombre = st.text_input("Nombre de quien cotiza", value=st.session_state.datos_cotizacion["cotiza_nombre"])
    with col_p2: cotiza_puesto = st.text_input("Puesto", value=st.session_state.datos_cotizacion["cotiza_puesto"])

    # Actualización automática en segundo plano
    st.session_state.datos_cotizacion.update({
        "folio": folio, "fecha": fecha, "cliente_nombre": cliente_nombre, "cliente_empresa": cliente_empresa,
        "cliente_contacto": cliente_contacto, "cliente_telefono": cliente_telefono, "cliente_correo": cliente_correo,
        "cotiza_nombre": cotiza_nombre, "cotiza_puesto": cotiza_puesto
    })

# ==========================================
# SECCIÓN 2: CONCEPTO A COTIZAR
# ==========================================
st.markdown("## 2. Captura de Conceptos")

with st.container(border=True):
    st.session_state.usar_preciario_besco = st.toggle("Habilitar Preciario BESCO", value=st.session_state.usar_preciario_besco)
    
    origen_concepto = "Captura manual"
    clave_preciario, tipo_servicio, descripcion, unidad, precio_unitario = "", "Servicio", "", "PZA", 0.00
    
    if st.session_state.usar_preciario_besco:
        origen_concepto = "Preciario BESCO"
        try:
            df_preciario = obtener_preciario_besco()
            if df_preciario.empty:
                st.warning("El Preciario BESCO está vacío.")
            else:
                columnas_region = [c for c in df_preciario.columns if "PU" in str(c).upper() or "$" in str(c) or "PRECIO" in str(c).upper()]
                columnas_region = [c for c in columnas_region if "METRO NORTE" not in str(c).upper()]
                
                if not columnas_region: columnas_region = ["PRECIO UNITARIO"]
                
                # Identificar el índice de la región Centro para ponerlo por defecto
                centro_idx = 0
                for i, col in enumerate(columnas_region):
                    if "CENTRO" in str(col).upper():
                        centro_idx = i
                        break
                
                col_reg, col_busq = st.columns([1, 2])
                with col_reg:
                    region_seleccionada = st.selectbox("📍 Región de Tarifas", options=columnas_region, index=centro_idx)
                with col_busq:
                    busqueda = st.text_input("🔍 Buscador (escribe clave o concepto):").strip().lower()
                
                df_filtrado = df_preciario.copy()
                if busqueda:
                    mascara = (
                        df_filtrado["clave"].astype(str).str.lower().str.contains(busqueda, na=False) |
                        df_filtrado["descripcion"].astype(str).str.lower().str.contains(busqueda, na=False)
                    )
                    df_filtrado = df_filtrado[mascara]
                
                if df_filtrado.empty:
                    st.warning("No hay coincidencias.")
                else:
                    df_filtrado["opcion_display"] = df_filtrado["clave"].astype(str) + " - " + df_filtrado["descripcion"].astype(str)
                    opcion_seleccionada = st.selectbox("Selecciona un concepto:", options=df_filtrado["opcion_display"].tolist())
                    
                    fila = df_filtrado[df_filtrado["opcion_display"] == opcion_seleccionada].iloc[0]
                    
                    clave_preciario = str(fila.get("clave", "S/C"))
                    tipo_servicio = str(fila.get("tipo_servicio", "S/C"))
                    descripcion = str(fila.get("descripcion", ""))
                    unidad = str(fila.get("unidad", "S/C")) if str(fila.get("unidad", "")) != "" else "S/C"
                    
                    precio_raw = str(fila.get(region_seleccionada, "0")).replace('$', '').replace(',', '').strip()
                    precio_unitario = float(precio_raw) if precio_raw.replace('.', '', 1).isdigit() else 0.00
                    
                    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                    with col_b1: st.text_input("Clave / Item", value=clave_preciario, disabled=True)
                    with col_b2: st.text_input("Tipo de servicio", value=tipo_servicio, disabled=True)
                    with col_b3: st.text_input("Unidad", value=unidad, disabled=True)
                    st.text_area("Descripción de producto o servicio", value=descripcion, height=80, disabled=True)
                    
                    precio_unitario = st.number_input("Precio Unitario Base ($)", value=precio_unitario, format="%.2f")

        except Exception as e:
            st.error(f"Error de conexión: {e}")
            st.session_state.usar_preciario_besco = False

    if not st.session_state.usar_preciario_besco:
        st.info("Modo de captura manual habilitado.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1: tipo_servicio = st.selectbox("Tipo de servicio", ["Aire Acondicionado", "Servicio", "Producto", "Instalación", "Mantenimiento", "Obra Civil", "Otro"])
        with col2: descripcion = st.text_area("Descripción detallada", height=80)
        with col3: unidad = st.selectbox("Unidad", ["PZA", "SERVICIO", "LOTE", "M2", "M3", "HORA", "DÍA", "MES", "KG", "OTRA"])
        precio_unitario = st.number_input("Precio unitario ($)", min_value=0.00, value=0.00, format="%.2f")

    st.markdown("### Cálculo Financiero")
    col4, col5, col6, col7 = st.columns([1, 1, 1, 1])
    with col4:
        cantidad = st.number_input("Cantidad", min_value=0.1, value=1.0, step=1.0)
    with col5:
        utilidad_pct = st.number_input("Utilidad (%)", min_value=0.00, value=23.55, step=0.50, format="%.2f")
    
    utilidad_monto = calcular_utilidad_monto(precio_unitario, utilidad_pct) * cantidad
    precio_venta = calcular_precio_venta(precio_unitario, utilidad_pct)
    importe_total = precio_venta * cantidad

    with col6: st.metric("Precio Venta Unitario", formatear_moneda(precio_venta))
    with col7: st.metric("Importe Total", formatear_moneda(importe_total))

    if st.button("➕ Agregar concepto a la cotización", use_container_width=True, type="primary"):
        if not descripcion.strip():
            st.warning("Debes capturar o seleccionar la descripción.")
        else:
            nuevo_concepto = {
                "Item": clave_preciario,
                "Tipo de servicio": tipo_servicio,
                "Concepto": descripcion,
                "Unidad": unidad,
                "Cantidad": cantidad,
                "PU Base": round(precio_unitario, 2),
                "Utilidad (%)": round(utilidad_pct, 2),
                "Precio Venta": round(precio_venta, 2),
                "Importe": round(importe_total, 2)
            }
            st.session_state.conceptos_cotizacion.append(nuevo_concepto)
            st.success("Concepto agregado.")
            st.rerun()

# ==========================================
# SECCIÓN 3: RESUMEN Y GENERACIÓN DE PDF
# ==========================================
st.markdown("## 3. Resumen y Documento Final")

if st.session_state.conceptos_cotizacion:
    df = pd.DataFrame(st.session_state.conceptos_cotizacion)
    st.dataframe(df, use_container_width=True, hide_index=True)

    subtotal = float(df["Importe"].sum())
    iva = subtotal * 0.16
    total = subtotal + iva

    c1, c2, c3 = st.columns(3)
    c1.metric("SUBTOTAL", formatear_moneda(subtotal))
    c2.metric("IVA (16%)", formatear_moneda(iva))
    c3.metric("TOTAL PRESUPUESTADO", formatear_moneda(total))

    col_btn_1, col_btn_2 = st.columns(2)
    with col_btn_1:
        if st.button("🗑️ Eliminar último concepto", use_container_width=True):
            st.session_state.conceptos_cotizacion.pop()
            st.rerun()
    with col_btn_2:
        if st.button("♻️ Limpiar toda la cotización", use_container_width=True):
            limpiar_cotizacion()
            st.rerun()
            
    st.markdown("---")
    
    # Lógica de FPDF Integrada con limpieza de caracteres
    datos = st.session_state.datos_cotizacion
    folio_pdf = datos["folio"] if datos["folio"] else "COT-S-N"
    fecha_pdf = datos["fecha"].strftime('%d/%m/%Y') if datos["fecha"] else date.today().strftime('%d/%m/%Y')
    
    class PDFCotizacion(FPDF):
        def header(self):
            if os.path.exists("logo besco 2026.jpeg"):
                self.image("logo besco 2026.jpeg", 10, 8, 30)
            
            self.set_font('Arial', 'B', 24)
            self.set_text_color(30, 58, 95)
            self.set_xy(45, 10)
            self.cell(40, 10, limpiar_texto_pdf("besco"), 0, 0, 'L')
            
            self.set_font('Arial', '', 8)
            self.set_text_color(0, 0, 0)
            self.set_xy(120, 10)
            self.multi_cell(80, 4, limpiar_texto_pdf("Grupo Besco SA de CV\nJOSE IGNACIO BARTOLOACHE # 1910 Col. Acacias, CDMX\nTel. 01 55 55 15 08 65\nRFC. GBE101207523"), 0, 'R')
            self.ln(10)
            
        def footer(self):
            self.set_y(-45)
            self.set_font('Arial', 'I', 7)
            # Cambiadas las viñetas por guiones para evitar errores de codificación latin-1
            terminos = (
                "- TIEMPO DE ENTREGA DE MATERIAL DE 1 A 2 DÍAS HÁBILES.\n"
                "- TIEMPO DE ENTREGA DEL SERVICIO DE 1 A 2 DÍAS HÁBILES.\n"
                "- SE REQUIERE ORDEN DE COMPRA, PEDIDO, O CONTRATO.\n"
                "- PAGO CONTRA ENTREGA DEL SERVICIO.\n"
                "- VIGENCIA DE LA COTIZACIÓN 15 DÍAS.\n"
                "- EL PRECIO QUE SE OFERTA ES POR EL TOTAL DE LOS TRABAJOS.\n"
                "- LOS TRABAJOS SE EJECUTARÁN EN HORARIO HÁBIL, EN CASO DE QUE SE REQUIERA FUERA DEL MISMO SE TENDRÁ VARIACIÓN EN EL COSTO 35%"
            )
            self.multi_cell(0, 4, limpiar_texto_pdf(terminos), 0, 'L')

    # Instanciar y construir PDF
    pdf = PDFCotizacion()
    pdf.add_page()
    
    # Bloque de Información del Cliente
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, limpiar_texto_pdf("CLIENTE:"), 0, 0, 'R')
    pdf.set_font('Arial', '', 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_nombre"].upper()), 0, 0, 'L')
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(45, 5, limpiar_texto_pdf("FECHA DE COTIZACION:"), 0, 0, 'R')
    pdf.set_font('Arial', '', 9)
    pdf.cell(30, 5, limpiar_texto_pdf(fecha_pdf), 0, 1, 'L')
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, limpiar_texto_pdf("EMPRESA:"), 0, 0, 'R')
    pdf.set_font('Arial', '', 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_empresa"].upper()), 0, 0, 'L')
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(45, 5, limpiar_texto_pdf("FECHA VIGENCIA:"), 0, 0, 'R')
    pdf.set_font('Arial', '', 9)
    pdf.cell(30, 5, limpiar_texto_pdf("15 DIAS HABILES"), 0, 1, 'L')
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, limpiar_texto_pdf("FOLIO BESCO:"), 0, 0, 'R')
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(18, 52, 86)
    pdf.cell(80, 5, limpiar_texto_pdf(folio_pdf), 0, 1, 'L')
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(35, 5, limpiar_texto_pdf("ATENCION:"), 0, 0, 'R')
    pdf.set_font('Arial', '', 9)
    pdf.cell(80, 5, limpiar_texto_pdf(datos["cliente_contacto"].upper()), 0, 1, 'L')
    pdf.ln(8)
    
    # Introducción
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, limpiar_texto_pdf("Por medio de la presente y a nombre de Grupo Besco SA de CV, presento la siguiente cotizacion:"), 0, 1, 'L')
    pdf.ln(4)
    
    # Encabezado de Tabla
    pdf.set_fill_color(153, 194, 255)
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(30, 8, limpiar_texto_pdf("CODIGO"), 1, 0, 'C', fill=True)
    pdf.cell(80, 8, limpiar_texto_pdf("CONCEPTO"), 1, 0, 'C', fill=True)
    pdf.cell(15, 8, limpiar_texto_pdf("UNIDAD"), 1, 0, 'C', fill=True)
    pdf.cell(20, 8, limpiar_texto_pdf("CANTIDAD"), 1, 0, 'C', fill=True)
    pdf.cell(20, 8, limpiar_texto_pdf("PU"), 1, 0, 'C', fill=True)
    pdf.cell(25, 8, limpiar_texto_pdf("IMPORTE"), 1, 1, 'C', fill=True)
    
    pdf.set_font('Arial', '', 8)
    
    # Filas Dinámicas
    for c in st.session_state.conceptos_cotizacion:
        if pdf.get_y() > 240:
            pdf.add_page()
            
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        pdf.set_xy(x_start + 30, y_start)
        pdf.multi_cell(80, 5, limpiar_texto_pdf(c['Concepto']), 0, 'L')
        max_y = pdf.get_y()
        h = max_y - y_start if max_y - y_start > 8 else 8
        
        pdf.set_xy(x_start, y_start)
        pdf.cell(30, h, limpiar_texto_pdf(c['Item']), 1, 0, 'C')
        pdf.set_xy(x_start + 30, y_start)
        pdf.cell(80, h, "", 1, 0)
        pdf.set_xy(x_start + 110, y_start)
        pdf.cell(15, h, limpiar_texto_pdf(c['Unidad']), 1, 0, 'C')
        pdf.cell(20, h, limpiar_texto_pdf(f"{c['Cantidad']:.2f}"), 1, 0, 'C')
        pdf.cell(20, h, limpiar_texto_pdf(f"$ {c['Precio Venta']:,.2f}"), 1, 0, 'R')
        pdf.cell(25, h, limpiar_texto_pdf(f"$ {c['Importe']:,.2f}"), 1, 1, 'R')
        
        pdf.set_y(y_start + h)
    
    # Totales
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(145, 6, limpiar_texto_pdf("SUBTOTAL"), 0, 0, 'R')
    pdf.cell(15, 6, limpiar_texto_pdf("$"), 0, 0, 'R')
    pdf.cell(30, 6, limpiar_texto_pdf(f"{subtotal:,.2f}"), 0, 1, 'R')
    
    pdf.cell(145, 6, limpiar_texto_pdf("IVA 16%"), 0, 0, 'R')
    pdf.cell(15, 6, limpiar_texto_pdf("$"), 0, 0, 'R')
    pdf.cell(30, 6, limpiar_texto_pdf(f"{iva:,.2f}"), 0, 1, 'R')
    
    pdf.cell(145, 6, limpiar_texto_pdf("TOTAL PRESUPUESTADO"), 0, 0, 'R')
    pdf.cell(15, 6, limpiar_texto_pdf("$"), 0, 0, 'R')
    pdf.cell(30, 6, limpiar_texto_pdf(f"{total:,.2f}"), 0, 1, 'R')
    
    # Firma Integrada
    if pdf.get_y() > 210:
        pdf.add_page()
        
    pdf.ln(20)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, limpiar_texto_pdf("ATENTAMENTE"), 0, 1, 'C')
    pdf.ln(12)
    pdf.cell(0, 4, limpiar_texto_pdf("___________________________________"), 0, 1, 'C')
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, limpiar_texto_pdf(datos["cotiza_nombre"].strip().upper()), 0, 1, 'C')
    pdf.cell(0, 5, limpiar_texto_pdf(datos["cotiza_puesto"].upper()), 0, 1, 'C')
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, limpiar_texto_pdf("GRUPO BESCO"), 0, 1, 'C')
    
    # Botón de Descarga FPDF
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    st.download_button(
        label="📥 Descargar Cotización en PDF",
        data=pdf_bytes,
        file_name=f"Cotizacion_{folio_pdf}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
else:
    st.info("Agrega conceptos para generar el documento PDF.")
