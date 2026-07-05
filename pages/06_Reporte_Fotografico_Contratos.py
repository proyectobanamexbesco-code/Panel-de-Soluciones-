import os
import tempfile
import smtplib
from datetime import datetime
from email.message import EmailMessage

import streamlit as st
import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# =========================================================
# CONFIGURACION GENERAL
# =========================================================
PAGE_TITLE = "Reporte Fotografico por Contrato"
PAGE_ICON = "📷"
LAYOUT = "centered"

PDF_WIDTH, PDF_HEIGHT = letter
MARGIN_LEFT = 45
MARGIN_RIGHT = 45

MAX_IMAGE_SIZE = (1000, 1000)
IMAGE_QUALITY = 65
MAX_FOTOS_POR_SECCION = 6


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)


# =========================================================
# CONTRATOS
# =========================================================
CONTRATOS_CONFIG = {
    "Santander": {
        "destinatarios": ["gerardo.mendez@besco.mx"],
        "tipos_servicio": [
            "Preventivo",
            "Correctivo",
            "Emergencia",
            "Visita tecnica",
            "Levantamiento",
        ],
        "estatus": [
            "Servicio concluido",
            "Servicio concluido con observaciones",
            "Pendiente por material",
            "Pendiente por autorizacion",
            "No concluido",
        ],
    },
    "MacStore": {
        "destinatarios": ["gerardo.mendez@besco.mx"],
        "tipos_servicio": [
            "Preventivo",
            "Correctivo",
            "Instalacion",
            "Reparacion",
            "Levantamiento",
        ],
        "estatus": [
            "Servicio concluido",
            "Servicio concluido con observaciones",
            "Pendiente por material",
            "Pendiente por autorizacion",
            "No concluido",
        ],
    },
    "Samsung": {
        "destinatarios": ["gerardo.mendez@besco.mx"],
        "tipos_servicio": [
            "Diagnostico",
            "Correctivo",
            "Instalacion",
            "Validacion",
            "Retiro",
            "Levantamiento",
        ],
        "estatus": [
            "Servicio concluido",
            "Servicio concluido con observaciones",
            "Pendiente por material",
            "Pendiente por autorizacion",
            "No concluido",
        ],
    },
}


# =========================================================
# ALCANCES
# =========================================================
ALCANCES = [
    ("01_Electrico", "Instalaciones electricas y tableros"),
    ("02_Canceleria_Vidrieria", "Perfiles, cristales y herrajes"),
    ("03_Hidrosanitaria", "Acometida, bombeo, pluviales"),
    ("04_Mobiliario", "Mobiliario y cerrajeria basica"),
    ("05_Generales", "Acabados, limpieza y reparaciones"),
    ("06.1_AA_Paquetes", "A/A integrales/paquetes"),
    ("06.2_AA_Divididos", "Mini-split/Fan and Coil"),
    ("06.3_Chillers_Manej", "Chillers/Manejadora"),
    ("06.4_Manejadoras_AireLav", "Manejadoras de aire lavado"),
    ("06.5_AA_menor_3TR", "Aire acondicionado menor a 3 TR"),
    ("07_UPS", "Revision de UPS"),
    ("09_Depositos_Agua", "Cisternas y tinacos"),
    ("13_Reportes", "Gestion documental"),
]


# =========================================================
# EVIDENCIAS
# =========================================================
EVIDENCIAS_OBLIGATORIAS = [
    "Fotos de fachada",
    "Fotos de acceso",
    "Fotos de area intervenida",
    "Antes",
    "Durante",
    "Despues",
]

EVIDENCIA_DOCUMENTAL = "Folio / ticket"
EVIDENCIA_OPCIONAL = "Evidencia adicional"


