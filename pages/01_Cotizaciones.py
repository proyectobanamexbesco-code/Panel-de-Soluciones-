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
    page_title="Cotizaciones",
    page_icon="💰",
    layout="wide"
)


# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def inicializar_session_state():
    if "conceptos_cotizacion" not in st.session_state:
        st.session_state.conceptos_cotizacion = []

    if "usar_preciario_besco" not in st.session_state:
        st.session_state.usar_preciario_besco = False

    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = {
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
            "cotiza_correo": ""
        }


def limpiar_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.usar_preciario_besco = False
    st.session_state.datos_cotizacion = {
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
        "cotiza_correo": ""
    }


def toggle_preciario_besco():
    st.session_state.usar_preciario_besco = not st.session_state.usar_preciario_besco


def calcular_precio_venta(precio_unitario: float, utilidad_porcentaje: float) -> float:
    return round(float(precio_unitario) * (1 + (float(utilidad_porcentaje) / 100)), 2)


def calcular_utilidad_monto(precio_unitario: float, utilidad_porcentaje: float) -> float:
    return round(float(precio_unitario) * (float(utilidad_porcentaje) / 100), 2)


def formatear_moneda(valor: float) -> str:
    return f"${float(valor):,.2f}"


def valor_secreto(*claves, default=None):
    """
    Busca una clave primero en st.secrets y luego en variables de entorno.
    """
    for clave in claves:
        # 1) st.secrets directo
        try:
            if clave in st.secrets:
                return st.secrets[clave]
        except Exception:
            pass

        # 2) variables de entorno
        valor_env = os.getenv(clave)
        if valor_env:
            return valor_env

    return default


