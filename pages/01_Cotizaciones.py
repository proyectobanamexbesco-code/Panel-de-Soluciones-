import json
import os
from datetime import date

import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_DISPONIBLE = True
except ImportError:
    gspread = None
    Credentials = None
    GSPREAD_DISPONIBLE = False


# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizaciones",
    page_icon="💰",
    layout="wide"
)


# ==========================================
# CONSTANTES
# ==========================================
TIPOS_SERVICIO = [
    "Servicio", "Producto", "Instalación",
    "Mantenimiento", "Refacción", "Proyecto", "Otro"
]

UNIDADES = [
    "PZA", "SERVICIO", "LOTE", "PAQUETE", "HORA",
    "DÍA", "MES", "M2", "M3", "KG", "LITRO", "OTRA"
]

CLAVES_URL_PRECIARIO = [
    "BESCO_PRECIARIO_URL", "PRECIARIO_BESCO_URL",
    "GOOGLE_SHEETS_URL", "PRECIARIO_URL"
]

CLAVES_KEY_PRECIARIO = [
    "BESCO_PRECIARIO_KEY", "PRECIARIO_BESCO_KEY",
    "GOOGLE_SHEETS_KEY", "PRECIARIO_KEY"
]

CLAVES_WORKSHEET_PRECIARIO = [
    "BESCO_PRECIARIO_WORKSHEET", "PRECIARIO_BESCO_WORKSHEET",
    "GOOGLE_SHEETS_WORKSHEET", "PRECIARIO_WORKSHEET"
]

IVA_PORCENTAJE = 16.0


# ==========================================
# ESTADO INICIAL
# ==========================================
def _datos_cotizacion_vacios() -> dict:
    return {
        "folio": "",
        "fecha": date.today(),
        "cliente_nombre": "",
        "cliente_empresa": "",
        "cliente_contacto": "",
        "cliente_telefono": "",
        "cliente_correo": "",
        "cotiza_nombre": "",
        "cotiza_puesto": "",
        "cotiza_telefono": "",
        "cotiza_correo": "",
    }


def inicializar_session_state():
    if "conceptos_cotizacion" not in st.session_state:
        st.session_state.conceptos_cotizacion = []

    if "usar_preciario_besco" not in st.session_state:
        st.session_state.usar_preciario_besco = False

    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = _datos_cotizacion_vacios()


def limpiar_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.usar_preciario_besco = False
    st.session_state.datos_cotizacion = _datos_cotizacion_vacios()


def toggle_preciario_besco():
    st.session_state.usar_preciario_besco = not st.session_state.usar_preciario_besco


# ==========================================
# FUNCIONES DE CÁLCULO Y FORMATO
# ==========================================
def calcular_precio_venta(precio_unitario: float, utilidad_pct: float) -> float:
    return round(precio_unitario * (1 + utilidad_pct / 100), 2)


def calcular_utilidad_monto(precio_unitario: float, utilidad_pct: float) -> float:
    return round(precio_unitario * (utilidad_pct / 100), 2)


def formatear_moneda(valor: float) -> str:
    return f"${float(valor):,.2f}"


# ==========================================
# ACCESO A SECRETS / ENV
# ==========================================
def valor_secreto(*claves, default=None):
    """Busca una clave en st.secrets y luego en variables de entorno."""
    for clave in claves:
        try:
            if clave in st.secrets:
                return st.secrets[clave]
        except Exception:
            pass

        valor_env = os.getenv(clave)
        if valor_env:
            return valor_env

    return default


