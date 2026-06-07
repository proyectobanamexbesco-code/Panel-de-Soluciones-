import streamlit as st
import pandas as pd


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

    if "datos_cotizacion" not in st.session_state:
        st.session_state.datos_cotizacion = {
            "folio": "",
            "fecha": None,
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


def calcular_precio_venta(precio_unitario: float, utilidad_porcentaje: float) -> float:
    """
    Calcula el precio de venta a partir del precio unitario y la utilidad (%).
    Fórmula:
        precio_venta = precio_unitario * (1 + utilidad_porcentaje / 100)
    """
    return round(precio_unitario * (1 + (utilidad_porcentaje / 100)), 2)


def calcular_utilidad_monto(precio_unitario: float, utilidad_porcentaje: float) -> float:
    """
    Calcula el monto de utilidad en dinero.
    """
    return round(precio_unitario * (utilidad_porcentaje / 100), 2)


def formatear_moneda(valor: float) -> str:
    return f"${valor:,.2f}"


def limpiar_cotizacion():
    st.session_state.conceptos_cotizacion = []
    st.session_state.datos_cotizacion = {
        "folio": "",
        "fecha": None,
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

    col4, col5, col6 = st.columns(3)

    with col4:
        precio_unitario = st.number_input(
            "Precio unitario",
            min_value=0.00,
            value=0.00,
            step=0.01,
            format="%.2f"
        )

    with col5:
        utilidad_pct = st.number_input(
            "Utilidad (%)",
            min_value=0.00,
            value=23.55,
            step=0.50,
            format="%.2f",
            help="Porcentaje de utilidad. Ejemplo: 23.55"
        )

    precio_venta = calcular_precio_venta(precio_unitario, utilidad_pct)
    utilidad_monto = calcular_utilidad_monto(precio_unitario, utilidad_pct)

    with col6:
        st.markdown("##### Precio venta")
        st.metric(
            label="Calculado automáticamente",
            value=formatear_moneda(precio_venta)
        )

    st.markdown("---")

    col7, col8, col9 = st.columns(3)
    with col7:
        st.info(f"**Utilidad en monto:** {formatear_moneda(utilidad_monto)}")
    with col8:
        st.info(f"**Precio unitario:** {formatear_moneda(precio_unitario)}")
    with col9:
        st.info(f"**Utilidad aplicada:** {utilidad_pct:.2f}%")

    agregar = st.button("➕ Agregar concepto", use_container_width=True)

    if agregar:
        if not descripcion.strip():
            st.warning("Debes capturar la **descripción de producto o servicio**.")
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
                "Tipo de servicio": tipo_servicio,
                "Descripción de producto o servicio": descripcion.strip(),
                "Unidad": unidad,
                "Precio unitario": round(precio_unitario, 2),
                "Utilidad (%)": round(utilidad_pct, 2),
                "Utilidad ($)": utilidad_monto,
                "Precio venta": precio_venta
            }

            st.session_state.conceptos_cotizacion.append(nuevo_concepto)
            st.success("Concepto agregado correctamente.")


# ==========================================
# RESUMEN DE IDENTIFICACIÓN
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
# TABLA DE CONCEPTOS
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
# FÓRMULA UTILIZADA
# ==========================================
with st.expander("Ver fórmula utilizada para el precio de venta"):
    st.write("**Precio venta = Precio unitario x (1 + Utilidad % / 100)**")
    st.code(
        "precio_venta = precio_unitario * (1 + utilidad_porcentaje / 100)",
        language="python"
    )
