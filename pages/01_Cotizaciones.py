import os
from datetime import date
import pandas as pd
import streamlit as st

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
    
    # Estandarización de columnas básica
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # Identificar columnas clave dinámicamente
    col_clave = next((c for c in df.columns if c in ["CLAVE", "ITEM", "CODIGO", "SKU"]), df.columns[0])
    col_desc = next((c for c in df.columns if c in ["CONCEPTO", "DESCRIPCION", "PRODUCTO"]), df.columns[1])
    col_unidad = next((c for c in df.columns if c in ["UNIDAD", "UOM", "UM"]), "UNIDAD")
    col_tipo = next((c for c in df.columns if "TIPO" in c or "SERVICIO" in c), "TIPO DE SERVICIO")
    
    # Renombrar a estándar interno para facilitar el manejo
    mapa = {col_clave: "clave", col_desc: "descripcion"}
    if col_unidad in df.columns: mapa[col_unidad] = "unidad"
    if col_tipo in df.columns: mapa[col_tipo] = "tipo_servicio"
    df = df.rename(columns=mapa)
    
    # Si no existen, crearlas vacías
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
    with col_g1: folio = st.text_input("Folio de cotización", value=st.session_state.datos_cotizacion["folio"])
    with col_g2: fecha = st.date_input("Fecha de cotización", value=st.session_state.datos_cotizacion["fecha"])

    col_c1, col_c2 = st.columns(2)
    with col_c1: cliente_nombre = st.text_input("Nombre del cliente", value=st.session_state.datos_cotizacion["cliente_nombre"])
    with col_c2: cliente_empresa = st.text_input("Empresa / Razón social", value=st.session_state.datos_cotizacion["cliente_empresa"])

    col_c3, col_c4, col_c5 = st.columns(3)
    with col_c3: cliente_contacto = st.text_input("Persona de contacto", value=st.session_state.datos_cotizacion["cliente_contacto"])
    with col_c4: cliente_telefono = st.text_input("Teléfono del cliente", value=st.session_state.datos_cotizacion["cliente_telefono"])
    with col_c5: cliente_correo = st.text_input("Correo del cliente", value=st.session_state.datos_cotizacion["cliente_correo"])

    col_p1, col_p2 = st.columns(2)
    with col_p1: cotiza_nombre = st.text_input("Nombre de quien cotiza", value=st.session_state.datos_cotizacion["cotiza_nombre"])
    with col_p2: cotiza_puesto = st.text_input("Puesto", value=st.session_state.datos_cotizacion["cotiza_puesto"])

    if st.button("💾 Guardar datos de identificación", use_container_width=True):
        st.session_state.datos_cotizacion.update({
            "folio": folio, "fecha": fecha, "cliente_nombre": cliente_nombre, "cliente_empresa": cliente_empresa,
            "cliente_contacto": cliente_contacto, "cliente_telefono": cliente_telefono, "cliente_correo": cliente_correo,
            "cotiza_nombre": cotiza_nombre, "cotiza_puesto": cotiza_puesto
        })
        st.success("Datos guardados.")

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
                # Extraer columnas de precios (Regiones) dinámicamente y filtrar opciones no deseadas
                columnas_region = [c for c in df_preciario.columns if "PU" in str(c).upper() or "$" in str(c) or "PRECIO" in str(c).upper()]
                columnas_region = [c for c in columnas_region if "PU METRO NORTE & SUR" not in str(c).upper()]
                
                if not columnas_region: columnas_region = ["PRECIO UNITARIO"]
                
                col_reg, col_busq = st.columns([1, 2])
                with col_reg:
                    region_seleccionada = st.selectbox("📍 Región de Tarifas", options=columnas_region)
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
                    unidad = str(fila.get("unidad", "S/C"))
                    
                    # Limpieza robusta del precio
                    precio_raw = str(fila.get(region_seleccionada, "0")).replace('$', '').replace(',', '').strip()
                    precio_unitario = float(precio_raw) if precio_raw.replace('.', '', 1).isdigit() else 0.00
                    
                    if precio_unitario == 0.00:
                        st.warning("⚠️ Este concepto tiene el precio en $0.00 o en blanco en la base de datos.")

                    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                    with col_b1: st.text_input("Clave / Item", value=clave_preciario, disabled=True)
                    with col_b2: st.text_input("Tipo de servicio", value=tipo_servicio, disabled=True)
                    with col_b3: st.text_input("Unidad", value=unidad, disabled=True)
                    st.text_area("Descripción de producto o servicio", value=descripcion, height=80, disabled=True)
                    
                    # Permite ajustar el precio aunque venga de la base
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
# SECCIÓN 3: CONCEPTOS CAPTURADOS
# ==========================================
st.markdown("## 3. Resumen de Cotización")

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
else:
    st.info("Aún no hay conceptos agregados a la cotización.")
