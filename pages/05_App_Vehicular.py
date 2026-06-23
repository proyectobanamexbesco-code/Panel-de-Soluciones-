import streamlit as st
import pandas as pd
import tempfile JIMENEZ CLAUDIA IVETTE",import tempfile
        "Puesto": "GERENTE DE SERVICIOS",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RCN688D",
        "Modelo": "KWID",
        "Responsable": "GOMEZ SANCHEZ DANTE",
        "Puesto": "SUPERVISOR",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RCN939D",
        "Modelo": "KWID",
        "Responsable": "OROPEZA OLGUIN JUAN CARLOS",
        "Puesto": "SUPERVISOR",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RDD843D",
        "Modelo": "KWID",
        "Responsable": "MAYAGOITIA ANDRES ARTURO",
        "Puesto": "SUPERVISOR",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "A60BPC",
        "Modelo": "TORNADO",
        "Responsable": "TECATE QUIÑONES FRANCISCO MANUEL",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "C20BRE",
        "Modelo": "KANGOO",
        "Responsable": "LOPEZ GONZALEZ MOISES",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "PAZ868C",
        "Modelo": "KANGOO",
        "Responsable": "MORENO ORIHUELA HERIBERTO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "D27BPX",
        "Modelo": "KWID",
        "Responsable": "RENDON VARGAS JOSE MANUEL",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RDD779D",
        "Modelo": "KWID",
        "Responsable": "DE LABRA GARCIA ROMAN (PRESTAMO)",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RDD838D",
        "Modelo": "KWID",
        "Responsable": "FLORES PALMA JUAN FERNANDO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "U68BPB",
        "Modelo": "TORNADO",
        "Responsable": "SALVADOR OJEDA HERNANDEZ",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "V42BPB",
        "Modelo": "TORNADO",
        "Responsable": "TALLER",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "C98BRE",
        "Modelo": "KWID",
        "Responsable": "RAMOS LOPEZ RODOLFO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "MORELIA",
        "Placa": "C79BRE",
        "Modelo": "KWID",
        "Responsable": "SIN RESPONSIVA",
        "Puesto": "SIN RESPONSIVA",
    },
    {
        "Region": "CENTRO",
        "Oficina": "MORELIA",
        "Placa": "B45BLR",
        "Modelo": "KWID",
        "Responsable": "ZAMANO FARIAS JAVIER",
        "Puesto": "SUPERVISOR",
    },
    {
        "Region": "CENTRO",
        "Oficina": "MORELIA",
        "Placa": "C09BRE",
        "Modelo": "KWID",
        "Responsable": "AVALOS AYALA VICTOR HUGO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "MORELIA",
        "Placa": "C16BRE",
        "Modelo": "KANGOO",
        "Responsable": "RUEDA LOPEZ OSCAR VINICIO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "MORELIA (URUAPAN)",
        "Placa": "C53BRE",
        "Modelo": "KWID",
        "Responsable": "MARTIN GARIBAY ROMERO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "MORELIA (ZAMORA)",
        "Placa": "F47BPX",
        "Modelo": "KANGOO",
        "Responsable": "PEREZ GARCIA JUAN GERARDO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "PACHUCA",
        "Placa": "RCN938D",
        "Modelo": "KWID",
        "Responsable": "SIN RESPONSIVA",
        "Puesto": "SIN RESPONSIVA",
    },
    {
        "Region": "CENTRO",
        "Oficina": "PACHUCA",
        "Placa": "C92BRE",
        "Modelo": "KANGOO",
        "Responsable": "ROJAS PEREZ GUILLERMO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "TOLUCA",
        "Placa": "RCN698D",
        "Modelo": "KWID",
        "Responsable": "POLICARPIO ROSALINO FRANCISCO",
        "Puesto": "JEFE DE OFICINA",
    },
    {
        "Region": "CENTRO",
        "Oficina": "TOLUCA",
        "Placa": "NZ8860A",
        "Modelo": "TORNADO",
        "Responsable": "SANCHEZ DESALES EDUARDO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "TOLUCA",
        "Placa": "NZ8862A",
        "Modelo": "TORNADO",
        "Responsable": "GARCIA VERA CRUZ MARTIN",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "TOLUCA",
        "Placa": "RCN684D",
        "Modelo": "KWID",
        "Responsable": "TOLENTINO MUNGUIA OSCAR",
        "Puesto": "TECNICO",
    },
]


