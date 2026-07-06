import os
import tempfile
import smtplib
import textwrap
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

TIPOS_SERVICIO = [
    "Correctivo",
    "Preventivo",
    "Levantamiento",
]


st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)


# =========================================================
# CONFIGURACION DE CONTRATOS
# =========================================================
CONTRATOS_CONFIG = {
    "Santander": {
        "destinatarios": ["gerardo.mendez@besco.mx"],
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
# ALCANCES POR CONTRATO
# Todas las evidencias fotograficas son opcionales.
# required se mantiene solo como referencia visual.
# =========================================================
ALCANCES_POR_CONTRATO = {
    "Santander": [
        {
            "numero": 1,
            "momento": "Arribo",
            "actividad": "Presentarse con gerente encargado. Confirmar OT/folio y alcance de visita.",
            "required": False,
        },
        {
            "numero": 2,
            "momento": "Seguridad",
            "actividad": "Induccion rapida: zonas restringidas, riesgos, energia, alturas y agua.",
            "required": False,
        },
        {
            "numero": 3,
            "momento": "Reconocimiento",
            "actividad": "Recorrido inicial por areas aplicables segun CHECK LIST.",
            "required": False,
        },
        {
            "numero": 4,
            "momento": "01_Electrico",
            "actividad": "Instalaciones electricas y tableros.",
            "required": False,
        },
        {
            "numero": 5,
            "momento": "02_Canceleria_Vidrieria",
            "actividad": "Perfiles, cristales y herrajes.",
            "required": False,
        },
        {
            "numero": 6,
            "momento": "03_Hidrosanitaria",
            "actividad": "Acometida y bajadas pluviales.",
            "required": False,
        },
        {
            "numero": 7,
            "momento": "03_Hidrosanitaria_Bombeo",
            "actividad": "Sistema de bombeo. Evidencia opcional.",
            "required": False,
        },
        {
            "numero": 8,
            "momento": "04_Mobiliario",
            "actividad": "Mobiliario y cerrajeria basica.",
            "required": False,
        },
        {
            "numero": 9,
            "momento": "05_Generales",
            "actividad": "Acabados, limpieza, pintura y reparaciones generales.",
            "required": False,
        },
        {
            "numero": 10,
            "momento": "06_AA_Parametros",
            "actividad": "Equipos de aire acondicionado con toma de parametros: minisplit, fan and coil, manejadora, aire lavado y chiller.",
            "required": False,
        },
        {
            "numero": 11,
            "momento": "07_UPS",
            "actividad": "Revision de UPS y toma de parametros.",
            "required": False,
        },
        {
            "numero": 12,
            "momento": "09_Depositos_Agua_Cisterna",
            "actividad": "Depositos de agua: cisterna.",
            "required": False,
        },
        {
            "numero": 13,
            "momento": "09_Depositos_Agua_Tinacos",
            "actividad": "Depositos de agua: tinacos. Evidencia opcional.",
            "required": False,
        },
        {
            "numero": 14,
            "momento": "Desviaciones",
            "actividad": "Documentar hallazgos con causa, impacto, material y recomendacion. Evidencia opcional.",
            "required": False,
        },
        {
            "numero": 15,
            "momento": "Limpieza y pruebas",
            "actividad": "Retirar residuos, normalizar areas y probar equipos intervenidos.",
            "required": False,
        },
    ],
    "MacStore": [
        {
            "numero": 1,
            "momento": "Arribo",
            "actividad": "Presentarse en tienda y confirmar folio, alcance y responsable en sitio.",
            "required": False,
        },
        {
            "numero": 2,
            "momento": "Inspeccion inicial",
            "actividad": "Realizar recorrido inicial y levantar evidencia del area intervenida.",
            "required": False,
        },
        {
            "numero": 3,
            "momento": "Ejecucion",
            "actividad": "Ejecutar actividades correctivas, preventivas o de levantamiento segun servicio.",
            "required": False,
        },
        {
            "numero": 4,
            "momento": "Pruebas",
            "actividad": "Validar funcionamiento, limpieza del area y condiciones finales.",
            "required": False,
        },
        {
            "numero": 5,
            "momento": "Cierre",
            "actividad": "Documentar hallazgos, evidencias, actividades y cierre con responsable.",
            "required": False,
        },
    ],
    "Samsung": [
        {
            "numero": 1,
            "momento": "Arribo",
            "actividad": "Presentarse en sitio y confirmar folio, alcance y responsable.",
            "required": False,
        },
        {
            "numero": 2,
            "momento": "Diagnostico",
            "actividad": "Realizar diagnostico inicial y documentar condiciones encontradas.",
            "required": False,
        },
        {
            "numero": 3,
            "momento": "Ejecucion",
            "actividad": "Ejecutar instalacion, validacion, retiro o correccion segun servicio.",
            "required": False,
        },
        {
            "numero": 4,
            "momento": "Pruebas",
            "actividad": "Realizar pruebas de funcionamiento y documentar resultado.",
            "required": False,
        },
        {
            "numero": 5,
            "momento": "Reporte",
            "actividad": "Registrar evidencias, observaciones y cierre del servicio.",
            "required": False,
        },
    ],
}


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

        .optional-box {
            background-color: #F4F6F8;
            border: 1px solid #D0D5DD;
            border-radius: 12px;
            padding: 10px;
            color: #475467;
            font-size: 0.85rem;
            margin-top: 8px;
            margin-bottom: 8px;
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
def normalizar_texto(texto):
    if texto is None:
        return ""

    valor = str(texto)

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
        valor = valor.replace(original, nuevo)

    return valor


def crear_nombre_archivo(nombre):
    valor = normalizar_texto(nombre)

    invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")", "&"]

    for caracter in invalidos:
        valor = valor.replace(caracter, "_")

    valor = valor.replace(" ", "_")

    return valor


def dividir_texto(texto, max_chars=90):
    texto_limpio = normalizar_texto(texto)

    if not texto_limpio.strip():
        return ["Sin informacion capturada."]

    lineas = textwrap.wrap(
        texto_limpio,
        width=max_chars,
        break_long_words=False,
        replace_whitespace=False
    )

    if not lineas:
        return ["Sin informacion capturada."]

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


def existe_archivo(uploaded_file):
    return uploaded_file is not None


# =========================================================
# PDF
# =========================================================
def encabezado_pdf(c, titulo):
    y = 750

    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.setFont("Helvetica-Bold", 15)
    c.drawString(MARGIN_LEFT, y, normalizar_texto(titulo))

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
    c.drawString(MARGIN_LEFT, y, normalizar_texto(titulo))

    y -= 18

    return y


def linea_pdf(c, etiqueta, valor, y):
    y = nueva_pagina(c, y, 70)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(MARGIN_LEFT, y, normalizar_texto(f"{etiqueta}:"))

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_LEFT + 125, y, normalizar_texto(valor))

    y -= 15

    return y


def bloque_texto_pdf(c, titulo, texto, y):
    y = titulo_seccion(c, titulo, y)

    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)

    for linea in dividir_texto(texto):
        y = nueva_pagina(c, y, 70)
        c.drawString(MARGIN_LEFT, y, normalizar_texto(linea))
        y -= 13

    y -= 10

    return y


