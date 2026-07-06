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
MARGIN_BOTTOM = 55

MAX_IMAGE_SIZE = (1000, 1000)
IMAGE_QUALITY = 65

APP_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(APP_DIR, ".."))
CWD_DIR = os.getcwd()

TIPOS_SERVICIO = [
    "Correctivo",
    "Preventivo",
    "Levantamiento",
]

EXTENSIONES_LOGO = [".png", ".jpg", ".jpeg"]


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
        "destinatarios": [
            "gerardo.mendez@besco.mx",
            "alejandro.ramirez@besco.mx",
            "patricia.cortes@besco.mx",
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
        "destinatarios": [
            "gerardo.mendez@besco.mx",
            "andres.mayagoitia@besco.mx",
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
        "destinatarios": [
            "gerardo.mendez@besco.mx",
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
# ALCANCES POR CONTRATO
# =========================================================
ALCANCES_POR_CONTRATO = {
    "Santander": [
        {
            "numero": 1,
            "momento": "Arribo",
            "actividad": "Presentarse con gerente encargado. Confirmar OT/folio y alcance de visita.",
        },
        {
            "numero": 2,
            "momento": "Seguridad",
            "actividad": "Induccion rapida: zonas restringidas, riesgos, energia, alturas y agua.",
        },
        {
            "numero": 3,
            "momento": "Reconocimiento",
            "actividad": "Recorrido inicial por areas aplicables segun CHECK LIST.",
        },
        {
            "numero": 4,
            "momento": "01_Electrico",
            "actividad": "Instalaciones electricas y tableros.",
        },
        {
            "numero": 5,
            "momento": "02_Canceleria_Vidrieria",
            "actividad": "Perfiles, cristales y herrajes.",
        },
        {
            "numero": 6,
            "momento": "03_Hidrosanitaria",
            "actividad": "Acometida y bajadas pluviales.",
        },
        {
            "numero": 7,
            "momento": "03_Hidrosanitaria_Bombeo",
            "actividad": "Sistema de bombeo. Evidencia opcional.",
        },
        {
            "numero": 8,
            "momento": "04_Mobiliario",
            "actividad": "Mobiliario y cerrajeria basica.",
        },
        {
            "numero": 9,
            "momento": "05_Generales",
            "actividad": "Acabados, limpieza, pintura y reparaciones generales.",
        },
        {
            "numero": 10,
            "momento": "06_AA_Parametros",
            "actividad": "Equipos de aire acondicionado con toma de parametros: minisplit, fan and coil, manejadora, aire lavado y chiller.",
        },
        {
            "numero": 11,
            "momento": "07_UPS",
            "actividad": "Revision de UPS y toma de parametros.",
        },
        {
            "numero": 12,
            "momento": "09_Depositos_Agua_Cisterna",
            "actividad": "Depositos de agua: cisterna.",
        },
        {
            "numero": 13,
            "momento": "09_Depositos_Agua_Tinacos",
            "actividad": "Depositos de agua: tinacos. Evidencia opcional.",
        },
        {
            "numero": 14,
            "momento": "Desviaciones",
            "actividad": "Documentar hallazgos con causa, impacto, material y recomendacion. Evidencia opcional.",
        },
        {
            "numero": 15,
            "momento": "Limpieza y pruebas",
            "actividad": "Retirar residuos, normalizar areas y probar equipos intervenidos.",
        },
    ],
    "MacStore": [
        {
            "numero": 1,
            "momento": "Arribo",
            "actividad": "Presentarse en tienda y confirmar folio, alcance y responsable en sitio.",
        },
        {
            "numero": 2,
            "momento": "Inspeccion inicial",
            "actividad": "Realizar recorrido inicial y levantar evidencia del area intervenida.",
        },
        {
            "numero": 3,
            "momento": "Ejecucion",
            "actividad": "Ejecutar actividades correctivas, preventivas o de levantamiento segun servicio.",
        },
        {
            "numero": 4,
            "momento": "Pruebas",
            "actividad": "Validar funcionamiento, limpieza del area y condiciones finales.",
        },
        {
            "numero": 5,
            "momento": "Cierre",
            "actividad": "Documentar hallazgos, evidencias, actividades y cierre con responsable.",
        },
    ],
    "Samsung": [
        {
            "numero": 1,
            "momento": "Arribo",
            "actividad": "Presentarse en sitio y confirmar folio, alcance y responsable.",
        },
        {
            "numero": 2,
            "momento": "Diagnostico",
            "actividad": "Realizar diagnostico inicial y documentar condiciones encontradas.",
        },
        {
            "numero": 3,
            "momento": "Ejecucion",
            "actividad": "Ejecutar instalacion, validacion, retiro o correccion segun servicio.",
        },
        {
            "numero": 4,
            "momento": "Pruebas",
            "actividad": "Realizar pruebas de funcionamiento y documentar resultado.",
        },
        {
            "numero": 5,
            "momento": "Reporte",
            "actividad": "Registrar evidencias, observaciones y cierre del servicio.",
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

    for*caracter in invalidos:
        val*r = valor.replace(caracter, "_")

*   valor = valor.replace(" ", "_")*
    return valor


def dividir_te*to(texto, max_chars=90):
    texto*limpio = normalizar_texto(texto)

*   if not texto_limpio.strip():
  *     return ["Sin informacion capturada."]

    lineas = textwrap.wra*(
        texto_limpio,
        wi*th=max_chars,
        break_long_w*rds=False,
        replace_whitesp*ce=False
    )

    if not lineas:*        return ["Sin informacion capturada."]

    return lineas


de* obtener_logo_path():
    rutas_ba*e = [
        ROOT_DIR,
        APP_DIR,
        CWD_DIR,
    ]

    *ombres_directos = [
        "logo besco 2026.jpeg",
        "logo besco 2026.jpg",
        "logo besco 2026.png",
        "logo_besco_2026.jpeg",
        "logo_besco_2026.jpg",
        "logo_besco_2026.png",
        "logo.jpeg",
        "logo.jpg",
        "logo.png",
    ]

   *for ruta_base in rutas_base:
     *  for nombre in nombres_directos:
*           ruta_logo = os.path.joi*(ruta_base, nombre)

            i* os.path.exists(ruta_logo):
      *         return ruta_logo

    for*ruta_base in rutas_base:
        i* not os.path.exists(ruta_base):
  *         continue

        for car*eta_actual, _, archivos in os.walk*ruta_base):
            for archiv* in archivos:
                arch*vo_lower = archivo.lower()
       *        extension = os.path.splite*t(archivo_lower)[1]

             *  if extension in EXTENSIONES_LOGO*
                    if "logo" in *rchivo_lower or "besco" in archivo*lower:
                        ret*rn os.path.join(carpeta_actual, ar*hivo)

    return None


def crear*logo_temporal(ruta_logo):
    imag*n = Image.open(ruta_logo).convert(*RGB")
    imagen.thumbnail((1000, *000))

    temp_logo = tempfile.Na*edTemporaryFile(delete=False, suff*x=".jpg")
    temp_logo.close()

 *  imagen.save(
        temp_logo.n*me,
        format="JPEG",
       *quality=90,
        optimize=True
*   )

    return temp_logo.name


*ef comprimir_imagen_a_temp(uploade*_file):
    uploaded_file.seek(0)
*    imagen = Image.open(uploaded_f*le).convert("RGB")
    imagen.thum*nail(MAX_IMAGE_SIZE)

    temp_img*= tempfile.NamedTemporaryFile(dele*e=False, suffix=".jpg")
    temp_i*g.close()

    imagen.save(
      * temp_img.name,
        format="JP*G",
        quality=IMAGE_QUALITY,*        optimize=True
    )

    r*turn temp_img.name


def hay_fotos*en_item(evidencia):
    return any*
        [
            evidencia.get("antes_1") is not None,
        *   evidencia.get("antes_2") is not*None,
            evidencia.get("d*spues_1") is not None,
           *evidencia.get("despues_2") is not *one,
        ]
    )


def hay_fot*s_antes(evidencia):
    return any*
        [
            evidencia.get("antes_1") is not None,
        *   evidencia.get("antes_2") is not*None,
        ]
    )


def hay_fo*os_despues(evidencia):
    return *ny(
        [
            evidencia.get("despues_1") is not None,
   *        evidencia.get("despues_2")*is not None,
        ]
    )


# =*==================================*====================
# PDF
# =====*==================================*================
def encabezado_pd*(c, titulo):
    logo_path = obten*r_logo_path()
    logo_temp = None*
    title_x = MARGIN_LEFT
    tit*e_y = 750
    line_y = 700

    if*logo_path:
        try:
          * logo_temp = crear_logo_temporal(l*go_path)
            logo_reader =*ImageReader(logo_temp)

          * logo_w, logo_h = logo_reader.getS*ze()

            logo_max_w = 115*            logo_max_h = 45

     *      ratio = min(logo_max_w / log*_w, logo_max_h / logo_h)

        *   draw_w = logo_w * ratio
       *    draw_h = logo_h * ratio

     *      logo_x = MARGIN_LEFT
       *    logo_y = 715

            c.dr*wImage(
                logo_reade*,
                logo_x,
        *       logo_y,
                wid*h=draw_w,
                height=d*aw_h,
                preserveAspe*tRatio=True,
                mask=*auto"
            )

            t*tle_x = MARGIN_LEFT + 135

       *except Exception:
            titl*_x = MARGIN_LEFT

        finally:*            if logo_temp and os.pa*h.exists(logo_temp):
             *  try:
                    os.remo*e(logo_temp)
                excep* Exception:
                    pa*s

    c.setFillColor(colors.HexCo*or("#1E3A5F"))
    c.setFont("Helv*tica-Bold", 15)
    c.drawString(t*tle_x, title_y, normalizar_texto(t*tulo))

    c.setFillColor(colors.*exColor("#5B6573"))
    c.setFont(*Helvetica", 9)
    fecha_generado * datetime.now().strftime("%d/%m/%Y*%H:%M:%S")
    c.drawString(title_*, title_y - 18, f"Generado el {fec*a_generado}")

    c.setStrokeColo*(colors.HexColor("#D9E2EC"))
    c*line(MARGIN_LEFT, line_y, PDF_WIDT* - MARGIN_RIGHT, line_y)

    retu*n line_y - 25


def nueva_pagina(c* y, espacio=120):
    if y < espac*o:
        c.showPage()
        y * encabezado_pdf(c, "REPORTE FOTOGR*FICO - CONTINUACION")

    return *


def titulo_seccion(c, titulo, y*:
    y = nueva_pagina(c, y, 80)

*   c.setFont("Helvetica-Bold", 13)*    c.setFillColor(colors.HexColor*"#1E3A5F"))
    c.drawString(MARGI*_LEFT, y, normalizar_texto(titulo)*

    y -= 18

    return y


def *inea_pdf(c, etiqueta, valor, y):
 *  y = nueva_pagina(c, y, 70)

    *.setFont("Helvetica-Bold", 9)
    *.setFillColor(colors.HexColor("#1E*A5F"))
    c.drawString(MARGIN_LEF*, y, normalizar_texto(f"{etiqueta}*"))

    c.setFont("Helvetica", 9)*    c.setFillColor(colors.black)
 *  c.drawString(MARGIN_LEFT + 125, *, normalizar_texto(valor))

    y *= 15

    return y


def bloque_te*to_pdf(c, titulo, texto, y):
    y*= titulo_seccion(c, titulo, y)

  * c.setFont("Helvetica", 9)
    c.s*tFillColor(colors.black)

    for *inea in dividir_texto(texto):
    *   y = nueva_pagina(c, y, 70)
    *   c.drawString(MARGIN_LEFT, y, no*malizar_texto(linea))
        y -=*13

    y -= 10

    return y


de* dibujar_imagen_en_celda(c, upload*d_file, x, y, ancho, alto):
    te*p_path = None

    try:
        te*p_path = comprimir_imagen_a_temp(uploaded_file)
        img_reader = ImageReader(temp_path)

        img_w, img_h = img_reader.getSize()
        ratio = min(ancho / img_w, alto / img_h)

        draw_w = img_w * ratio
        draw_h = img_h * ratio

        x_img = x + (ancho - draw_w) / 2
        y_img = y + (alto - draw_h) / 2

        c.drawImage(
            img_reader,
            x_img,
            y_img,
            width=draw_w,
            height=draw_h,
            preserveAspectRatio=True,
            mask="auto"
        )

    except Exception:
        c.setStrokeColor(colors.HexColor("#B8C2CC"))
        c.setFillColor(colors.HexColor("#F4F6F8"))
        c.rect(x, y, ancho, alto, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#667085"))
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + ancho / 2, y + alto / 2, "Error imagen")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def fila_dos_fotos_pdf(c, titulo_izq, archivo_izq, titulo_der, archivo_der, y):
    if archivo_izq is None and archivo_der is None:
        return y

    alto_img = 145
    alto_total = alto_img + 38

    y = nueva_pagina(c, y, alto_total + MARGIN_BOTTOM)

    ancho_total = PDF_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    espacio = 18
    ancho_celda = (ancho_total - espacio) / 2

    x_izq = MARGIN_LEFT
    x_der = MARGIN_LEFT + ancho_celda + espacio

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1E3A5F"))

    if archivo_izq is not None:
        c.drawString(x_izq, y, normalizar_texto(titulo_izq))

    if archivo_der is not None:
        c.drawString(x_der, y, normalizar_texto(titulo_der))

    y_img = y - alto_img - 8

    if archivo_izq is not None:
        dibujar_imagen_en_celda(c, archivo_izq, x_izq, y_img, ancho_celda, alto_img)

    if archivo_der is not None:
        dibujar_imagen_en_celda(c, archivo_der, x_der, y_img, ancho_celda, alto_img)

    y = y_img - 18

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

    y = titulo_seccion(c, "Alcance y evidencias fotograficas", y)

    total_segmentos_con_foto = 0

    for item in alcance_items:
        numero = item["numero"]
        momento = item["momento"]
        actividad = item["actividad"]
        evidencia = evidencias_por_item.get(numero, {})

        if not hay_fotos_en_item(evidencia):
            continue

        total_segmentos_con_foto += 1

        y = nueva_pagina(c, y, 170)

        y = linea_pdf(c, "Renglon", str(numero), y)
        y = linea_pdf(c, "Momento", momento, y)
        y = bloque_texto_pdf(c, "Actividad critica", actividad, y)

        if hay_fotos_antes(evidencia):
            y = fila_dos_fotos_pdf(
                c,
                f"{momento} - Antes 1",
                evidencia.get("antes_1"),
                f"{momento} - Antes 2",
                evidencia.get("antes_2"),
                y
            )

        if hay_fotos_despues(evidencia):
            y = fila_dos_fotos_pdf(
                c,
                f"{momento} - Despues 1",
                evidencia.get("despues_1"),
                f"{momento} - Despues 2",
                evidencia.get("despues_2"),
                y
            )

    if total_segmentos_con_foto == 0:
        y = linea_pdf(c, "Evidencias", "No se adjuntaron fotografias.", y)

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

    logo_detectado = obtener_logo_path()

    if logo_detectado:
        st.success(f"Logo detectado para PDF: {os.path.basename(logo_detectado)}")
    else:
        st.warning("No se detecto logo BESCO en el repositorio. Verifica que el archivo del logo este en la raiz o en una carpeta del proyecto.")

    st.page_link(
        "portal.py",
        label="⬅️ Volver al portal",
        use_container_width=True
    )

    st.markdown(
        """
        <div class="info-box">
            Version ligera para celular. Todas las fotos son opcionales.
            En el PDF se acomodan dos fotos por fila y solo se muestran los segmentos que tengan fotografias.
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
                    En el PDF se mostraran dos fotos por fila.
                    Si este segmento no tiene fotos, no aparecera en el apartado fotografico del PDF.
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