# =========================================================
# SECCIONES DE EVIDENCIA
# =========================================================
EVIDENCIAS_CRITICAS = [
    "Frente",
    "Atrás",
    "Tablero para kilometraje",
    "Tarjeta de circulación",
    "Póliza de seguro",
]

EVIDENCIAS_RECOMENDADAS = [
    "Costado izquierdo",
    "Costado derecho",
    "Asientos delanteros",
    "Herramienta",
    "Llanta de refacción",
]

EVIDENCIAS_OPCIONALES = [
    "Asientos traseros",
]


# =========================================================
# ESTILOS LIGEROS
# =========================================================
def aplicar_estilos_ligeros() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            max-width: 780px;
        }

        .main-title {
            text-align: center;
            color: #1E3A5F;
            font-size: 1.7rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            text-align: center;
            color: #5B6573;
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }

        .info-box {
            background-color: #F7F9FC;
            border: 1px solid #D9E2EC;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 1rem;
            color: #334E68;
            font-size: 0.9rem;
        }

        .warning-box {
            background-color: #FFF4E5;
            border: 1px solid #F3D19C;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            color: #9A6700;
            font-size: 0.9rem;
        }

        .ok-box {
            background-color: #E3FCEF;
            border: 1px solid #B7E4C7;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            color: #127C56;
            font-size: 0.9rem;
        }

        .section-title {
            font-size: 1.1rem;
            font-weight: 800;
            color: #1E3A5F;
            margin-top: 1.2rem;
            margin-bottom: 0.5rem;
        }

        .footer-text {
            text-align: center;
            color: #7B8794;
            font-size: 0.8rem;
            padding-top: 1rem;
        }

        button {
            border-radius: 10px !important;
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
    df = pd.DataFrame(VEHICULOS_DATA)

    columnas = [
        "Region",
        "Oficina",
        "Placa",
        "Modelo",
        "Responsable",
        "Puesto",
    ]

    for columna in columnas:
        df[columna] = df[columna].fillna("").astype(str).str.strip()

    df = df[df["Placa"] != ""].copy()

    return df


# =========================================================
# UTILIDADES DE IMAGEN
# =========================================================
def comprimir_imagen_a_temp(uploaded_file) -> str:
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    else:
        image = image.convert("RGB")

    image.thumbnail(MAX_IMAGE_SIZE)

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_img.close()

    image.save(
        temp_img.name,
        format="JPEG",
        quality=IMAGE_QUALITY,
        optimize=True
    )

    return temp_img.name


def obtener_imagen_desde_session(key_base: str):
    key_subir = f"{key_base}_subir"
    key_camara = f"{key_base}_camara"

    if key_subir in st.session_state and st.session_state[key_subir] is not None:
        return st.session_state[key_subir]

    if key_camara in st.session_state and st.session_state[key_camara] is not None:
        return st.session_state[key_camara]

    return None


def render_captura_evidencia(nombre: str, obligatorio: bool = False) -> None:
    key_base = nombre.lower()
    key_base = key_base.replace(" ", "_")
    key_base = key_base.replace("á", "a")
    key_base = key_base.replace("é", "e")
    key_base = key_base.replace("í", "i")
    key_base = key_base.replace("ó", "o")
    key_base = key_base.replace("ú", "u")
    key_base = key_base.replace("ñ", "n")

    etiqueta = f"{nombre}"
    if obligatorio:
        etiqueta = f"{nombre} *"

    modo = st.radio(
        f"Método para {etiqueta}",
        ["Subir archivo", "Cámara"],
        horizontal=True,
        key=f"modo_{key_base}"
    )

    if modo == "Subir archivo":
        st.file_uploader(
            etiqueta,
            type=["jpg", "jpeg", "png"],
            key=f"{key_base}_subir"
        )
    else:
        st.camera_input(
            etiqueta,
            key=f"{key_base}_camara"
        )

    imagen = obtener_imagen_desde_session(key_base)

    if imagen is not None:
        st.success(f"{nombre}: imagen cargada.")
    else:
        st.caption(f"{nombre}: pendiente.")


def obtener_todas_las_imagenes() -> dict:
    imagenes = {}

    todas = EVIDENCIAS_CRITICAS + EVIDENCIAS_RECOMENDADAS + EVIDENCIAS_OPCIONALES

    for nombre in todas:
        key_base = nombre.lower()
        key_base = key_base.replace(" ", "_")
        key_base = key_base.replace("á", "a")
        key_base = key_base.replace("é", "e")
        key_base = key_base.replace("í", "i")
        key_base = key_base.replace("ó", "o")
        key_base = key_base.replace("ú", "u")
        key_base = key_base.replace("ñ", "n")

        imagenes[nombre] = obtener_imagen_desde_session(key_base)

    return imagenes


# =========================================================
# UTILIDADES PDF
# =========================================================
def limpiar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        texto = str(texto)

    reemplazos = {
        "•": "-",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u200b": "",
        "\r": "",
        "°": " grados",
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    return texto


def dividir_texto(texto: str, max_chars: int = 90) -> list:
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


def dibujar_encabezado_pdf(c: canvas.Canvas, titulo: str) -> int:
    y = 750

    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(PDF_MARGIN_LEFT, y, limpiar_texto(titulo))

    y -= 18

    c.setFillColor(colors.HexColor("#5B6573"))
    c.setFont("Helvetica", 9)
    c.drawString(
        PDF_MARGIN_LEFT,
        y,
        limpiar_texto(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    )

    y -= 20

    c.setStrokeColor(colors.HexColor("#D9E2EC"))
    c.line(PDF_MARGIN_LEFT, y, PDF_PAGE_WIDTH - PDF_MARGIN_RIGHT, y)

    y -= 25

    return y


def nueva_pagina_si_necesaria(
    c: canvas.Canvas,
    y: int,
    espacio_requerido: int = 120
) -> int:
    if y < espacio_requerido:
        c.showPage()
        y = dibujar_encabezado_pdf(c, "REPORTE VEHICULAR - CONTINUACIÓN")

    return y


def escribir_linea_pdf(
    c: canvas.Canvas,
    etiqueta: str,
    valor: str,
    y: int
) -> int:
    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=70)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, limpiar_texto(f"{etiqueta}:"))

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    c.drawString(PDF_MARGIN_LEFT + 120, y, limpiar_texto(str(valor)))

    return y - 16


def dibujar_imagen_en_pdf(
    c: canvas.Canvas,
    titulo: str,
    uploaded_file,
    y: int,
    ancho_max: int = 250,
    alto_max: int = 165
) -> int:
    if uploaded_file is None:
        return y

    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=235)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, limpiar_texto(titulo))

    y -= 10

    temp_path = None

    try:
        temp_path = comprimir_imagen_a_temp(uploaded_file)

        image_reader = ImageReader(temp_path)
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

        y -= 18

    except Exception as error:
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.red)
        c.drawString(
            PDF_MARGIN_LEFT,
            y - 20,
            limpiar_texto(f"No se pudo insertar la imagen: {error}")
        )
        y -= 45

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

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
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = temp_pdf.name
    temp_pdf.close()

    c = canvas.Canvas(pdf_path, pagesize=letter)

    y = dibujar_encabezado_pdf(c, "REPORTE VEHICULAR")

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
    y = escribir_linea_pdf(c, "Kilometraje", kilometraje if kilometraje else "No capturado", y)
    y = escribir_linea_pdf(c, "Nivel combustible", nivel_combustible, y)
    y = escribir_linea_pdf(c, "Estado general", estado_general, y)
    y = escribir_linea_pdf(c, "Usuario reporta", usuario_reporta if usuario_reporta else "No capturado", y)

    y -= 10

    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=120)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, "Observaciones")
    y -= 18

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)

    texto_observaciones = observaciones.strip() if observaciones.strip() else "Sin observaciones."

    for linea in dividir_texto(texto_observaciones, max_chars=90):
        y = nueva_pagina_si_necesaria(c, y, espacio_requerido=80)
        c.drawString(PDF_MARGIN_LEFT, y, limpiar_texto(linea))
        y -= 14

    y -= 15

    y = nueva_pagina_si_necesaria(c, y, espacio_requerido=180)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(PDF_MARGIN_LEFT, y, "Evidencias fotográficas")
    y -= 25

    hay_imagenes = False

    for nombre_seccion, uploaded_file in imagenes.items():
        if uploaded_file is not None:
            hay_imagenes = True
            y = dibujar_imagen_en_pdf(c, nombre_seccion, uploaded_file, y)

    if not hay_imagenes:
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(PDF_MARGIN_LEFT, y, "No se adjuntaron evidencias fotográficas.")
        y -= 20

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

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                smtp.starttls()
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)

        return True, "Correo enviado correctamente."

    except KeyError as error:
        return (
            False,
            f"Falta configurar la variable en st.secrets: {error}. "
            "Configura SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_FROM."
        )

    except Exception as error:
        return False, f"No se pudo enviar el correo: {error}"


