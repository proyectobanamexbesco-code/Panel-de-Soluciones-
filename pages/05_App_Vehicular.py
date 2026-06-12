import streamlit as st
import pandas as pd
import tempfile
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PIL import Image


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "App Vehicular"
PAGE_ICON = "🚗"
LAYOUT = "wide"

EXCEL_FILE = "CONCENTRADO REGION CENTRO 1.xlsx"

PDF_MARGIN_LEFT = 45
PDF_MARGIN_RIGHT = 45
PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT = letter


# =========================================================
# CONFIGURAR PÁGINA
# =========================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)


# =========================================================
# ESTILOS
# =========================================================
def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
        .vehicular-header {
            text-align: center;
            padding: 0.5rem 0 1rem 0;
        }

        .vehicular-title {
            font-size: 2.1rem;
            font-weight: 800;
            color: #1E3A5F;
            margin-bottom: 0.2rem;
        }

        .vehicular-subtitle {
            font-size: 1rem;
            color: #5B6573;
            margin-bottom: 1rem;
        }

        .info-card {
            background: linear-gradient(135deg, #F7F9FC 0%, #EEF3F8 100%);
            border: 1px solid #D9E2EC;
            border-radius: 14px;
            padding: 16px 18px;
            margin-bottom: 1rem;
        }

        .info-card p {
            margin: 0.2rem 0;
            color: #334E68;
            font-size: 0.95rem;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1E3A5F;
            margin-top: 1.5rem;
            margin-bottom: 0.7rem;
        }

        .required-label {
            color: #B42318;
            font-weight: 700;
        }

        .ok-box {
            background-color: #E3FCEF;
            border: 1px solid #B7E4C7;
            color: #127C56;
            border-radius: 12px;
            padding: 12px 14px;
            margin-top: 10px;
        }

        .warning-box {
            background-color: #FFF4E5;
            border: 1px solid #F3D19C;
            color: #9A6700;
            border-radius: 12px;
            padding: 12px 14px;
            margin-top: 10px;
        }

        .footer-text {
            text-align: center;
            color: #7B8794;
            font-size: 0.85rem;
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# CARGA DE DATOS
# =========================================================
@st.cache_data
def cargar_datos_vehiculos() -> pd.DataFrame:
    """
    Carga el archivo Excel de vehículos.
    El archivo debe estar en la raíz del repositorio:
    CONCENTRADO REGION CENTRO 1.xlsx
    """

    if not os.path.exists(EXCEL_FILE):
        st.error(
            f"No se encontró el archivo: {EXCEL_FILE}. "
            "Verifica que esté en la raíz del repositorio."
        )
        st.stop()

    df = pd.read_excel(EXCEL_FILE, engine="openpyxl")

    # Normalizar nombres de columnas
    df.columns = [str(col).strip().upper() for col in df.columns]

    posibles_columnas = {
        "REGION": "Region",
        "OFICINA": "Oficina",
        "OFICINA ": "Oficina",
        "PLACA": "Placa",
        "MODELO": "Modelo",
        "REPONSABLE ACTUAL": "Responsable",
        "RESPONSABLE ACTUAL": "Responsable",
        "PUESTO": "Puesto",
    }

    df = df.rename(columns=posibles_columnas)

    columnas_necesarias = [
        "Region",
        "Oficina",
        "Placa",
        "Modelo",
        "Responsable",
        "Puesto",
    ]

    columnas_faltantes = [
        col for col in columnas_necesarias if col not in df.columns
    ]

    if columnas_faltantes:
        st.error(
            "El archivo Excel no contiene las columnas necesarias: "
            + ", ".join(columnas_faltantes)
        )
        st.stop()

    df = df[columnas_necesarias].copy()

    for col in columnas_necesarias:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df = df[df["Placa"] != ""]

    if df.empty:
        st.error("El archivo Excel no contiene placas válidas.")
        st.stop()

    return df


# =========================================================
# UTILIDADES DE PDF
# =========================================================
def dibujar_encabezado_pdf(c: canvas.Canvas, titulo: str) -> int:
    """
    Dibuja encabezado del PDF y devuelve la posición Y siguiente.
    """

    y = 750

    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(PDF_MARGIN_LEFT, y, titulo)

    y -= 18

    c.setFillColor(colors.HexColor("#5B6573"))
    c.setFont("Helvetica", 9)
    c.drawString(
        PDF_MARGIN_LEFT,
        y,
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )

    y -= 20

    c.setStrokeColor(colors.HexColor("#D9E2EC"))
    c.line(PDF_MARGIN_LEFT, y, PDF_PAGE_WIDTH - PDF_MARGIN_RIGHT, y)

    y -= 25

    return y


def nueva_pagina_si_necesaria(c: canvas.Canvas, y: int, espacio_requerido: int = 120) -> int:
    """
    Si no hay espacio suficiente, crea nueva página.
    """

    if y < espacio_requerido:
        c.showPage()
        y = dibujar_encabezado_pdf(c, "REPORTE VEHICULAR - CONTINUACIÓN")

    return y


def escribir_linea_pdf(c: canvas.Canvas, etiqueta: str, valor: str, y: int) -> int:
    """
    Escribe una línea etiqueta/valor en PDF.
    """

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, f"{etiqueta}:")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(PDF_MARGIN_LEFT + 110, y, str(valor))

    return y - 16


def guardar_imagen_temporal(uploaded_file) -> str:
    """
    Guarda una imagen subida por Streamlit en archivo temporal.
    Convierte a RGB para evitar errores con PNG transparentes.
    """

    image = Image.open(uploaded_file)

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    image.save(temp_img.name, format="JPEG", quality=85)

    return temp_img.name


def dibujar_imagen_en_pdf(
    c: canvas.Canvas,
    titulo: str,
    image_path: str,
    y: int,
    ancho_max: int = 240,
    alto_max: int = 160
) -> int:
    """
    Inserta imagen en PDF manteniendo proporción.
    """

    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=230)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, titulo)

    y -= 10

    try:
        image_reader = ImageReader(image_path)
        img_width, img_height = image_reader.getSize()

        ratio = min(ancho_max / img_width, alto_max / img_height)
        draw_width = img_width * ratio
        draw_height = img_height * ratio

        y -= draw_height + 8

        c.drawImage(
            image_reader,
            PDF_MARGIN_LEFT,
            y,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto"
        )

        y -= 20

    except Exception as error:
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.red)
        c.drawString(
            PDF_MARGIN_LEFT,
            y - 20,
            f"No se pudo insertar la imagen: {error}"
        )
        y -= 45

    return y


