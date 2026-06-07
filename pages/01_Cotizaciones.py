import streamlit as st
import pandas as pd


# =========================
# CONFIGURACIÓN DE PÁGINA
# =========================
st.set_page_config(page_title="Cotizaciones", page_icon="💰", layout="wide")


# =========================
# FUNCIONES AUXILIARES
# =========================
def inicializar_session_state():
    if "conceptos_cotizacion" not in st.session_state:
        st.session_state.conceptos_cotizacion = []


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


# =========================
# INICIALIZAR ESTADO
# =========================
inicializar_session_state()


# =========================
# ENCABEZADO
# =========================
st.title("💰 Cotizaciones")
st.markdown("Captura los conceptos a cotizar y calcula automáticamente el **precio de venta**.")


# =========================
# FORMULARIO DE CAPTURA
# =========================
with st.container(border=True):
    st.subheader("Concepto a cotizar")

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
            nuevo_concepto = {
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


# =========================
# TABLA DE CONCEPTOS
# =========================
st.markdown("## Conceptos capturados")

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