def obtener_credenciales_gcp():
    """
    Recupera credenciales desde st.secrets o variables de entorno.

    Formatos soportados:
    - st.secrets["gcp_service_account"] = { ...json de la cuenta de servicio... }
    - st.secrets["GOOGLE_SERVICE_ACCOUNT"] = { ... }
    - os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"] = texto JSON
    """
    if Credentials is None:
        raise RuntimeError(
            "No está instalado google-auth. Agrega 'google-auth' y 'gspread' a requirements.txt."
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    # Opción 1: secrets con objeto dict
    try:
        if "gcp_service_account" in st.secrets:
            info = dict(st.secrets["gcp_service_account"])
            return Credentials.from_service_account_info(info, scopes=scopes)
    except Exception:
        pass

    try:
        if "GOOGLE_SERVICE_ACCOUNT" in st.secrets:
            info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
            return Credentials.from_service_account_info(info, scopes=scopes)
    except Exception:
        pass

    # Opción 2: variable de entorno con JSON texto
    service_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_json:
        import json
        info = json.loads(service_json)
        return Credentials.from_service_account_info(info, scopes=scopes)

    raise RuntimeError(
        "No se encontraron credenciales de Google Sheets en st.secrets ni en variables de entorno."
    )


def construir_cliente_gspread():
    """
    Construye el cliente de gspread usando la cuenta de servicio ya configurada.
    """
    if gspread is None:
        raise RuntimeError(
            "No está instalado gspread. Agrega 'gspread' y 'google-auth' a requirements.txt."
        )

    creds = obtener_credenciales_gcp()
    return gspread.authorize(creds)


def obtener_spreadsheet_besco():
    """
    Recupera el spreadsheet del Preciario BESCO usando:
    - URL completa del Google Sheet
    - o clave (spreadsheet key)

    El código intenta encontrar cualquiera de estas claves en secrets/env:
    URL:
      BESCO_PRECIARIO_URL
      PRECIARIO_BESCO_URL
      GOOGLE_SHEETS_URL
      PRECIARIO_URL

    KEY:
      BESCO_PRECIARIO_KEY
      PRECIARIO_BESCO_KEY
      GOOGLE_SHEETS_KEY
      PRECIARIO_KEY
    """
    gc = construir_cliente_gspread()

    spreadsheet_url = valor_secreto(
        "BESCO_PRECIARIO_URL",
        "PRECIARIO_BESCO_URL",
        "GOOGLE_SHEETS_URL",
        "PRECIARIO_URL",
        default=None
    )

    spreadsheet_key = valor_secreto(
        "BESCO_PRECIARIO_KEY",
        "PRECIARIO_BESCO_KEY",
        "GOOGLE_SHEETS_KEY",
        "PRECIARIO_KEY",
        default=None
    )

    if spreadsheet_url:
        return gc.open_by_url(spreadsheet_url)

    if spreadsheet_key:
        return gc.open_by_key(spreadsheet_key)

    raise RuntimeError(
        "No se encontró el vínculo ni la clave del Preciario BESCO en st.secrets o variables de entorno."
    )


def normalizar_columnas_preciario(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandariza nombres de columnas para que el módulo funcione
    aunque el Google Sheet traiga encabezados ligeramente distintos.
    """
    df = df.copy()
    columnas_originales = list(df.columns)

    mapa = {}
    for col in columnas_originales:
        col_norm = str(col).strip().lower()

        if col_norm in ["clave", "codigo", "código", "id", "sku"]:
            mapa[col] = "clave"
        elif col_norm in ["tipo_servicio", "tipo de servicio", "tipo", "servicio"]:
            mapa[col] = "tipo_servicio"
        elif col_norm in [
            "descripcion", "descripción", "descripcion de producto o servicio",
            "descripción de producto o servicio", "concepto", "producto", "servicio_descripcion"
        ]:
            mapa[col] = "descripcion"
        elif col_norm in ["unidad", "uom", "um"]:
            mapa[col] = "unidad"
        elif col_norm in [
            "precio_unitario", "precio unitario", "precio", "costo", "costo unitario"
        ]:
            mapa[col] = "precio_unitario"

    df = df.rename(columns=mapa)

    columnas_obligatorias = ["tipo_servicio", "descripcion", "unidad", "precio_unitario"]
    faltantes = [c for c in columnas_obligatorias if c not in df.columns]

    if faltantes:
        raise ValueError(
            f"El Preciario BESCO no tiene las columnas requeridas. "
            f"Faltan: {', '.join(faltantes)}. "
            f"Columnas detectadas: {', '.join([str(c) for c in df.columns])}"
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

    df = df[df["descripcion"].str.strip() != ""].copy()
    df = df.reset_index(drop=True)

    return df


@st.cache_data(show_spinner=False, ttl=300)
def obtener_preciario_besco():
    """
    Carga el Preciario BESCO desde Google Sheets.
    """
    spreadsheet = obtener_spreadsheet_besco()

    worksheet_name = valor_secreto(
        "BESCO_PRECIARIO_WORKSHEET",
        "PRECIARIO_BESCO_WORKSHEET",
        "GOOGLE_SHEETS_WORKSHEET",
        "PRECIARIO_WORKSHEET",
        default=None
    )

    if worksheet_name:
        worksheet = spreadsheet.worksheet(worksheet_name)
    else:
        worksheet = spreadsheet.get_worksheet(0)

    records = worksheet.get_all_records()

    if not records:
        return pd.DataFrame(columns=["clave", "tipo_servicio", "descripcion", "unidad", "precio_unitario"])

    df = pd.DataFrame(records)
    df = normalizar_columnas_preciario(df)

    return df


# ==========================================
# INICIALIZAR ESTADO
# ==========================================
inicializar_session_state()


# ==========================================
# ENCABEZADO
# ==========================================
st.title("💰 Cotizaciones")
st.markdown("Captura la información del cliente, la persona que cotiza y los conceptos a cotizar.")


# ==========================================
# SECCIÓN 1: IDENTIFICACIÓN DEL CLIENTE
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
            "cotiza_correo": cotiza_correo
        }
        st.success("Datos de identificación guardados correctamente.")


# ==========================================
# SECCIÓN 2: CONCEPTO A COTIZAR
# ==========================================
st.markdown("## 2. Concepto a cotizar")

with st.container(border=True):
    st.markdown("### Modo de captura del concepto")

    col_m1, col_m2 = st.columns([1, 3])

    with col_m1:
        texto_boton = (
            "📘 Deshabilitar Preciario BESCO"
            if st.session_state.usar_preciario_besco
            else "📘 Habilitar Preciario BESCO"
        )

        st.button(
            texto_boton,
            on_click=toggle_preciario_besco,
            use_container_width=True
        )

    with col_m2:
        if st.session_state.usar_preciario_besco:
            st.success("Modo activo: Preciario BESCO")
        else:
            st.info("Modo activo: Captura manual")

    st.markdown("---")

    origen_concepto = "Captura manual"
    clave_preciario = ""
    tipo_servicio = ""
    descripcion = ""
    unidad = ""
    precio_unitario = 0.00

    if st.session_state.usar_preciario_besco:
        origen_concepto = "Preciario BESCO"

        try:
            df_preciario = obtener_preciario_besco()

            if df_preciario.empty:
                st.warning("El Preciario BESCO está vacío.")
            else:
                filtro_texto = st.text_input(
                    "Buscar en Preciario BESCO",
                    placeholder="Escribe clave, descripción, unidad o tipo de servicio"
                ).strip().lower()

                df_filtrado = df_preciario.copy()

                if filtro_texto:
                    mascara = (
                        df_filtrado["clave"].astype(str).str.lower().str.contains(filtro_texto, na=False)
                        | df_filtrado["descripcion"].astype(str).str.lower().str.contains(filtro_texto, na=False)
                        | df_filtrado["unidad"].astype(str).str.lower().str.contains(filtro_texto, na=False)
                        | df_filtrado["tipo_servicio"].astype(str).str.lower().str.contains(filtro_texto, na=False)
                    )
                    df_filtrado = df_filtrado[mascara].copy()

                if df_filtrado.empty:
                    st.warning("No hay coincidencias en el Preciario BESCO con ese filtro.")
                else:
                    df_filtrado["opcion"] = df_filtrado.apply(
                        lambda x: (
                            f"{str(x['clave']).strip()} | "
                            f"{x['descripcion']} | "
                            f"{x['unidad']} | "
                            f"{formatear_moneda(x['precio_unitario'])}"
                        ),
                        axis=1
                    )

                    opcion_seleccionada = st.selectbox(
                        "Selecciona un concepto del Preciario BESCO",
                        options=df_filtrado["opcion"].tolist()
                    )

                    fila = df_filtrado[df_filtrado["opcion"] == opcion_seleccionada].iloc[0]

                    clave_preciario = str(fila["clave"]).strip()
                    tipo_servicio = str(fila["tipo_servicio"]).strip()
                    descripcion = str(fila["descripcion"]).strip()
                    unidad = str(fila["unidad"]).strip()
                    precio_unitario = float(fila["precio_unitario"])

                    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])

                    with col_b1:
                        st.text_input("Clave preciario", value=clave_preciario, disabled=True)

                    with col_b2:
                        st.text_area(
                            "Descripción de producto o servicio",
                            value=descripcion,
                            height=100,
                            disabled=True
                        )

                    with col_b3:
                        st.text_input("Unidad", value=unidad, disabled=True)

                    col_b4, col_b5 = st.columns(2)

                    with col_b4:
                        st.text_input("Tipo de servicio", value=tipo_servicio, disabled=True)

                    with col_b5:
                        st.text_input("Precio unitario", value=formatear_moneda(precio_unitario), disabled=True)

        except Exception as e:
            st.error(f"No se pudo cargar el Preciario BESCO: {e}")
            st.warning(
                "Mientras se corrige el vínculo o la configuración del Google Sheet, puedes usar la captura manual."
            )
            origen_concepto = "Captura manual"

            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                tipo_servicio = st.selectbox(
                    "Tipo de servicio",
                    options=[
                        "Servicio", "Producto", "Instalación",
                        "Mantenimiento", "Refacción", "Proyecto", "Otro"
                    ],
                    index=0
                )

            with col2:
                descripcion = st.text_area(
                    "Descripción de producto o servicio",
                    placeholder="Escribe la descripción del producto o servicio...",
                    height=100
                )

            with col3:
                unidad = st.selectbox(
                    "Unidad",
                    options=[
                        "PZA", "SERVICIO", "LOTE", "PAQUETE", "HORA",
                        "DÍA", "MES", "M2", "M3", "KG", "LITRO", "OTRA"
                    ],
                    index=0
                )

            precio_unitario = st.number_input(
                "Precio unitario",
                min_value=0.00,
                value=0.00,
                step=0.01,
                format="%.2f"
            )

    else:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            tipo_servicio = st.selectbox(
                "Tipo de servicio",
                options=[
                    "Servicio",
                    "Producto",
                    "Instalación",
                    "Mantenimiento",
                    "Refacción",
                    "Proyecto",
                    "Otro"
                ],
                index=0
            )

        with col2:
            descripcion = st.text_area(
                "Descripción de producto o servicio",
                placeholder="Escribe la descripción del producto o servicio...",
                height=100
            )

        with col3:
            unidad = st.selectbox(
                "Unidad",
                options=[
                    "PZA",
                    "SERVICIO",
                    "LOTE",
                    "PAQUETE",
                    "HORA",
                    "DÍA",
                    "MES",
                    "M2",
                    "M3",
                    "KG",
                    "LITRO",
                    "OTRA"
                ],
                index=0
            )

        precio_unitario = st.number_input(
            "Precio unitario",
            min_value=0.00,
            value=0.00,
            step=0.01,
            format="%.2f"
        )

    st.markdown("### Cálculo de utilidad y precio de venta")

    col4, col5, col6 = st.columns(3)

    with col4:
        utilidad_pct = st.number_input(
            "Utilidad (%)",
            min_value=0.00,
            value=23.55,
            step=0.50,
            format="%.2f",
            help="Porcentaje de utilidad. Ejemplo: 23.55"
        )

    utilidad_monto = calcular_utilidad_monto(precio_unitario, utilidad_pct)
    precio_venta = calcular_precio_venta(precio_unitario, utilidad_pct)

    with col5:
        st.metric(
            label="Utilidad en monto",
            value=formatear_moneda(utilidad_monto)
        )

    with col6:
        st.metric(
            label="Precio venta",
            value=formatear_moneda(precio_venta)
        )

    st.markdown("---")

    col7, col8, col9 = st.columns(3)
    with col7:
        st.info(f"**Origen del concepto:** {origen_concepto}")
    with col8:
        st.info(f"**Precio unitario:** {formatear_moneda(precio_unitario)}")
    with col9:
        st.info(f"**Utilidad aplicada:** {utilidad_pct:.2f}%")

    agregar = st.button("➕ Agregar concepto", use_container_width=True)

    if agregar:
        if not str(descripcion).strip():
            st.warning("Debes capturar o seleccionar la descripción de producto o servicio.")
        else:
            datos = st.session_state.datos_cotizacion

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
                "Descripción de producto o servicio": str(descripcion).strip(),
                "Unidad": unidad,
                "Precio unitario": round(float(precio_unitario), 2),
                "Utilidad (%)": round(float(utilidad_pct), 2),
                "Utilidad ($)": round(float(utilidad_monto), 2),
                "Precio venta": round(float(precio_venta), 2)
            }

            st.session_state.conceptos_cotizacion.append(nuevo_concepto)
            st.success("Concepto agregado correctamente.")


# ==========================================
# SECCIÓN 3: RESUMEN DE IDENTIFICACIÓN
# ==========================================
st.markdown("## 3. Resumen de identificación")

datos = st.session_state.datos_cotizacion

with st.container(border=True):
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("### Cliente")
        st.write(f"**Folio:** {datos['folio']}")
        st.write(f"**Fecha:** {datos['fecha'] if datos['fecha'] else ''}")
        st.write(f"**Nombre del cliente:** {datos['cliente_nombre']}")
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
# SECCIÓN 4: CONCEPTOS CAPTURADOS
# ==========================================
st.markdown("## 4. Conceptos capturados")

if st.session_state.conceptos_cotizacion:
    df = pd.DataFrame(st.session_state.conceptos_cotizacion)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    total_precio_unitario = float(df["Precio unitario"].sum())
    total_utilidad = float(df["Utilidad ($)"].sum())
    total_precio_venta = float(df["Precio venta"].sum())

    st.markdown("### Totales")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total precio unitario", formatear_moneda(total_precio_unitario))
    c2.metric("Total utilidad", formatear_moneda(total_utilidad))
    c3.metric("Total precio venta", formatear_moneda(total_precio_venta))

    st.markdown("---")

    col_btn_1, col_btn_2, col_btn_3 = st.columns(3)

    with col_btn_1:
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Descargar cotización en CSV",
            data=csv,
            file_name="cotizacion.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_btn_2:
        if st.button("🗑️ Eliminar último concepto", use_container_width=True):
            st.session_state.conceptos_cotizacion.pop()
            st.rerun()

    with col_btn_3:
        if st.button("♻️ Limpiar toda la cotización", use_container_width=True):
            limpiar_cotizacion()
            st.rerun()
else:
    st.info("Aún no hay conceptos agregados a la cotización.")


# ==========================================
# APOYO TÉCNICO
# ==========================================
with st.expander("Ver fórmula utilizada para el precio de venta"):
    st.write("**Precio venta = Precio unitario x (1 + Utilidad % / 100)**")
    st.code(
        "precio_venta = precio_unitario * (1 + utilidad_porcentaje / 100)",
        language="python"
    )

with st.expander("Diagnóstico de conexión con Preciario BESCO"):
    try:
        url_detectada = valor_secreto(
            "BESCO_PRECIARIO_URL",
            "PRECIARIO_BESCO_URL",
            "GOOGLE_SHEETS_URL",
            "PRECIARIO_URL",
            default=""
        )
        key_detectada = valor_secreto(
            "BESCO_PRECIARIO_KEY",
            "PRECIARIO_BESCO_KEY",
            "GOOGLE_SHEETS_KEY",
            "PRECIARIO_KEY",
            default=""
        )
        worksheet_detectada = valor_secreto(
            "BESCO_PRECIARIO_WORKSHEET",
            "PRECIARIO_BESCO_WORKSHEET",
            "GOOGLE_SHEETS_WORKSHEET",
            "PRECIARIO_WORKSHEET",
            default=""
        )

        st.write(f"**URL detectada:** {'Sí' if url_detectada else 'No'}")
        st.write(f"**KEY detectada:** {'Sí' if key_detectada else 'No'}")
        st.write(f"**Worksheet configurada:** {worksheet_detectada if worksheet_detectada else 'Primera hoja'}")

        if st.button("🔄 Probar carga del Preciario BESCO", use_container_width=True):
            df_test = obtener_preciario_besco()
            st.success(f"Preciario cargado correctamente. Registros encontrados: {len(df_test)}")
            st.dataframe(df_test.head(20), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Diagnóstico: {e}")