# =========================================================
# VALIDACIONES
# =========================================================
def validar_reporte(kilometraje: str, usuario_reporta: str, imagenes: dict) -> list:
    faltantes = []

    if not kilometraje.strip():
        faltantes.append("Kilometraje")

    if not usuario_reporta.strip():
        faltantes.append("Nombre de quien realiza el reporte")

    for evidencia in EVIDENCIAS_CRITICAS:
        if imagenes.get(evidencia) is None:
            faltantes.append(evidencia)

    return faltantes


def limpiar_nombre_archivo(nombre: str) -> str:
    invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")"]

    limpio = nombre

    for caracter in invalidos:
        limpio = limpio.replace(caracter, "_")

    limpio = limpio.replace(" ", "_")

    return limpio


# =========================================================
# INTERFAZ PRINCIPAL
# =========================================================
def main() -> None:
    aplicar_estilos_ligeros()

    st.markdown(
        """
        <div class="main-title">🚗 App Vehicular</div>
        <div class="subtitle">
            Versión ligera para Android: captura evidencias, genera PDF y envía correo opcionalmente.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.page_link(
        "portal.py",
        label="⬅️ Volver al portal",
        use_container_width=True
    )

    st.markdown(
        """
        <div class="info-box">
            Recomendación para celular: captura solo las evidencias necesarias.
            Las fotos se comprimen automáticamente para que el PDF sea más ligero.
        </div>
        """,
        unsafe_allow_html=True
    )

    df = cargar_datos_vehiculos()

    paso = st.radio(
        "Sección",
        [
            "1. Vehículo",
            "2. Datos",
            "3. Evidencias críticas",
            "4. Evidencias recomendadas",
            "5. Observaciones y PDF",
        ],
        horizontal=False
    )

    if "vehicular_form" not in st.session_state:
        st.session_state["vehicular_form"] = {}

    form_state = st.session_state["vehicular_form"]

    if paso == "1. Vehículo":
        st.markdown(
            '<div class="section-title">1. Selección del vehículo</div>',
            unsafe_allow_html=True
        )

        oficinas = ["Todas"] + sorted(df["Oficina"].dropna().unique().tolist())

        oficina_seleccionada = st.selectbox(
            "Filtrar por oficina",
            oficinas,
            key="vehicular_oficina_filtro"
        )

        df_filtrado = df.copy()

        if oficina_seleccionada != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Oficina"] == oficina_seleccionada]

        placas = sorted(df_filtrado["Placa"].dropna().unique().tolist())

        if not placas:
            st.warning("No hay placas disponibles para la oficina seleccionada.")
            st.stop()

        placa_seleccionada = st.selectbox(
            "Selecciona la placa",
            placas,
            key="vehicular_placa"
        )

        datos_auto = df[df["Placa"] == placa_seleccionada].iloc[0]

        form_state["placa"] = placa_seleccionada

        st.markdown(
            f"""
            <div class="info-box">
                <strong>Región:</strong> {datos_auto["Region"]}<br>
                <strong>Oficina:</strong> {datos_auto["Oficina"]}<br>
                <strong>Placa:</strong> {datos_auto["Placa"]}<br>
                <strong>Modelo:</strong> {datos_auto["Modelo"]}<br>
                <strong>Responsable:</strong> {datos_auto["Responsable"]}<br>
                <strong>Puesto:</strong> {datos_auto["Puesto"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    elif paso == "2. Datos":
        st.markdown(
            '<div class="section-title">2. Datos del reporte</div>',
            unsafe_allow_html=True
        )

        form_state["kilometraje"] = st.text_input(
            "Kilometraje del tablero",
            value=form_state.get("kilometraje", ""),
            placeholder="Ejemplo: 45,230"
        )

        form_state["nivel_combustible"] = st.selectbox(
            "Nivel de combustible",
            [
                "No especificado",
                "Vacío",
                "1/4",
                "1/2",
                "3/4",
                "Lleno",
            ],
            index=[
                "No especificado",
                "Vacío",
                "1/4",
                "1/2",
                "3/4",
                "Lleno",
            ].index(form_state.get("nivel_combustible", "No especificado"))
            if form_state.get("nivel_combustible", "No especificado") in [
                "No especificado",
                "Vacío",
                "1/4",
                "1/2",
                "3/4",
                "Lleno",
            ]
            else 0
        )

        form_state["estado_general"] = st.selectbox(
            "Estado general del vehículo",
            [
                "Bueno",
                "Regular",
                "Malo",
                "Requiere revisión",
            ],
            index=[
                "Bueno",
                "Regular",
                "Malo",
                "Requiere revisión",
            ].index(form_state.get("estado_general", "Bueno"))
            if form_state.get("estado_general", "Bueno") in [
                "Bueno",
                "Regular",
                "Malo",
                "Requiere revisión",
            ]
            else 0
        )

        form_state["usuario_reporta"] = st.text_input(
            "Nombre de quien realiza el reporte",
            value=form_state.get("usuario_reporta", ""),
            placeholder="Nombre del usuario que reporta"
        )

        st.success("Datos guardados temporalmente en la sesión.")

    elif paso == "3. Evidencias críticas":
        st.markdown(
            '<div class="section-title">3. Evidencias críticas</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="warning-box">
                Estas evidencias son las más importantes para cerrar el reporte desde celular.
                No se muestran previsualizaciones para mantener ligera la app.
            </div>
            """,
            unsafe_allow_html=True
        )

        for evidencia in EVIDENCIAS_CRITICAS:
            render_captura_evidencia(evidencia, obligatorio=True)
            st.divider()

    elif paso == "4. Evidencias recomendadas":
        st.markdown(
            '<div class="section-title">4. Evidencias recomendadas y opcionales</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="info-box">
                Estas evidencias ayudan a documentar mejor el estado del vehículo,
                pero no bloquean la generación del PDF si se genera como reporte incompleto.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### Recomendadas")
        for evidencia in EVIDENCIAS_RECOMENDADAS:
            render_captura_evidencia(evidencia, obligatorio=False)
            st.divider()

        st.markdown("### Opcionales")
        for evidencia in EVIDENCIAS_OPCIONALES:
            render_captura_evidencia(evidencia, obligatorio=False)
            st.divider()

    elif paso == "5. Observaciones y PDF":
        st.markdown(
            '<div class="section-title">5. Observaciones y generación de PDF</div>',
            unsafe_allow_html=True
        )

        form_state["observaciones"] = st.text_area(
            "Observaciones opcionales",
            value=form_state.get("observaciones", ""),
            placeholder="Captura aquí cualquier comentario adicional.",
            height=120
        )

        placa_actual = form_state.get("placa")

        if not placa_actual:
            st.warning("Primero selecciona un vehículo en la sección 1.")
            st.stop()

        datos_auto = df[df["Placa"] == placa_actual].iloc[0]

        imagenes = obtener_todas_las_imagenes()

        kilometraje = form_state.get("kilometraje", "")
        nivel_combustible = form_state.get("nivel_combustible", "No especificado")
        estado_general = form_state.get("estado_general", "Bueno")
        usuario_reporta = form_state.get("usuario_reporta", "")
        observaciones = form_state.get("observaciones", "")

        faltantes = validar_reporte(
            kilometraje=kilometraje,
            usuario_reporta=usuario_reporta,
            imagenes=imagenes
        )

        if faltantes:
            st.markdown(
                f"""
                <div class="warning-box">
                    Faltan datos o evidencias críticas: {", ".join(faltantes)}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="ok-box">
                    Datos críticos completos. Puedes generar el PDF.
                </div>
                """,
                unsafe_allow_html=True
            )

        permitir_incompleto = st.checkbox(
            "Permitir generar PDF aunque falten datos/evidencias críticas",
            value=True
        )

        puede_generar = permitir_incompleto or not faltantes

        generar_pdf = st.button(
            "📄 Generar PDF",
            type="primary",
            use_container_width=True,
            disabled=not puede_generar
        )

        if generar_pdf:
            with st.spinner("Generando PDF y comprimiendo imágenes..."):
                try:
                    pdf_path = crear_pdf_reporte(
                        datos_auto=datos_auto,
                        placa=placa_actual,
                        kilometraje=kilometraje,
                        nivel_combustible=nivel_combustible,
                        estado_general=estado_general,
                        observaciones=observaciones,
                        imagenes=imagenes,
                        usuario_reporta=usuario_reporta,
                    )

                    nombre_pdf = limpiar_nombre_archivo(
                        f"Reporte_Vehicular_{placa_actual}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    )

                    st.session_state["vehicular_pdf_path"] = pdf_path
                    st.session_state["vehicular_nombre_pdf"] = nombre_pdf
                    st.session_state["vehicular_pdf_placa"] = placa_actual
                    st.session_state["vehicular_pdf_oficina"] = datos_auto["Oficina"]
                    st.session_state["vehicular_pdf_modelo"] = datos_auto["Modelo"]

                    st.success("PDF generado correctamente.")

                except Exception as error:
                    st.error(f"No se pudo generar el PDF: {error}")

        if "vehicular_pdf_path" in st.session_state:
            pdf_path = st.session_state["vehicular_pdf_path"]
            nombre_pdf = st.session_state["vehicular_nombre_pdf"]

            with open(pdf_path, "rb") as file:
                st.download_button(
                    "⬇️ Descargar PDF",
                    data=file,
                    file_name=nombre_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )

            st.markdown(
                '<div class="section-title">Enviar por correo</div>',
                unsafe_allow_html=True
            )

            st.markdown(
                """
                <div class="info-box">
                    El PDF ya fue generado. Si tienes buena conexión, puedes enviarlo por correo.
                    Si falla el envío, descarga el PDF y compártelo de forma manual.
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.expander("📧 Configurar envío", expanded=False):
                destinatario = st.text_input(
                    "Correo destinatario",
                    placeholder="ejemplo@empresa.com"
                )

                asunto = st.text_input(
                    "Asunto",
                    value=f"Reporte vehicular - {st.session_state.get('vehicular_pdf_placa', '')}"
                )

                cuerpo = st.text_area(
                    "Mensaje",
                    value=(
                        "Buen día,\n\n"
                        "Se adjunta el reporte vehicular generado desde el Portal de Soluciones Operativas.\n\n"
                        f"Placa: {st.session_state.get('vehicular_pdf_placa', '')}\n"
                        f"Oficina: {st.session_state.get('vehicular_pdf_oficina', '')}\n"
                        f"Modelo: {st.session_state.get('vehicular_pdf_modelo', '')}\n\n"
                        "Saludos."
                    ),
                    height=150
                )

                enviar = st.button(
                    "📨 Enviar correo",
                    use_container_width=True
                )

                if enviar:
                    if not destinatario.strip():
                        st.warning("Captura un correo destinatario.")
                    else:
                        with st.spinner("Enviando correo..."):
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
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "App Vehicular"
PAGE_ICON = "🚗"
LAYOUT = "centered"

PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT = letter
PDF_MARGIN_LEFT = 45
PDF_MARGIN_RIGHT = 45

MAX_IMAGE_SIZE = (900, 900)
IMAGE_QUALITY = 60


# =========================================================
# CONFIGURAR PÁGINA
# =========================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)


# =========================================================
# BASE DE DATOS INTEGRADA DE VEHÍCULOS
# =========================================================
VEHICULOS_DATA = [
    {
        "Region": "CENTRO",
        "Oficina": "ACAPULCO",
        "Placa": "C58BRE",
        "Modelo": "KWID",
        "Responsable": "TALLER",
        "Puesto": "INACTIVO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "ACAPULCO",
        "Placa": "B98BLR",
        "Modelo": "KANGOO",
        "Responsable": "IBARRA BUENAVENTURA LUIS ALBERTO",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "ACAPULCO",
        "Placa": "F56BPX",
        "Modelo": "KWID",
        "Responsable": "CINTORA AVALOS FRANCISCO JAVIER",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "ACAPULCO",
        "Placa": "D89BPX (CHILPANCINGO)",
        "Modelo": "KWID",
        "Responsable": "LOPEZ MARCIAL JULIO CESAR",
        "Puesto": "TECNICO",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "F52AJM",
        "Modelo": "GRAND-I-10",
        "Responsable": "RAMIREZ GARCIA RICARDO ALEJANDRO",
        "Puesto": "GERENTE DE SERVICIOS",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RCN697D",
        "Modelo": "KWID",
        "Responsable": "MANZO RAMIREZ CHRISTIAN",
        "Puesto": "GERENTE DE SERVICIOS",
    },
    {
        "Region": "CENTRO",
        "Oficina": "CDMX",
        "Placa": "RDD750D",
        "Modelo": "KWID",