# =========================================================
# ESTILOS
# =========================================================
def aplicar_estilos():
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

        .titulo {
            text-align: center;
            color: #1E3A5F;
            font-size: 1.65rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitulo {
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
            color: #334E68;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }

        .warning-box {
            background-color: #FFF4E5;
            border: 1px solid #F3D19C;
            border-radius: 12px;
            padding: 12px;
            color: #9A6700;
            font-size: 0.9rem;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .ok-box {
            background-color: #E3FCEF;
            border: 1px solid #B7E4C7;
            border-radius: 12px;
            padding: 12px;
            color: #127C56;
            font-size: 0.9rem;
            margin-top: 10px;
            margin-bottom: 10px;
        }

        .footer {
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
        unsafe_allow_html=True,
    )


# =========================================================
# UTILIDADES
# =========================================================
def limpiar_texto(texto):
    if texto is None:
        return ""

    texto = str(texto)

    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "ñ": "n",
        "Ñ": "N",
        "ü": "u",
        "Ü": "U",
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

    for original, nuevo in reemplazos.items():
        texto = texto.replace(original, nuevo)

    return texto


def limpiar_nombre_archivo(nombre):
    invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")", "&"]

    limpio = limpiar_texto(str(nombre))

    for caracter in invalidos:
        limpio = limpio.replace(caracter, "_")

    limpio = limpio.replace(" ", "_")

    return limpio


def dividir_texto(texto, max_chars=90):
    palabras = limpiar_texto(texto).split()
    lineas = []
    linea_actual = ""

    for palabra in palabras:
        if len(linea_actual) + len(palabra) + 1 <= max_chars:
            if linea_actual:
                linea_actual += " " + palabra
            else:
                linea_actual = palabra
        else:
            lineas.append(linea_actual)
            linea_actual = palabra

    if linea_actual:
        lineas.append(linea_actual)

    return lineas


def comprimir_imagen_a_temp(uploaded_file):
    uploaded_file.seek(0)

    imagen = Image.open(uploaded_file).convert("RGB")
    imagen.thumbnail(MAX_IMAGE_SIZE)

    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_img.close()

    imagen.save(
        temp_img.name,
        format="JPEG",
        quality=IMAGE_QUALITY,
        optimize=True
    )

    return temp_img.name


def contar_archivos(archivos):
    if not archivos:
        return 0

    return len(archivos)


def mostrar_estado(nombre, archivos):
    cantidad = contar_archivos(archivos)

    if cantidad == 0:
        st.caption(f"{nombre}: sin archivos cargados.")
    elif cantidad <= MAX_FOTOS_POR_SECCION:
        st.success(f"{nombre}: {cantidad} archivo(s) cargado(s).")
    else:
        st.warning(
            f"{nombre}: {cantidad} archivo(s) cargado(s). "
            f"Se integraran maximo {MAX_FOTOS_POR_SECCION} para mantener ligero el PDF."
        )


def obtener_descripcion(seccion):
    for sec, desc in ALCANCES:
        if sec == seccion:
            return desc

    return ""


# =========================================================
# PDF
# =========================================================
def encabezado_pdf(c, titulo):
    y = 750

    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.setFont("Helvetica-Bold", 15)
    c.drawString(MARGIN_LEFT, y, limpiar_texto(titulo))

    y -= 18

    c.setFillColor(colors.HexColor("#5B6573"))
    c.setFont("Helvetica", 9)
    fecha_generado = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    c.drawString(MARGIN_LEFT, y, f"Generado el {fecha_generado}")

    y -= 20

    c.setStrokeColor(colors.HexColor("#D9E2EC"))
    c.line(MARGIN_LEFT, y, PDF_WIDTH - MARGIN_RIGHT, y)

    y -= 25

    return y


def nueva_pagina(c, y, espacio=120):
    if y < espacio:
        c.showPage()
        y = encabezado_pdf(c, "REPORTE FOTOGRAFICO - CONTINUACION")

    return y


def titulo_seccion(c, titulo, y):
    y = nueva_pagina(c, y, 80)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(MARGIN_LEFT, y, limpiar_texto(titulo))

    y -= 18

    return y


def linea_pdf(c, etiqueta, valor, y):
    y = nueva_pagina(c, y, 70)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(MARGIN_LEFT, y, limpiar_texto(f"{etiqueta}:"))

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_LEFT + 125, y, limpiar_texto(valor))

    y -= 15

    return y


def bloque_texto_pdf(c, titulo, texto, y):
    y = titulo_seccion(c, titulo, y)

    if not texto:
        texto = "Sin informacion capturada."

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)

    for linea in dividir_texto(texto):
        y = nueva_pagina(c, y, 70)
        c.drawString(MARGIN_LEFT, y, limpiar_texto(linea))
        y -= 13

    y -= 10

    return y