def crear_pdf_reporte(
    datos_auto: pd.Series,
    placa: str,
    kilometraje: str,
    nivel_combustible: str,
    estado_general: str,
    observaciones: str,
    imagenes: dict,
    usuario_reporta: str,
) -> str:
    """
    Crea el PDF del reporte vehicular.
    """

    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = temp_pdf.name
    temp_pdf.close()

    c = canvas.Canvas(pdf_path, pagesize=letter)

    y = dibujar_encabezado_pdf(c, "REPORTE VEHICULAR")

    # Datos del vehículo
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, "Datos del vehículo")
    y -= 22

    y = escribir_linea_pdf(c, "Región", datos_auto["Region"], y)
    y = escribir_linea_pdf(c, "Oficina", datos_auto["Oficina"], y)
    y = escribir_linea_pdf(c, "Placa", placa, y)
    y = escribir_linea_pdf(c, "Modelo", datos_auto["Modelo"], y)
    y = escribir_linea_pdf(c, "Responsable", datos_auto["Responsable"], y)
    y = escribir_linea_pdf(c, "Puesto", datos_auto["Puesto"], y)
    y = escribir_linea_pdf(c, "Kilometraje", kilometraje, y)
    y = escribir_linea_pdf(c, "Nivel combustible", nivel_combustible, y)
    y = escribir_linea_pdf(c, "Estado general", estado_general, y)
    y = escribir_linea_pdf(c, "Usuario reporta", usuario_reporta, y)

    y -= 10

    # Observaciones
    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=120)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, "Observaciones")
    y -= 18

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    if observaciones.strip():
        texto = observaciones.strip()
    else:
        texto = "Sin observaciones."

    lineas = dividir_texto(texto, max_chars=90)

    for linea in lineas:
        y = nueva_pagina_si_necesaria(c, y, espacio_requerido=80)
        c.drawString(PDF_MARGIN_LEFT, y, linea)
        y -= 14

    y -= 15

    # Evidencias
    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=180)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, "Evidencias fotográficas")
    y -= 25

    hay_imagenes = False

    for nombre_seccion, uploaded_file in imagenes.items():
        if uploaded_file is not None:
            hay_imagenes = True
            image_path = guardar_imagen_temporal(uploaded_file)
            y = dibujar_imagen_en_pdf(c, nombre_seccion, image_path, y)

    if not hay_imagenes:
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(PDF_MARGIN_LEFT, y, "No se adjuntaron evidencias fotográficas.")
        y -= 20

    # Footer final
    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=80)

    c.setStrokeColor(colors.HexColor("#D9E2EC"))
    c.line(PDF_MARGIN_LEFT, y, PDF_PAGE_WIDTH - PDF_MARGIN_RIGHT, y)
    y -= 18

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#7B8794"))
    c.drawString(
        PDF_MARGIN_LEFT,
        y,
        "Sistema Operativo - Grupo Besco | Reporte generado automáticamente"
    )

    c.save()

    return pdf_path