# ==========================================
# GOOGLE SHEETS — CREDENCIALES Y CLIENTE
# ==========================================
def obtener_credenciales_gcp() -> "Credentials":
    if not GSPREAD_DISPONIBLE:
        raise RuntimeError(
            "Dependencias faltantes: agrega 'gspread' y 'google-auth' a requirements.txt."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    for clave in ("gcp_service_account", "GOOGLE_SERVICE_ACCOUNT"):
        try:
            if clave in st.secrets:
                info = dict(st.secrets[clave])
                return Credentials.from_service_account_info(info, scopes=scopes)
        except Exception:
            pass

    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_json:
        info = json.loads(service_json)
        return Credentials.from_service_account_info(info, scopes=scopes)

    raise RuntimeError(
        "No se encontraron credenciales de Google en st.secrets ni en variables de entorno."
    )


def construir_cliente_gspread() -> "gspread.Client":
    creds = obtener_credenciales_gcp()
    # gspread.authorize() está deprecado desde v5; se usa Client directamente.
    return gspread.Client(auth=creds)


def _abrir_spreadsheet(gc: "gspread.Client") -> "gspread.Spreadsheet":
    url = valor_secreto(*CLAVES_URL_PRECIARIO, default=None)
    if url:
        return gc.open_by_url(url)

    key = valor_secreto(*CLAVES_KEY_PRECIARIO, default=None)
    if key:
        return gc.open_by_key(key)

    raise RuntimeError(
        "No se encontró URL ni clave del Preciario BESCO "
        "en st.secrets o variables de entorno."
    )


def _cargar_registros_hoja() -> list[dict]:
    """Abre el spreadsheet y devuelve los registros sin caché de objetos gspread."""
    gc = construir_cliente_gspread()
    spreadsheet = _abrir_spreadsheet(gc)

    worksheet_name = valor_secreto(*CLAVES_WORKSHEET_PRECIARIO, default=None)
    worksheet = (
        spreadsheet.worksheet(worksheet_name)
        if worksheet_name
        else spreadsheet.get_worksheet(0)
    )
    return worksheet.get_all_records()


# ==========================================
# NORMALIZACIÓN DEL PRECIARIO
# ==========================================
def normalizar_columnas_preciario(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza encabezados del Google Sheet independientemente de su capitalización."""
    df = df.copy()

    mapa = {}
    for col in df.columns:
        cn = str(col).strip().lower()

        if cn in {"clave", "codigo", "código", "id", "sku"}:
            mapa[col] = "clave"
        elif cn in {"tipo_servicio", "tipo de servicio", "tipo", "servicio"}:
            mapa[col] = "tipo_servicio"
        elif cn in {
            "descripcion", "descripción",
            "descripcion de producto o servicio",
            "descripción de producto o servicio",
            "concepto", "producto", "servicio_descripcion"
        }:
            mapa[col] = "descripcion"
        elif cn in {"unidad", "uom", "um"}:
            mapa[col] = "unidad"
        elif cn in {
            "precio_unitario", "precio unitario",
            "precio", "costo", "costo unitario"
        }:
            mapa[col] = "precio_unitario"

    df = df.rename(columns=mapa)

    obligatorias = {"tipo_servicio", "descripcion", "unidad", "precio_unitario"}
    faltantes = obligatorias - set(df.columns)
    if faltantes:
        raise ValueError(
            f"El Preciario BESCO no tiene columnas requeridas. "
            f"Faltan: {', '.join(sorted(faltantes))}. "
            f"Detectadas: {', '.join(str(c) for c in df.columns)}"
        )

    if "clave" not in df.columns:
        df["clave"] = ""

    df["tipo_servicio"] = df["tipo_servicio"].fillna("").astype(str)
    df["descripcion"] = df["descripcion"].fillna("").astype(str)
    df["unidad"] = df["unidad"].fillna("").astype(str)
    df["precio_unitario"] = (
        df["precio_unitario"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce").fillna(0.0)

    df = df[df["descripcion"].str.strip() != ""].reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False, ttl=300)
def obtener_preciario_besco() -> pd.DataFrame:
    """Carga y normaliza el Preciario BESCO desde Google Sheets (caché 5 min)."""
    registros = _cargar_registros_hoja()

    if not registros:
        return pd.DataFrame(
            columns=["clave", "tipo_servicio", "descripcion", "unidad", "precio_unitario"]
        )

    df = pd.DataFrame(registros)
    return normalizar_columnas_preciario(df)


# ==========================================
# COMPONENTES DE UI REUTILIZABLES
# ==========================================
def ui_captura_manual():
    """Renderiza los campos de captura manual y devuelve los valores."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        tipo_servicio = st.selectbox("Tipo de servicio", options=TIPOS_SERVICIO)

    with col2:
        descripcion = st.text_area(
            "Descripción de producto o servicio",
            placeholder="Escribe la descripción del producto o servicio...",
            height=100
        )

    with col3:
        unidad = st.selectbox("Unidad", options=UNIDADES)

    precio_unitario = st.number_input(
        "Precio unitario", min_value=0.00, value=0.00, step=0.01, format="%.2f"
    )

    return "", tipo_servicio, descripcion, unidad, precio_unitario


def ui_captura_desde_preciario():
    """
    Renderiza la búsqueda y selección del Preciario BESCO.
    Devuelve (clave, tipo_servicio, descripcion, unidad, precio_unitario).
    Lanza excepción si el Preciario no carga.
    """
    df_preciario = obtener_preciario_besco()

    if df_preciario.empty:
        st.warning("El Preciario BESCO está vacío.")
        return "", "", "", "", 0.00

    filtro = st.text_input(
        "Buscar en Preciario BESCO",
        placeholder="Clave, descripción, unidad o tipo de servicio"
    ).strip().lower()

    df_filtrado = df_preciario.copy()

    if filtro:
        mascara = (
            df_filtrado["clave"].astype(str).str.lower().str.contains(filtro, na=False)
            | df_filtrado["descripcion"].str.lower().str.contains(filtro, na=False)
            | df_filtrado["unidad"].str.lower().str.contains(filtro, na=False)
            | df_filtrado["tipo_servicio"].str.lower().str.contains(filtro, na=False)
        )
        df_filtrado = df_filtrado[mascara].copy()

    if df_filtrado.empty:
        st.warning("Sin coincidencias en el Preciario BESCO con ese filtro.")
        return "", "", "", "", 0.00

    df_filtrado["_opcion"] = df_filtrado.apply(
        lambda x: (
            f"{str(x['clave']).strip()} | "
            f"{x['descripcion']} | "
            f"{x['unidad']} | "
            f"{formatear_moneda(x['precio_unitario'])}"
        ),
        axis=1
    )

    opcion = st.selectbox(
        "Selecciona un concepto del Preciario BESCO",
        options=df_filtrado["_opcion"].tolist()
    )

    fila = df_filtrado[df_filtrado["_opcion"] == opcion].iloc[0]

    clave = str(fila["clave"]).strip()
    tipo_servicio = str(fila["tipo_servicio"]).strip()
    descripcion = str(fila["descripcion"]).strip()
    unidad = str(fila["unidad"]).strip()
    precio_unitario = float(fila["precio_unitario"])

    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b1:
        st.text_input("Clave preciario", value=clave, disabled=True)
    with col_b2:
        st.text_area("Descripción", value=descripcion, height=100, disabled=True)
    with col_b3:
        st.text_input("Unidad", value=unidad, disabled=True)

    col_b4, col_b5 = st.columns(2)
    with col_b4:
        st.text_input("Tipo de servicio", value=tipo_servicio, disabled=True)
    with col_b5:
        st.text_input("Precio unitario", value=formatear_moneda(precio_unitario), disabled=True)

    return clave, tipo_servicio, descripcion, unidad, precio_unitario


# ==========================================
# INICIALIZAR ESTADO
# ==========================================
inicializar_session_state()


# ==========================================
# ENCABEZADO
# ==========================================
st.title("💰 Cotizaciones")
st.markdown(
    "Captura la información del cliente, la persona que cotiza y los conceptos a cotizar."
)


# ==========================================
# SECCIÓN 1 — IDENTIFICACIÓN
# ==========================================
st.markdown("## 1. Identificación del cliente y persona que cotiza")

with st.container(border=True):
    st.markdown("### Datos generales de la cotización")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        folio = st.text_input(
            "Folio de cotización",
            value=st.session_state.datos_cotizacion["folio"],
            placeholder="Ej. COT-2026-001"
        )
    with col_g2:
        fecha = st.date_input(
            "Fecha de cotización",
            value=st.session_state.datos_cotizacion["fecha"]
        )

    st.markdown("### Identificación del cliente")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cliente_nombre = st.text_input(
            "Nombre del cliente",
            value=st.session_state.datos_cotizacion["cliente_nombre"],
            placeholder="Nombre de la persona o cliente"
        )
    with col_c2:
        cliente_empresa = st.text_input(
            "Empresa / Razón social",
            value=st.session_state.datos_cotizacion["cliente_empresa"],
            placeholder="Nombre de la empresa"
        )

    col_c3, col_c4, col_c5 = st.columns(3)
    with col_c3:
        cliente_contacto = st.text_input(
            "Persona de contacto",
            value=st.session_state.datos_cotizacion["cliente_contacto"],
            placeholder="Nombre del contacto"
        )
    with col_c4:
        cliente_telefono = st.text_input(
            "Teléfono del cliente",
            value=st.session_state.datos_cotizacion["cliente_telefono"],
            placeholder="Ej. 55 1234 5678"
        )
    with col_c5:
        cliente_correo = st.text_input(
            "Correo del cliente",
            value=st.session_state.datos_cotizacion["cliente_correo"],
            placeholder="correo@empresa.com"
        )

    st.markdown("### Persona que cotiza")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        cotiza_nombre = st.text_input(
            "Nombre de quien cotiza",
            value=st.session_state.datos_cotizacion["cotiza_nombre"],
            placeholder="Nombre del ejecutivo o responsable"
        )
    with col_p2:
        cotiza_puesto = st.text_input(
            "Puesto",
            value=st.session_state.datos_cotizacion["cotiza_puesto"],
            placeholder="Ej. Gerente de Servicio"
        )

    col_p3, col_p4 = st.columns(2)
    with col_p3:
        cotiza_telefono = st.text_input(
            "Teléfono de quien cotiza",
            value=st.session_state.datos_cotizacion["cotiza_telefono"],
            placeholder="Ej. 55 9876 5432"
        )
    with col_p4:
        cotiza_correo = st.text_input(
            "Correo de quien cotiza",
            value=st.session_state.datos_cotizacion["cotiza_correo"],
            placeholder="correo@empresa.com"
        )

    if st.button("💾 Guardar datos de identificación", use_container_width=True):
        st.session_state.datos_cotizacion = {
            "folio": folio,
            "fecha": fecha,
            "cliente_nombre": cliente_nombre,
            "cliente_empresa": cliente_empresa,
            "cliente_contacto": cliente_contacto,
            "cliente_telefono": cliente_telefono,
            "cliente_correo": cliente_correo,
            "cotiza_nombre": cotiza_nombre,
            "cotiza_puesto": cotiza_puesto,
            "cotiza_telefono": cotiza_telefono,
            "cotiza_correo": cotiza_correo,
        }
        st.success("Datos de identificación guardados correctamente.")


# ==========================================
# SECCIÓN 2 — CONCEPTO A COTIZAR
# ==========================================
st.markdown("## 2. Concepto a cotizar")

with st.container(border=True):
    st.markdown("### Modo de captura del concepto")

    col_m1, col_m2 = st.columns([1, 3])
    with col_m1:
        label_btn = (
            "📘 Deshabilitar Preciario BESCO"
            if st.session_state.usar_preciario_besco
            else "📘 Habilitar Preciario BESCO"
        )
        st.button(label_btn, on_click=toggle_preciario_besco, use_container_width=True)
    with col_m2:
        if st.session_state.usar_preciario_besco:
            st.success("Modo activo: Preciario BESCO")
        else:
            st.info("Modo activo: Captura manual")

    st.markdown("---")

    # Variables con valores por defecto
    origen_concepto = "Captura manual"
    clave_preciario = ""
    tipo_servicio = ""
    descripcion = ""
    unidad = ""
    precio_unitario = 0.00

    if st.session_state.usar_preciario_besco:
        origen_concepto = "Preciario BESCO"
        try:
            clave_preciario, tipo_servicio, descripcion, unidad, precio_unitario = (
                ui_captura_desde_preciario()
            )
        except Exception as e:
            st.error(f"No se pudo cargar el Preciario BESCO: {e}")
            st.warning(
                "Mientras se corrige la configuración, puedes usar la captura manual."
            )
            origen_concepto = "Captura manual"
            clave_preciario, tipo_servicio, descripcion, unidad, precio_unitario = (
                ui_captura_manual()
            )
    else:
        clave_preciario, tipo_servicio, descripcion, unidad, precio_unitario = (
            ui_captura_manual()
        )

    st.markdown("### Cantidad y cálculo de utilidad")

    col_cant, col_util = st.columns(2)
    with col_cant:
        cantidad = st.number_input(
            "Cantidad",
            min_value=0.00,
            value=1.00,
            step=1.00,
            format="%.2f"
        )
    with col_util:
        utilidad_pct = st.number_input(
            "Utilidad (%)",
            min_value=0.00,
            value=23.55,
            step=0.50,
            format="%.2f",
            help="Porcentaje de utilidad sobre el precio unitario."
        )

    utilidad_monto_u = calcular_utilidad_monto(precio_unitario, utilidad_pct)
    precio_venta_u = calcular_precio_venta(precio_unitario, utilidad_pct)
    subtotal = round(precio_venta_u * cantidad, 2)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Utilidad / u", formatear_moneda(utilidad_monto_u))
    col_m2.metric("Precio venta / u", formatear_moneda(precio_venta_u))
    col_m3.metric("Cantidad", f"{cantidad:,.2f}")
    col_m4.metric("Subtotal", formatear_moneda(subtotal))

    st.markdown("---")

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.info(f"**Origen:** {origen_concepto}")
    with col_info2:
        st.info(f"**Precio unitario:** {formatear_moneda(precio_unitario)}")
    with col_info3:
        st.info(f"**Utilidad aplicada:** {utilidad_pct:.2f}%")

    if st.button("➕ Agregar concepto", use_container_width=True):
        datos = st.session_state.datos_cotizacion
        errores = []

        if not str(descripcion).strip():
            errores.append("La descripción del producto o servicio es obligatoria.")
        if cantidad <= 0:
            errores.append("La cantidad debe ser mayor a cero.")

        if errores:
            for e in errores:
                st.warning(e)
        else:
            nuevo_concepto = {
                "Folio": datos["folio"],
                "Fecha": str(datos["fecha"]) if datos["fecha"] else "",
                "Cliente": datos["cliente_nombre"],
                "Empresa / Razón social": datos["cliente_empresa"],
                "Contacto cliente": datos["cliente_contacto"],
                "Teléfono cliente": datos["cliente_telefono"],
                "Correo cliente": datos["cliente_correo"],
                "Persona que cotiza": datos["cotiza_nombre"],
                "Puesto": datos["cotiza_puesto"],
                "Teléfono quien cotiza": datos["cotiza_telefono"],
                "Correo quien cotiza": datos["cotiza_correo"],
                "Origen concepto": origen_concepto,
                "Clave preciario": clave_preciario,
                "Tipo de servicio": tipo_servicio,
                "Descripción": str(descripcion).strip(),
                "Unidad": unidad,
                "Cantidad": round(float(cantidad), 2),
                "Precio unitario": round(float(precio_unitario), 2),
                "Utilidad (%)": round(float(utilidad_pct), 2),
                "Utilidad ($)": round(float(utilidad_monto_u), 2),
                "Precio venta / u": round(float(precio_venta_u), 2),
                "Subtotal": round(float(subtotal), 2),
            }

            st.session_state.conceptos_cotizacion.append(nuevo_concepto)
            st.success("Concepto agregado correctamente.")


# ==========================================
# SECCIÓN 3 — RESUMEN DE IDENTIFICACIÓN
# ==========================================
st.markdown("## 3. Resumen de identificación")

datos = st.session_state.datos_cotizacion

with st.container(border=True):
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("### Cliente")
        st.write(f"**Folio:** {datos['folio']}")
        st.write(f"**Fecha:** {datos['fecha'] or ''}")
        st.write(f"**Nombre:** {datos['cliente_nombre']}")
        st.write(f"**Empresa / Razón social:** {datos['cliente_empresa']}")
        st.write(f"**Persona de contacto:** {datos['cliente_contacto']}")
        st.write(f"**Teléfono:** {datos['cliente_telefono']}")
        st.write(f"**Correo:** {datos['cliente_correo']}")

    with col_r2:
        st.markdown("### Persona que cotiza")
        st.write(f"**Nombre:** {datos['cotiza_nombre']}")
        st.write(f"**Puesto:** {datos['cotiza_puesto']}")
        st.write(f"**Teléfono:** {datos['cotiza_telefono']}")
        st.write(f"**Correo:** {datos['cotiza_correo']}")


# ==========================================
# SECCIÓN 4 — CONCEPTOS CAPTURADOS
# ==========================================
st.markdown("## 4. Conceptos capturados")

if st.session_state.conceptos_cotizacion:
    df = pd.DataFrame(st.session_state.conceptos_cotizacion)

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Totales con IVA
    total_precio_unitario = float(df["Precio unitario"].sum())
    total_utilidad = float(df["Utilidad ($)"].sum())
    subtotal_total = float(df["Subtotal"].sum())
    iva_monto = round(subtotal_total * IVA_PORCENTAJE / 100, 2)
    total_con_iva = round(subtotal_total + iva_monto, 2)

    st.markdown("### Totales")

    col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
    col_t1.metric("Suma precio unitario", formatear_moneda(total_precio_unitario))
    col_t2.metric("Suma utilidad", formatear_moneda(total_utilidad))
    col_t3.metric("Subtotal", formatear_moneda(subtotal_total))
    col_t4.metric(f"IVA ({IVA_PORCENTAJE:.0f}%)", formatear_moneda(iva_monto))
    col_t5.metric("Total con IVA", formatear_moneda(total_con_iva))

    st.markdown("---")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Descargar cotización CSV",
            data=csv,
            file_name=f"cotizacion_{datos['folio'] or 'sin_folio'}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_btn2:
        if st.button("🗑️ Eliminar último concepto", use_container_width=True):
            st.session_state.conceptos_cotizacion.pop()
            st.rerun()

    with col_btn3:
        if st.button("♻️ Limpiar toda la cotización", use_container_width=True):
            limpiar_cotizacion()
            st.rerun()

else:
    st.info("Aún no hay conceptos agregados a la cotización.")


# ==========================================
# APOYO TÉCNICO
# ==========================================
with st.expander("Ver fórmula utilizada para el precio de venta"):
    st.write("**Precio venta = Precio unitario × (1 + Utilidad % / 100)**")
    st.code(
        "precio_venta = precio_unitario * (1 + utilidad_porcentaje / 100)",
        language="python"
    )
    st.write("**Subtotal = Precio venta × Cantidad**")
    st.code(
        "subtotal = precio_venta * cantidad",
        language="python"
    )

with st.expander("Diagnóstico de conexión con Preciario BESCO"):
    url_det = valor_secreto(*CLAVES_URL_PRECIARIO, default="")
    key_det = valor_secreto(*CLAVES_KEY_PRECIARIO, default="")
    ws_det = valor_secreto(*CLAVES_WORKSHEET_PRECIARIO, default="")

    st.write(f"**gspread disponible:** {'Sí' if GSPREAD_DISPONIBLE else 'No — instala gspread y google-auth'}")
    st.write(f"**URL detectada:** {'Sí' if url_det else 'No'}")
    st.write(f"**KEY detectada:** {'Sí' if key_det else 'No'}")
    st.write(f"**Worksheet configurada:** {ws_det or 'Primera hoja (por defecto)'}")

    if st.button("🔄 Probar carga del Preciario BESCO", use_container_width=True):
        try:
            obtener_preciario_besco.clear()
            df_test = obtener_preciario_besco()
            st.success(f"Preciario cargado correctamente. Registros encontrados: {len(df_test)}")
            st.dataframe(df_test.head(20), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error al cargar el Preciario: {e}")