def imagen_pdf(c, titulo, uploaded_file, y):
    if uploaded_file is None:
        return y

    y = nueva_pagina(c, y, 240)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(MARGIN_LEFT, y, limpiar_texto(titulo))

    y -= 10

    temp_path = None

    try:
        temp_path = comprimir_imagen_a_temp(uploaded_file)
        img_reader = ImageReader(temp_path)

        img_w, img_h = img_reader.getSize()

        ancho_max = 250
        alto_max = 160

        ratio = min(ancho_max / img_w, alto_max / img_h)

        draw_w = img_w * ratio
        draw_h = img_h * ratio

        y -= draw_h + 8

        c.drawImage(
            img_reader,
            MARGIN_LEFT,
            y,
            width=draw_w,
            height=draw_h,
            preserveAspectRatio=True,
            mask="auto"
        )

        y -= 18

    except Exception as error:
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.red)
        c.drawString(
            MARGIN_LEFT,
            y - 20,
            limpiar_texto(f"No se pudo insertar imagen: {error}")
        )
        y -= 40

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

    return y


def crear_pdf(
    contrato,
    folio,
    fecha_ejecucion,
    sucursal,
    direccion,
    ciudad,
    oficina,
    tecnico,
    supervisor,
    tipo_servicio,
    estatus_final,
    seccion,
    descripcion,
    actividades,
    observaciones,
    df_materiales,
    evidencias,
    destinatarios,
):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = temp_pdf.name
    temp_pdf.close()

    c = canvas.Canvas(pdf_path, pagesize=letter)

    y = encabezado_pdf(c, "REPORTE FOTOGRAFICO POR CONTRATO")

    y = titulo_seccion(c, "Datos generales", y)

    y = linea_pdf(c, "Contrato", contrato, y)
    y = linea_pdf(c, "Folio / Ticket / OT", folio, y)
    y = linea_pdf(c, "Fecha de ejecucion", fecha_ejecucion.strftime("%d/%m/%Y"), y)
    y = linea_pdf(c, "Sucursal / Inmueble", sucursal, y)
    y = linea_pdf(c, "Direccion", direccion if direccion else "-", y)
    y = linea_pdf(c, "Ciudad", ciudad if ciudad else "-", y)
    y = linea_pdf(c, "Oficina responsable", oficina if oficina else "-", y)
    y = linea_pdf(c, "Tecnico asignado", tecnico, y)
    y = linea_pdf(c, "Supervisor", supervisor if supervisor else "-", y)
    y = linea_pdf(c, "Tipo de servicio", tipo_servicio, y)
    y = linea_pdf(c, "Estatus final", estatus_final, y)

    y -= 8

    y = titulo_seccion(c, "Alcance del servicio", y)
    y = linea_pdf(c, "Seccion", seccion, y)
    y = linea_pdf(c, "Descripcion", descripcion, y)

    y = bloque_texto_pdf(c, "Actividades realizadas", actividades, y)

    if df_materiales is not None and not df_materiales.empty:
        y = titulo_seccion(c, "Materiales utilizados", y)

        for _, row in df_materiales.iterrows():
            cantidad = str(row.get("Cantidad", "")).strip()
            descripcion_material = str(row.get("Descripcion", "")).strip()

            if descripcion_material:
                y = linea_pdf(
                    c,
                    "Material",
                    f"{cantidad} - {descripcion_material}",
                    y
                )

        y -= 8

    y = bloque_texto_pdf(c, "Observaciones", observaciones, y)

    y = titulo_seccion(c, "Evidencias fotograficas", y)

    hay_evidencias = False

    for nombre_evidencia, archivos in evidencias.items():
        if archivos:
            hay_evidencias = True

            archivos_limitados = archivos[:MAX_FOTOS_POR_SECCION]

            for index, archivo in enumerate(archivos_limitados, start=1):
                if hasattr(archivo, "type") and archivo.type == "application/pdf":
                    y = linea_pdf(
                        c,
                        nombre_evidencia,
                        f"PDF adjunto registrado: {archivo.name}",
                        y
                    )
                else:
                    y = imagen_pdf(
                        c,
                        f"{nombre_evidencia} - Foto {index}",
                        archivo,
                        y
                    )

            if len(archivos) > MAX_FOTOS_POR_SECCION:
                y = linea_pdf(
                    c,
                    nombre_evidencia,
                    f"Se integraron {MAX_FOTOS_POR_SECCION} de {len(archivos)} archivos.",
                    y
                )

    if not hay_evidencias:
        y = linea_pdf(c, "Evidencias", "No se adjuntaron evidencias.", y)

    y = bloque_texto_pdf(
        c,
        "Destinatarios configurados",
        "\n".join(destinatarios) if destinatarios else "Sin destinatarios configurados.",
        y
    )

    y = nueva_pagina(c, y, 80)

    c.setStrokeColor(colors.HexColor("#D9E2EC"))
    c.line(MARGIN_LEFT, y, PDF_WIDTH - MARGIN_RIGHT, y)

    y -= 18

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#7B8794"))
    c.drawString(
        MARGIN_LEFT,
        y,
        "Sistema Operativo - Grupo Besco | Reporte generado automaticamente"
    )

    c.save()

    return pdf_path