def dividir_texto(texto: str, max_chars: int = 90) -> list:
    """
    Divide texto largo en líneas simples para PDF.
    """

    palabras = texto.split()
    lineas = []
    linea_actual = ""

    for palabra in palabras:
        if len(linea_actual) + len(palabra) + 1 <= max_chars:
            linea_actual += " " + palabra if linea_actual else palabra
        else:
            lineas.append(linea_actual)
            linea_actual = palabra

    if linea_actual:
        lineas.append(linea_actual)

    return lineas


# =========================================================
# ENVÍO DE CORREO
# =========================================================
def enviar_correo_con_pdf(
    pdf_path: str,
    destinatario: str,
    asunto: str,
    cuerpo: str,
    nombre_archivo: str
) -> tuple:
    """
    Envía el PDF por correo usando SMTP.
    Requiere configuración en Streamlit secrets.
    """

    try:
        smtp_host = st.secrets["SMTP_HOST"]
        smtp_port = int(st.secrets["SMTP_PORT"])
        smtp_user = st.secrets["SMTP_USER"]
        smtp_password = st.secrets["SMTP_PASSWORD"]
        smtp_from = st.secrets.get("SMTP_FROM", smtp_user)

        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = smtp_from
        msg["To"] = destinatario
        msg.set_content(cuerpo)

        with open(pdf_path, "rb") as file:
            msg.add_attachment(
                file.read(),
                maintype="application",
                subtype="pdf",
                filename=nombre_archivo
            )

        with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)

        return True, "Correo enviado correctamente."

    except KeyError as error:
        return (
            False,
            f"Falta configurar la variable en st.secrets: {error}. "
            "Configura SMTP_HOST, SMTP_PORT, SMTP_USER y SMTP_PASSWORD."
        )

    except Exception as error:
        return False, f"No se pudo enviar el correo: {error}"