def imagen_pdf(c, titulo, uploaded_file, y):
    if uploaded_file is None:
        return y

    y = nueva_pagina(c, y, 240)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(MARGIN_LEFT, y, normalizar_texto(titulo))

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
            normalizar_texto(f"No se pudo insertar imagen: {error}")
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
    alcance_items,
    evidencias_por_item,
    observaciones,
    df_materiales,
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

    y = titulo_seccion(c, "Alcance y evidencias", y)

    for item in alcance_items:
        numero = item["numero"]
        momento = item["momento"]
        actividad = item["actividad"]

        y = nueva_pagina(c, y, 160)

        y = linea_pdf(c, "Renglon", str(numero), y)
        y = linea_pdf(c, "Momento", momento, y)
        y = linea_pdf(c, "Tipo evidencia", "Opcional", y)
        y = bloque_texto_pdf(c, "Actividad critica", actividad, y)

        evidencia = evidencias_por_item.get(numero, {})

        y = imagen_pdf(c, f"{momento} - Antes 1", evidencia.get("antes_1"), y)
        y = imagen_pdf(c, f"{momento} - Antes 2", evidencia.get("antes_2"), y)
        y = imagen_pdf(c, f"{momento} - Despues 1", evidencia.get("despues_1"), y)
        y = imagen_pdf(c, f"{momento} - Despues 2", evidencia.get("despues_2"), y)

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

    y = bloque_texto_pdf(c, "Observaciones", observaciones, y)

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
        msg["Subject"] = normalizar_texto(
            f"Reporte Fotografico BESCO: {contrato} | TK: {folio} | Of: {oficina}"
        )
        msg["From"] = remitente
        msg["To"] = ", ".join(destinatarios)

        msg.set_content(
            normalizar_texto(
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
def validar_reporte(contrato, folio, sucursal, tecnico):
    faltantes = []

    if not contrato:
        faltantes.append("Contrato")

    if not folio.strip():
        faltantes.append("Folio / Ticket / OT")

    if not sucursal.strip():
        faltantes.append("Sucursal / Inmueble")

    if not tecnico.strip():
        faltantes.append("Tecnico asignado")

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
            Version ligera para celular. Todas las fotos son opcionales.
            Si se cargan fotos, se integraran al PDF. Si no se cargan, el PDF se genera solo con datos y alcance.
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
    alcance_items = ALCANCES_POR_CONTRATO.get(contrato, [])

    tipo_servicio = st.selectbox(
        "Tipo de servicio",
        TIPOS_SERVICIO
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

    st.subheader("2. Alcance del contrato")

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Contrato seleccionado:</strong> {contrato}<br>
            <strong>Renglones del alcance:</strong> {len(alcance_items)}<br>
            Todas las evidencias fotograficas son opcionales.
        </div>
        """,
        unsafe_allow_html=True
    )

    evidencias_por_item = {}

    for item in alcance_items:
        numero = item["numero"]
        momento = item["momento"]
        actividad = item["actividad"]

        titulo_expander = f"{numero}. {momento} (Fotos opcionales)"

        with st.expander(titulo_expander, expanded=False):
            st.markdown(
                """
                <div class="optional-box">
                    Fotos opcionales: puedes cargar hasta 2 fotos antes y 2 fotos despues.
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div class="info-box">
                    <strong>Actividad critica:</strong><br>
                    {actividad}
                </div>
                """,
                unsafe_allow_html=True
            )

            antes_1 = st.file_uploader(
                f"{momento} - Antes 1 opcional",
                type=["jpg", "jpeg", "png"],
                key=f"{contrato}_{numero}_antes_1"
            )

            antes_2 = st.file_uploader(
                f"{momento} - Antes 2 opcional",
                type=["jpg", "jpeg", "png"],
                key=f"{contrato}_{numero}_antes_2"
            )

            despues_1 = st.file_uploader(
                f"{momento} - Despues 1 opcional",
                type=["jpg", "jpeg", "png"],
                key=f"{contrato}_{numero}_despues_1"
            )

            despues_2 = st.file_uploader(
                f"{momento} - Despues 2 opcional",
                type=["jpg", "jpeg", "png"],
                key=f"{contrato}_{numero}_despues_2"
            )

            evidencias_por_item[numero] = {
                "antes_1": antes_1,
                "antes_2": antes_2,
                "despues_1": despues_1,
                "despues_2": despues_2,
            }

            cargadas = 0

            if antes_1:
                cargadas += 1

            if antes_2:
                cargadas += 1

            if despues_1:
                cargadas += 1

            if despues_2:
                cargadas += 1

            st.info(f"Fotos cargadas en este renglon: {cargadas} de 4 opcionales.")

    st.divider()

    st.subheader("3. Observaciones y materiales")

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

    st.subheader("4. Estatus final")

    estatus_final = st.selectbox(
        "Estatus final",
        config["estatus"]
    )

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
        tecnico=tecnico
    )

    if faltantes:
        st.markdown(
            f"""
            <div class="warning-box">
                Faltan campos obligatorios: {", ".join(faltantes)}
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

    generar = st.button(
        "📄 Generar PDF",
        type="primary",
        use_container_width=True,
        disabled=bool(faltantes)
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
                    alcance_items=alcance_items,
                    evidencias_por_item=evidencias_por_item,
                    observaciones=observaciones,
                    df_materiales=df_materiales,
                    destinatarios=destinatarios_base,
                )

                nombre_pdf = crear_nombre_archivo(
                    f"Reporte_Fotografico_{contrato}_{folio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