# =========================================================
# CORREO
# =========================================================
def enviar_correo(
    pdf_path,
    contrato,
    folio,
    sucursal,
    oficina,
    nombre_archivo,
    correos_extra,
    fecha_ejecucion,
    destinatarios_base,
):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            return False, "Faltan EMAIL_SENDER o EMAIL_PASSWORD en Secrets."

        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]

        extras = []

        if correos_extra:
            extras = [
                correo.strip()
                for correo in correos_extra.split(",")
                if correo.strip()
            ]

        destinatarios = list(set(destinatarios_base + extras))

        msg = EmailMessage()
        msg["Subject"] = limpiar_texto(
            f"Reporte Fotografico BESCO: {contrato} | TK: {folio} | Of: {oficina}"
        )
        msg["From"] = remitente
        msg["To"] = ", ".join(destinatarios)

        msg.set_content(
            limpiar_texto(
                f"Se ha generado un nuevo reporte fotografico desde el Portal de Soluciones BESCO.\n\n"
                f"Contrato: {contrato}\n"
                f"Fecha de ejecucion: {fecha_ejecucion}\n"
                f"Oficina: {oficina}\n"
                f"Folio / Ticket / OT: {folio}\n"
                f"Sucursal / Inmueble: {sucursal}\n\n"
                f"Se adjunta el PDF del reporte."
            )
        )

        with open(pdf_path, "rb") as archivo:
            msg.add_attachment(
                archivo.read(),
                maintype="application",
                subtype="pdf",
                filename=nombre_archivo
            )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)

        return True, "Correo enviado correctamente."

    except Exception as error:
        return False, f"No se pudo enviar el correo: {error}"


# =========================================================
# VALIDACION
# =========================================================
def validar_reporte(contrato, folio, sucursal, tecnico, seccion, actividades, evidencias):
    faltantes = []

    if not contrato:
        faltantes.append("Contrato")

    if not folio.strip():
        faltantes.append("Folio / Ticket / OT")

    if not sucursal.strip():
        faltantes.append("Sucursal / Inmueble")

    if not tecnico.strip():
        faltantes.append("Tecnico asignado")

    if not seccion:
        faltantes.append("Seccion / Alcance")

    if not actividades.strip():
        faltantes.append("Actividades realizadas")

    for evidencia in EVIDENCIAS_OBLIGATORIAS:
        if not evidencias.get(evidencia):
            faltantes.append(evidencia)

    return faltantes