# =========================================================
# HEADER
# =========================================================
def render_header() -> None:
    st.markdown(
        """
        <div class="vehicular-header">
            <div class="vehicular-title">🚗 App de Reporte Vehicular</div>
            <div class="vehicular-subtitle">
                Captura de evidencias, datos del vehículo, generación de PDF y envío de reporte.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    aplicar_estilos()
    render_header()

    col_back, col_space = st.columns([1, 5])

    with col_back:
        st.page_link(
            "portal.py",
            label="⬅️ Volver al portal",
            use_container_width=True
        )

    df = cargar_datos_vehiculos()

    st.markdown('<div class="section-title">1. Selección del vehículo</div>', unsafe_allow_html=True)

    col_filtro_1, col_filtro_2 = st.columns(2)

    with col_filtro_1:
        oficinas = ["Todas"] + sorted(df["Oficina"].dropna().unique().tolist())
        oficina_seleccionada = st.selectbox(
            "Filtrar por oficina",
            oficinas
        )

    df_filtrado = df.copy()

    if oficina_seleccionada != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Oficina"] == oficina_seleccionada]

    with col_filtro_2:
        placas = sorted(df_filtrado["Placa"].dropna().unique().tolist())

        if not placas:
            st.warning("No hay placas disponibles para la oficina seleccionada.")
            st.stop()

        placa_seleccionada = st.selectbox(
            "Selecciona la placa",
            placas
        )

    datos_auto = df[df["Placa"] == placa_seleccionada].iloc[0]

    st.markdown('<div class="info-card">', unsafe_allow_html=True)

    col_info_1, col_info_2, col_info_3 = st.columns(3)

    with col_info_1:
        st.markdown(f"**Región:** {datos_auto['Region']}")
        st.markdown(f"**Oficina:** {datos_auto['Oficina']}")

    with col_info_2:
        st.markdown(f"**Placa:** {datos_auto['Placa']}")
        st.markdown(f"**Modelo:** {datos_auto['Modelo']}")

    with col_info_3:
        st.markdown(f"**Responsable:** {datos_auto['Responsable']}")
        st.markdown(f"**Puesto:** {datos_auto['Puesto']}")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">2. Datos del reporte</div>', unsafe_allow_html=True)

    col_datos_1, col_datos_2, col_datos_3 = st.columns(3)

    with col_datos_1:
        kilometraje = st.text_input(
            "Kilometraje del tablero",
            placeholder="Ejemplo: 45,230"
        )

    with col_datos_2:
        nivel_combustible = st.selectbox(
            "Nivel de combustible",
            [
                "No especificado",
                "Vacío",
                "1/4",
                "1/2",
                "3/4",
                "Lleno",
            ]
        )

    with col_datos_3:
        estado_general = st.selectbox(
            "Estado general del vehículo",
            [
                "Bueno",
                "Regular",
                "Malo",
                "Requiere revisión",
            ]
        )

    usuario_reporta = st.text_input(
        "Nombre de quien realiza el reporte",
        placeholder="Captura el nombre del usuario que reporta"
    )

    st.markdown('<div class="section-title">3. Evidencias fotográficas</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="warning-box">
            Los campos marcados como obligatorios son recomendados para generar un reporte completo.
            Las secciones opcionales pueden dejarse vacías.
        </div>
        """,
        unsafe_allow_html=True
    )

    secciones_obligatorias = [
        "Frente",
        "Atrás",
        "Costado izquierdo",
        "Costado derecho",
        "Tablero para kilometraje",
        "Asientos delanteros",
        "Herramienta",
        "Llanta de refacción",
        "Tarjeta de circulación",
        "Póliza de seguro",
    ]

    secciones_opcionales = [
        "Asientos traseros",
    ]

    imagenes = {}

    st.markdown("#### Evidencias obligatorias")

    for i in range(0, len(secciones_obligatorias), 2):
        col_img_1, col_img_2 = st.columns(2)

        with col_img_1:
            seccion = secciones_obligatorias[i]
            imagenes[seccion] = st.file_uploader(
                f"{seccion} *",
                type=["jpg", "jpeg", "png"],
                key=f"img_{seccion}"
            )

        if i + 1 < len(secciones_obligatorias):
            with col_img_2:
                seccion = secciones_obligatorias[i + 1]
                imagenes[seccion] = st.file_uploader(
                    f"{seccion} *",
                    type=["jpg", "jpeg", "png"],
                    key=f"img_{seccion}"
                )

    st.markdown("#### Evidencias opcionales")

    for seccion in secciones_opcionales:
        imagenes[seccion] = st.file_uploader(
            f"{seccion} opcional",
            type=["jpg", "jpeg", "png"],
            key=f"img_{seccion}"
        )

    st.markdown('<div class="section-title">4. Observaciones</div>', unsafe_allow_html=True)

    observaciones = st.text_area(
        "Observaciones opcionales",
        placeholder="Captura aquí cualquier comentario adicional sobre el estado del vehículo.",
        height=120
    )

    st.markdown('<div class="section-title">5. Generar reporte</div>', unsafe_allow_html=True)

    faltantes = []

    if not kilometraje.strip():
        faltantes.append("Kilometraje")

    if not usuario_reporta.strip():
        faltantes.append("Nombre de quien realiza el reporte")

    for seccion in secciones_obligatorias:
        if imagenes.get(seccion) is None:
            faltantes.append(seccion)

    if faltantes:
        st.markdown(
            f"""
            <div class="warning-box">
                Faltan datos/evidencias recomendadas: {", ".join(faltantes)}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="ok-box">
                Todo listo para generar el PDF del reporte vehicular.
            </div>
            """,
            unsafe_allow_html=True
        )

    permitir_generar_incompleto = st.checkbox(
        "Permitir generar PDF aunque falten evidencias/datos",
        value=True
    )

    puede_generar = permitir_generar_incompleto or not faltantes

    col_pdf_1, col_pdf_2 = st.columns([1, 1])

    with col_pdf_1:
        generar = st.button(
            "📄 Generar PDF",
            use_container_width=True,
            disabled=not puede_generar
        )

    if generar:
        with st.spinner("Generando reporte PDF..."):
            pdf_path = crear_pdf_reporte(
                datos_auto=datos_auto,
                placa=placa_seleccionada,
                kilometraje=kilometraje,
                nivel_combustible=nivel_combustible,
                estado_general=estado_general,
                observaciones=observaciones,
                imagenes=imagenes,
                usuario_reporta=usuario_reporta,
            )

        nombre_pdf = f"Reporte_Vehicular_{placa_seleccionada}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        st.session_state["pdf_path_vehicular"] = pdf_path
        st.session_state["nombre_pdf_vehicular"] = nombre_pdf

        st.success("PDF generado correctamente.")

    if "pdf_path_vehicular" in st.session_state:
        pdf_path = st.session_state["pdf_path_vehicular"]
        nombre_pdf = st.session_state["nombre_pdf_vehicular"]

        with open(pdf_path, "rb") as file:
            st.download_button(
                "⬇️ Descargar PDF",
                data=file,
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown('<div class="section-title">6. Enviar por correo</div>', unsafe_allow_html=True)

        with st.expander("📧 Envío por correo", expanded=False):
            destinatario = st.text_input(
                "Correo destinatario",
                placeholder="ejemplo@empresa.com"
            )

            asunto = st.text_input(
                "Asunto",
                value=f"Reporte vehicular - {placa_seleccionada}"
            )

            cuerpo = st.text_area(
                "Mensaje",
                value=(
                    "Buen día,\n\n"
                    "Se adjunta el reporte vehicular generado desde el Portal de Soluciones Operativas.\n\n"
                    f"Placa: {placa_seleccionada}\n"
                    f"Oficina: {datos_auto['Oficina']}\n"
                    f"Modelo: {datos_auto['Modelo']}\n\n"
                    "Saludos."
                ),
                height=150
            )

            if st.button("📨 Enviar correo", use_container_width=True):
                if not destinatario.strip():
                    st.warning("Captura un correo destinatario.")
                else:
                    enviado, mensaje = enviar_correo_con_pdf(
                        pdf_path=pdf_path,
                        destinatario=destinatario,
                        asunto=asunto,
                        cuerpo=cuerpo,
                        nombre_archivo=nombre_pdf
                    )

                    if enviado:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)

    st.divider()

    st.markdown(
        """
        <div class="footer-text">
            Sistema Operativo - Grupo Besco | App Vehicular
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