# =========================================================
# APP
# =========================================================
def main():
    aplicar_estilos()

    st.markdown(
        """
        <div class="titulo">📷 Reporte Fotografico por Contrato</div>
        <div class="subtitulo">
            Reporte configurable por contrato, alcance, evidencias, PDF y correo.
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
            Version ligera para celular. Primero genera el PDF, despues descargalo o envialo por correo.
            Las fotos se comprimen automaticamente.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("1. Datos generales")

    contrato = st.selectbox(
        "Contrato",
        list(CONTRATOS_CONFIG.keys())
    )

    config = CONTRATOS_CONFIG[contrato]

    tipo_servicio = st.selectbox(
        "Tipo de servicio",
        config["tipos_servicio"]
    )

    estatus_final = st.selectbox(
        "Estatus final",
        config["estatus"]
    )

    folio = st.text_input(
        "Folio / Ticket / OT",
        max_chars=40
    )

    fecha_ejecucion = st.date_input(
        "Fecha de ejecucion",
        datetime.now()
    )

    sucursal = st.text_input("Sucursal / Inmueble")
    direccion = st.text_input("Direccion")
    ciudad = st.text_input("Ciudad")
    oficina = st.text_input("Oficina responsable")
    tecnico = st.text_input("Tecnico asignado")
    supervisor = st.text_input("Supervisor")

    st.divider()

    st.subheader("2. Alcance")

    labels_alcances = [
        f"{seccion} - {descripcion}"
        for seccion, descripcion in ALCANCES
    ]

    alcance_label = st.selectbox(
        "Selecciona la seccion del alcance",
        labels_alcances
    )

    seccion = alcance_label.split(" - ")[0].strip()
    descripcion = obtener_descripcion(seccion)

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Seccion:</strong> {seccion}<br>
            <strong>Descripcion:</strong> {descripcion}
        </div>
        """,
        unsafe_allow_html=True
    )

    actividades_default = (
        f"Se ejecutan actividades correspondientes a la seccion {seccion}: {descripcion}."
    )

    actividades = st.text_area(
        "Actividades realizadas",
        value=actividades_default,
        height=130
    )

    st.divider()

    st.subheader("3. Evidencias fotograficas")

    st.markdown(
        """
        <div class="warning-box">
            No se muestran vistas previas para mantener ligera la app.
            Se recomienda maximo 6 fotos por seccion.
        </div>
        """,
        unsafe_allow_html=True
    )

    evidencias = {}

    st.markdown("#### Evidencias obligatorias")

    for evidencia in EVIDENCIAS_OBLIGATORIAS:
        archivos = st.file_uploader(
            evidencia,
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key=f"ev_{evidencia}"
        )

        evidencias[evidencia] = archivos
        mostrar_estado(evidencia, archivos)

    st.markdown("#### Evidencia documental")

    archivos_folio = st.file_uploader(
        EVIDENCIA_DOCUMENTAL,
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        key="ev_folio_ticket"
    )

    evidencias[EVIDENCIA_DOCUMENTAL] = archivos_folio
    mostrar_estado(EVIDENCIA_DOCUMENTAL, archivos_folio)

    st.markdown("#### Evidencia opcional")

    archivos_adicional = st.file_uploader(
        EVIDENCIA_OPCIONAL,
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="ev_adicional"
    )

    evidencias[EVIDENCIA_OPCIONAL] = archivos_adicional
    mostrar_estado(EVIDENCIA_OPCIONAL, archivos_adicional)

    st.divider()

    st.subheader("4. Observaciones y materiales")

    observaciones = st.text_area(
        "Observaciones",
        height=120
    )

    usar_materiales = st.checkbox(
        "Agregar materiales utilizados",
        value=False
    )

    if usar_materiales:
        df_materiales = st.data_editor(
            pd.DataFrame(columns=["Cantidad", "Descripcion"]),
            num_rows="dynamic",
            use_container_width=True
        )
    else:
        df_materiales = pd.DataFrame(columns=["Cantidad", "Descripcion"])

    st.divider()

    st.subheader("5. Generar PDF y enviar correo")

    destinatarios_base = config["destinatarios"].copy()

    if "gerardo.mendez@besco.mx" not in destinatarios_base:
        destinatarios_base.append("gerardo.mendez@besco.mx")

    st.info(f"Destinatarios automaticos: {', '.join(destinatarios_base)}")

    correos_extra = st.text_input(
        "Correos adicionales separados por coma"
    )

    faltantes = validar_reporte(
        contrato=contrato,
        folio=folio,
        sucursal=sucursal,
        tecnico=tecnico,
        seccion=seccion,
        actividades=actividades,
        evidencias=evidencias
    )

    if faltantes:
        st.markdown(
            f"""
            <div class="warning-box">
                Faltan campos o evidencias obligatorias: {", ".join(faltantes)}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div class="ok-box">
                Datos minimos completos. Puedes generar el PDF.
            </div>
            """,
            unsafe_allow_html=True
        )

    permitir_incompleto = st.checkbox(
        "Permitir generar PDF aunque falten campos/evidencias obligatorias",
        value=True
    )

    puede_generar = permitir_incompleto or not faltantes

    generar = st.button(
        "📄 Generar PDF",
        type="primary",
        use_container_width=True,
        disabled=not puede_generar
    )

    if generar:
        with st.spinner("Generando PDF y comprimiendo imagenes..."):
            try:
                pdf_path = crear_pdf(
                    contrato=contrato,
                    folio=folio,
                    fecha_ejecucion=fecha_ejecucion,
                    sucursal=sucursal,
                    direccion=direccion,
                    ciudad=ciudad,
                    oficina=oficina,
                    tecnico=tecnico,
                    supervisor=supervisor,
                    tipo_servicio=tipo_servicio,
                    estatus_final=estatus_final,
                    seccion=seccion,
                    descripcion=descripcion,
                    actividades=actividades,
                    observaciones=observaciones,
                    df_materiales=df_materiales,
                    evidencias=evidencias,
                    destinatarios=destinatarios_base,
                )

                nombre_pdf = limpiar_nombre_archivo(
                    f"Reporte_Fotografico_{contrato}_{seccion}_{folio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                )

                st.session_state["rf_contrato_pdf_path"] = pdf_path
                st.session_state["rf_contrato_nombre_pdf"] = nombre_pdf
                st.session_state["rf_contrato_fecha"] = fecha_ejecucion.strftime("%d/%m/%Y")
                st.session_state["rf_contrato_datos_mail"] = {
                    "contrato": contrato,
                    "folio": folio,
                    "sucursal": sucursal,
                    "oficina": oficina,
                    "correos_extra": correos_extra,
                    "destinatarios": destinatarios_base,
                }

                st.success("PDF generado correctamente.")

            except Exception as error:
                st.error(f"No se pudo generar el PDF: {error}")
                st.exception(error)

    if "rf_contrato_pdf_path" in st.session_state:
        pdf_path = st.session_state["rf_contrato_pdf_path"]
        nombre_pdf = st.session_state["rf_contrato_nombre_pdf"]

        with open(pdf_path, "rb") as archivo_pdf:
            st.download_button(
                "⬇️ Descargar PDF",
                data=archivo_pdf,
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True
            )

        enviar = st.button(
            "📨 Enviar reporte por correo",
            use_container_width=True
        )

        if enviar:
            datos_mail = st.session_state["rf_contrato_datos_mail"]

            with st.spinner("Enviando correo..."):
                enviado, mensaje = enviar_correo(
                    pdf_path=pdf_path,
                    contrato=datos_mail["contrato"],
                    folio=datos_mail["folio"],
                    sucursal=datos_mail["sucursal"],
                    oficina=datos_mail["oficina"],
                    nombre_archivo=nombre_pdf,
                    correos_extra=datos_mail["correos_extra"],
                    fecha_ejecucion=st.session_state["rf_contrato_fecha"],
                    destinatarios_base=datos_mail["destinatarios"],
                )

            if enviado:
                st.success(mensaje)
            else:
                st.warning(mensaje)

    st.divider()

    st.markdown(
        """
        <div class="footer">
            Sistema Operativo - Grupo Besco | Reporte Fotografico por Contrato
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
