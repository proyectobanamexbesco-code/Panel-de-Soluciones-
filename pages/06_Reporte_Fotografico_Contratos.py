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
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "Reporte Fotográfico por Contrato"
PAGE_ICON = "📷"
LAYOUT = "centered"

PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT = letter
PDF_MARGIN_LEFT = 45
PDF_MARGIN_RIGHT = 45

MAX_IMAGE_SIZE = (1000, 1000)
IMAGE_QUALITY = 65


# =========================================================
# CONFIGURAR PÁGINA
# =========================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT
)


# =========================================================
# CONFIGURACIÓN DE CONTRATOS
# =========================================================
CONTRATOS_CONFIG = {
    "Santander": {
        "destinatarios": [
            "gerardo.mendez@besco.mx"
        ],
        "tipos_servicio": [
            "Preventivo",
            "Correctivo",
            "Emergencia",
            "Visita técnica",
            "Levantamiento",
        ],
        "estatus": [
            "Servicio concluido",
            "Servicio concluido con observaciones",
            "Pendiente por material",
            "Pendiente por autorización",
            "No concluido",
        ],
    },
    "MacStore": {
        "destinatarios": [
            "gerardo.mendez@besco.mx"
        ],
        "tipos_servicio": [
            "Preventivo",
            "Correctivo",
            "Instalación",
            "Reparación",
            "Levantamiento",
        ],
        "estatus": [
            "Servicio concluido",
            "Servicio concluido con observaciones",
            "Pendiente por material",
            "Pendiente por autorización",
            "No concluido",
        ],
    },
    "Samsung": {
        "destinatarios": [
            "gerardo.mendez@besco.mx"
        ],
        "tipos_servicio": [
            "Diagnóstico",
            "Correctivo",
            "Instalación",
            "Validación",
            "Retiro",
            "Levantamiento",
        ],
        "estatus": [
            "Servicio concluido",
            "Servicio concluido con observaciones",
            "Pendiente por material",
            "Pendiente por autorización",
            "No concluido",
        ],
    },
}


# =========================================================
# ALCANCES / SECCIONES
# =========================================================
ALCANCES = [
    {
        "Seccion": "01_Electrico",
        "Descripcion": "Instalaciones eléctricas y tableros",
    },
    {
        "Seccion": "02_Canceleria_Vidrieria",
        "Descripcion": "Perfiles, cristales y herrajes",
    },
    {
        "Seccion": "03_Hidrosanitaria",
        "Descripcion": "Acometida, bombeo, pluviales",
    },
    {
        "Seccion": "04_Mobiliario",
        "Descripcion": "Mobiliario y cerrajería básica",
    },
    {
        "Seccion": "05_Generales",
        "Descripcion": "Acabados, limpieza y reparaciones",
    },
    {
        "Seccion": "06.1_AA_Paquetes",
        "Descripcion": "A/A integrales/paquetes",
    },
    {
        "Seccion": "06.2_AA_Divididos",
        "Descripcion": "Mini-split/Fan & Coil",
    },
    {
        "Seccion": "06.3_Chillers_Manej",
        "Descripcion": "Chillers/Manejadora",
    },
    {
        "Seccion": "06.4_Manejadoras_AireLav",
        "Descripcion": "Manejadoras de aire lavado",
    },
    {
        "Seccion": "06.5_AA_menor_3TR",
        "Descripcion": "Aire acondicionado menor a 3 TR",
    },
    {
        "Seccion": "07_UPS",
        "Descripcion": "Revisión de UPS",
    },
    {
        "Seccion": "09_Depositos_Agua",
        "Descripcion": "Cisternas y tinacos",
    },
    {
        "Seccion": "13_Reportes",
        "Descripcion": "Gestión documental",
    },
]


# =========================================================
# EVIDENCIAS
# =========================================================
EVIDENCIAS_OBLIGATORIAS = [
    "Fotos de fachada",
    "Fotos de acceso",
    "Fotos de área intervenida",
    "Antes",
    "Durante",
    "Después",
]

EVIDENCIAS_DOCUMENTALES = [
    "Folio / ticket",
]

EVIDENCIAS_OPCIONALES = [
    "Evidencia adicional",
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
# UTILIDADES
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


def limpiar_nombre_archivo(nombre: str) -> str:
    invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")", "&"]

    lim*io = nombre

    for caracter in i*validos:
        limpio = limpio.r*place(caracter, "_")

    limpio =*limpio.replace(" ", "_")

    retu*n limpio


def dividir_texto(texto* str, max_chars: int = 85) -> list*
    palabras = str(texto).split()*    lineas = []
    linea_actual =*""

    for palabra in palabras:
 *      if len(linea_actual) + len(p*labra) + 1 <= max_chars:
         *  if linea_actual:
               *linea_actual += " " + palabra
    *       else:
                linea*actual = palabra
        else:
   *        lineas.append(linea_actual*
            linea_actual = palabr*

    if linea_actual:
        lin*as.append(linea_actual)

    retur* lineas


def obtener_descripcion_*lcance(seccion: str) -> str:
    f*r alcance in ALCANCES:
        if *lcance["Seccion"] == seccion:
    *       return alcance["Descripcion"]

    return ""


def obtener_alc*nce_label(alcance: dict) -> str:
 *  return f"{alcance['Seccion']} - *alcance['Descripcion']}"


def obt*ner_seccion_desde_label(label: str* -> str:
    if " - " in label:
  *     return label.split(" - ")[0].*trip()

    return label.strip()

*def contar_archivos(archivos) -> i*t:
    if not archivos:
        re*urn 0

    return len(archivos)


*ef mostrar_estado_archivos(nombre:*str, archivos) -> None:
    cantid*d = contar_archivos(archivos)

   *if cantidad == 0:
        st.capti*n(f"{nombre}: sin archivos cargado*.")
    elif cantidad <= 6:
      * st.success(f"{nombre}: {cantidad}*archivo(s) cargado(s).")
    else:*        st.warning(
            f"*nombre}: {cantidad} archivo(s) car*ado(s). "
            "Para celula* se recomienda máximo 6 fotos por *ección."
        )


def comprimir*imagen_a_temp(uploaded_file) -> st*:
    uploaded_file.seek(0)

    i*age = Image.open(uploaded_file)

 *  if image.mode in ("RGBA", "P"):
*       image = image.convert("RGB"*
    else:
        image = image.c*nvert("RGB")

    image.thumbnail(*AX_IMAGE_SIZE)

    temp_img = tem*file.NamedTemporaryFile(delete=Fal*e, suffix=".jpg")
    temp_img.clo*e()

    image.save(
        temp_*mg.name,
        format="JPEG",
  *     quality=IMAGE_QUALITY,
      * optimize=True
    )

    return t*mp_img.name


# ==================*==================================*===
# PDF - FUNCIONES
# ==========*==================================*===========
def dibujar_encabezado*pdf(c: canvas.Canvas, titulo: str)*-> int:
    y = 750

    c.setFill*olor(colors.HexColor("#1E3A5F"))
 *  c.setFont("Helvetica-Bold", 15)
*   c.drawString(45, y, limpiar_tex*o(titulo))

    y -= 18

    c.set*illColor(colors.HexColor("#5B6573"*)
    c.setFont("Helvetica", 9)
  * c.drawString(
        45,
       *y,
        limpiar_texto(f"Generad* el {datetime.now().strftime('%d/%*/%Y %H:%M:%S')}")
    )

    y -= *0

    c.setStrokeColor(colors.Hex*olor("#D9E2EC"))
    c.line(45, y,*PDF_PAGE_WIDTH - 45, y)

    y -= *5

    return y


def nueva_pagina*si_necesaria(c: canvas.Canvas, y: *nt, espacio_requerido: int = 120) *> int:
    if y < espacio_requerid*:
        c.showPage()
        y =*dibujar_encabezado_pdf(c, "REPORTE*FOTOGRÁFICO - CONTINUACIÓN")

    *eturn y


def escribir_titulo_secc*on(c: canvas.Canvas, titulo: str, *: int) -> int:
    y = nueva_pagin*_si_necesaria(c, y, 80)

    c.set*ont("Helvetica-Bold", 13)
    c.se*FillColor(colors.HexColor("#1E3A5F*))
    c.drawString(45, y, limpiar*texto(titulo))

    y -= 18

    r*turn y


def escribir_linea_pdf(c:*canvas.Canvas, etiqueta: str, valo*: str, y: int) -> int:
    y = nue*a_pagina_si_necesaria(c, y, 70)

 *  c.setFont("Helvetica-Bold", 9)
 *  c.setFillColor(colors.HexColor("*1E3A5F"))
    c.drawString(45, y, *impiar_texto(f"{etiqueta}:"))

   *c.setFont("Helvetica", 9)
    c.se*FillColor(colors.black)
    c.draw*tring(170, y, limpiar_texto(str(va*or)))

    y -= 15

    return y

*def escribir_bloque_texto_pdf(c: c*nvas.Canvas, titulo: str, texto: s*r, y: int) -> int:
    y = escribi*_titulo_seccion(c, titulo, y)

   *if not texto:
        texto = "Sin*información capturada."

    c.set*ont("Helvetica", 9)
    c.setFillC*lor(colors.black)

    lineas = di*idir_texto(texto, max_chars=90)

 *  for linea in lineas:
        y =*nueva_pagina_si_necesaria(c, y, 70*
        c.drawString(45, y, limpi*r_texto(linea))
        y -= 13

 *  y -= 10

    return y


def dibu*ar_imagen_pdf(c: canvas.Canvas, ti*ulo: str, uploaded_file, y: int) -* int:
    if uploaded_file is None*
        return y

    y = nueva_p*gina_si_necesaria(c, y, 240)

    *.setFont("Helvetica-Bold", 10)
   *c.setFillColor(colors.HexColor("#1*3A5F"))
    c.drawString(45, y, li*piar_texto(titulo))

    y -= 10

*   temp_path = None

    try:
    *   temp_path = comprimir_imagen_a_*emp(uploaded_file)
        image_r*ader = ImageReader(temp_path)

   *    img_width, img_height = image_*eader.getSize()

        ancho_max*= 250
        alto_max = 160

    *   ratio = min(ancho_max / img_wid*h, alto_max / img_height)

       *draw_width = img_width * ratio
   *    draw_height = img_height * rat*o

        y -= draw_height + 8

 *      c.drawImage(
            ima*e_reader,
            45,
        *   y,
            width=draw_width*
            height=draw_height,
 *          preserveAspectRatio=True*
            mask="auto"
        )*
        y -= 18

    except Excep*ion as error:
        c.setFont("H*lvetica", 8)
        c.setFillColo*(colors.red)
        c.drawString(*5, y - 20, limpiar_texto(f"No se p*do insertar imagen: {error}"))
   *    y -= 40

    finally:
        *f temp_path and os.path.exists(tem*_path):
            try:
         *      os.remove(temp_path)
       *    except Exception:
            *   pass

    return y


def crear_*df_reporte(
    contrato: str,
   *folio: str,
    fecha_ejecucion,
 *  sucursal: str,
    direccion: st*,
    ciudad: str,
    oficina: st*,
    tecnico: str,
    supervisor* str,
    tipo_servicio: str,
    *status_final: str,
    seccion: st*,
    descripcion: str,
    activi*ades: str,
    observaciones: str,*    df_materiales: pd.DataFrame,
 *  evidencias: dict,
    destinatar*os: list,
) -> str:
    temp_pdf =*tempfile.NamedTemporaryFile(delete*False, suffix=".pdf")
    pdf_path*= temp_pdf.name
    temp_pdf.close*)

    c = canvas.Canvas(pdf_path,*pagesize=letter)

    y = dibujar_*ncabezado_pdf(c, "REPORTE FOTOGRÁF*CO POR CONTRATO")

    y = escribi*_titulo_seccion(c, "Datos generale*", y)

    y = escribir_linea_pdf(*, "Contrato", contrato, y)
    y =*escribir_linea_pdf(c, "Folio / Tic*et / OT", folio, y)
    y = escrib*r_linea_pdf(c, "Fecha de ejecución*, fecha_ejecucion.strftime("%d/%m/*Y"), y)
    y = escribir_linea_pdf*c, "Sucursal / Inmueble", sucursal* y)
    y = escribir_linea_pdf(c, *Dirección", direccion if direccion*else "-", y)
    y = escribir_line*_pdf(c, "Ciudad", ciudad if ciudad*else "-", y)
    y = escribir_line*_pdf(c, "Oficina responsable", ofi*ina if oficina else "-", y)
    y * escribir_linea_pdf(c, "Técnico as*gnado", tecnico, y)
    y = escrib*r_linea_pdf(c, "Supervisor", super*isor if supervisor else "-", y)
  * y = escribir_linea_pdf(c, "Tipo d* servicio", tipo_servicio, y)
    * = escribir_linea_pdf(c, "Estatus *inal", estatus_final, y)

    y -=*8

    y = escribir_titulo_seccion*c, "Alcance del servicio", y)

   *y = escribir_linea_pdf(c, "Sección*, seccion, y)
    y = escribir_lin*a_pdf(c, "Descripción", descripcio*, y)

    y = escribir_bloque_text*_pdf(c, "Actividades realizadas", *ctividades, y)

    if df_material*s is not None and not df_materiale*.empty:
        y = escribir_titul*_seccion(c, "Materiales utilizados*, y)

        for _, row in df_mat*riales.iterrows():
            can*idad = str(row.get("Cantidad", "")*.strip()
            descripcion_m*t = str(row.get("Descripción", "")*.strip()

            if descripci*n_mat:
                y = escribi*_linea_pdf(
                    c,*                    "Material",
  *                 f"{cantidad} - {d*scripcion_mat}",
                 *  y
                )

        y -* 8

    y = escribir_bloque_texto_*df(c, "Observaciones", observacion*s, y)

    y = escribir_titulo_sec*ion(c, "Evidencias fotográficas", *)

    hay_evidencias = False

   *for nombre_evidencia, archivos in *videncias.items():
        if arch*vos:
            hay_evidencias = *rue

            for index, archiv* in enumerate(archivos[:6], start=*):
                if hasattr(arch*vo, "type") and archivo.type == "a*plication/pdf":
                  * y = escribir_linea_pdf(
         *              c,
                 *      nombre_evidencia,
          *             f"PDF adjunto registr*do: {archivo.name}",
             *          y
                    )
*               else:
             *      y = dibujar_imagen_pdf(
    *                   c,
            *           f"{nombre_evidencia} - *oto {index}",
                    *   archivo,
                      * y
                    )

        *   if len(archivos) > 6:
         *      y = escribir_linea_pdf(
    *               c,
                *   nombre_evidencia,
             *      f"Se integraron 6 de {len(ar*hivos)} archivos para mantener el *DF ligero.",
                    y*                )

    if not hay_*videncias:
        y = escribir_li*ea_pdf(c, "Evidencias", "No se adj*ntaron evidencias.", y)

    y = e*cribir_bloque_texto_pdf(
        c*
        "Destinatarios configurad*s",
        "\n".join(destinatario*) if destinatarios else "Sin desti*atarios configurados.",
        y
*   )

    y = nueva_pagina_si_nece*aria(c, y, 80)

    c.setStrokeCol*r(colors.HexColor("#D9E2EC"))
    *.line(45, y, PDF_PAGE_WIDTH - 45, *)

    y -= 18

    c.setFont("Hel*etica", 8)
    c.setFillColor(colo*s.HexColor("#7B8794"))
    c.drawS*ring(
        45,
        y,
     *  "Sistema Operativo - Grupo Besco*| Reporte generado automáticamente*
    )

    c.save()

    return p*f_path


# =======================*=================================
* CORREO
# ========================*================================
d*f enviar_correo_reporte(
    pdf_p*th: str,
    contrato: str,
    fo*io: str,
    sucursal: str,
    of*cina: str,
    nombre_archivo: str*
    correos_extra: str,
    fecha*ejecucion: str,
    lista_destinat*rios: list,
) -> tuple:
    try:
 *      if "EMAIL_SENDER" not in st.*ecrets or "EMAIL_PASSWORD" not in *t.secrets:
            return (
  *             False,
              * "Faltan EMAIL_SENDER o EMAIL_PASS*ORD en Secrets."
            )

  *     remitente = st.secrets["EMAIL_SENDER"]
        password = st.sec*ets["EMAIL_PASSWORD"]

        ext*a = []

        if correos_extra:
            extra = [
                c.strip()
                for c in correos_extra.split(",")
                if c.strip()
            ]

        destinatarios = list(set(lista_destinatarios + extra))

        msg = EmailMessage()
        msg["Subject"] = limpiar_texto(
            f"Reporte Fotográfico BESCO: {contrato} | TK: {folio} | Of: {oficina}"
        )
        msg["From"] = remitente
        msg["To"] = ", ".join(destinatarios)

        msg.set_content(
            limpiar_texto(
                f"Se ha generado un nuevo reporte fotográfico desde el Portal de Soluciones BESCO.\n\n"
                f"Contrato: {contrato}\n"
                f"Fecha de ejecución: {fecha_ejecucion}\n"
                f"Oficina: {oficina}\n"
                f"Folio / Ticket / OT: {folio}\n"
                f"Sucursal / Inmueble: {sucursal}\n\n"
                f"Se adjunta el PDF del reporte."
            )
        )

        with open(pdf_path, "rb") as file:
            msg.add_attachment(
                file.read(),
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
# VALIDACIÓN
# =========================================================
def validar_campos_obligatorios(
    contrato: str,
    folio: str,
    sucursal: str,
    tecnico: str,
    seccion: str,
    actividades: str,
    evidencias: dict,
) -> list:
    faltantes = []

    if not contrato:
        faltantes.append("Contrato")

    if not folio.strip():
        faltantes.append("Folio / Ticket / OT")

    if not sucursal.strip():
        faltantes.append("Sucursal / Inmueble")

    if not tecnico.strip():
        faltantes.append("Técnico asignado")

    if not seccion:
        faltantes.append("Sección / Alcance")

    if not actividades.strip():
        faltantes.append("Actividades realizadas")

    for evidencia in EVIDENCIAS_OBLIGATORIAS:
        if not evidencias.get(evidencia):
            faltantes.append(evidencia)

    return faltantes


# =========================================================
# INTERFAZ PRINCIPAL
# =========================================================
def main() -> None:
    aplicar_estilos_ligeros()

    st.markdown(
        """
        <div class="main-title">📷 Reporte Fotográfico por Contrato</div>
        <div class="subtitle">
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
            Versión ligera para celular: primero genera el PDF, después descárgalo o envíalo por correo.
            Las fotos se comprimen automáticamente para reducir el peso del reporte.
        </div>
        """,
        unsafe_allow_html=True
    )

    if "contrato_reporte" not in st.session_state:
        st.session_state["contrato_reporte"] = {}

    form_state = st.session_state["contrato_reporte"]

    paso = st.radio(
        "Sección",
        [
            "1. Datos generales",
            "2. Alcance",
            "3. Evidencias",
            "4. Observaciones y materiales",
            "5. PDF y correo",
        ],
        horizontal=False
    )

    contratos = list(CONTRATOS_CONFIG.keys())

    if paso == "1. Datos generales":
        st.markdown(
            '<div class="section-title">1. Datos generales</div>',
            unsafe_allow_html=True
        )

        contrato_actual = form_state.get("contrato", contratos[0])

        contrato = st.selectbox(
            "Contrato",
            contratos,
            index=contratos.index(contrato_actual) if contrato_actual in contratos else 0
        )

        form_state["contrato"] = contrato

        config_contrato = CONTRATOS_CONFIG[contrato]

        tipo_servicio_actual = form_state.get(
            "tipo_servicio",
            config_contrato["tipos_servicio"][0]
        )

        tipo_servicio = st.selectbox(
            "Tipo de servicio",
            config_contrato["tipos_servicio"],
            index=config_contrato["tipos_servicio"].index(tipo_servicio_actual)
            if tipo_servicio_actual in config_contrato["tipos_servicio"]
            else 0
        )

        estatus_actual = form_state.get(
            "estatus_final",
            config_contrato["estatus"][0]
        )

        estatus_final = st.selectbox(
            "Estatus final",
            config_contrato["estatus"],
            index=config_contrato["estatus"].index(estatus_actual)
            if estatus_actual in config_contrato["estatus"]
            else 0
        )

        form_state["tipo_servicio"] = tipo_servicio
        form_state["estatus_final"] = estatus_final

        form_state["folio"] = st.text_input(
            "Folio / Ticket / OT",
            value=form_state.get("folio", ""),
            max_chars=40
        )

        form_state["fecha_ejecucion"] = st.date_input(
            "Fecha de ejecución",
            value=form_state.get("fecha_ejecucion", datetime.now())
        )

        form_state["sucursal"] = st.text_input(
            "Sucursal / Inmueble",
            value=form_state.get("sucursal", "")
        )

        form_state["direccion"] = st.text_input(
            "Dirección",
            value=form_state.get("direccion", "")
        )

        form_state["ciudad"] = st.text_input(
            "Ciudad",
            value=form_state.get("ciudad", "")
        )

        form_state["oficina"] = st.text_input(
            "Oficina responsable",
            value=form_state.get("oficina", "")
        )

        form_state["tecnico"] = st.text_input(
            "Técnico asignado",
            value=form_state.get("tecnico", "")
        )

        form_state["supervisor"] = st.text_input(
            "Supervisor",
            value=form_state.get("supervisor", "")
        )

        st.success("Datos generales guardados temporalmente.")

    elif paso == "2. Alcance":
        st.markdown(
            '<div class="section-title">2. Alcance / Sección del servicio</div>',
            unsafe_allow_html=True
        )

        labels_alcances = [obtener_alcance_label(a) for a in ALCANCES]

        seccion_actual = form_state.get("seccion", ALCANCES[0]["Seccion"])

        label_actual = labels_alcances[0]

        for label in labels_alcances:
            if label.startswith(seccion_actual):
                label_actual = label
                break

        alcance_label = st.selectbox(
            "Selecciona la sección del alcance",
            labels_alcances,
            index=labels_alcances.index(label_actual)
        )

        seccion = obtener_seccion_desde_label(alcance_label)
        descripcion = obtener_descripcion_alcance(seccion)

        form_state["seccion"] = seccion
        form_state["descripcion"] = descripcion

        st.markdown(
            f"""
            <div class="info-box">
                <strong>Sección:</strong> {seccion}<br>
                <strong>Descripción de ejecución:</strong> {descripcion}
            </div>
            """,
            unsafe_allow_html=True
        )

        texto_base = (
            f"Se ejecutan actividades correspondientes a la sección {seccion}: "
            f"{descripcion}."
        )

        form_state["actividades"] = st.text_area(
            "Actividades realizadas",
            value=form_state.get("actividades", texto_base),
            height=140
        )

        st.success("Alcance guardado temporalmente.")

    elif paso == "3. Evidencias":
        st.markdown(
            '<div class="section-title">3. Evidencias fotográficas</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="warning-box">
                Para mantener ligera la app en celular, no se muestran vistas previas.
                Se recomienda máximo 6 fotos por sección.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### Evidencias obligatorias")

        for evidencia in EVIDENCIAS_OBLIGATORIAS:
            archivos = st.file_uploader(
                evidencia,
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"evidencia_{evidencia}"
            )

            mostrar_estado_archivos(evidencia, archivos)

        st.markdown("### Evidencia documental")

        for evidencia in EVIDENCIAS_DOCUMENTALES:
            archivos = st.file_uploader(
                evidencia,
                type=["jpg", "jpeg", "png", "pdf"],
                accept_multiple_files=True,
                key=f"evidencia_{evidencia}"
            )

            mostrar_estado_archivos(evidencia, archivos)

        st.markdown("### Evidencias opcionales")

        for evidencia in EVIDENCIAS_OPCIONALES:
            archivos = st.file_uploader(
                evidencia,
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"evidencia_{evidencia}"
            )

            mostrar_estado_archivos(evidencia, archivos)

        st.success("Evidencias cargadas temporalmente.")

    elif paso == "4. Observaciones y materiales":
        st.markdown(
            '<div class="section-title">4. Observaciones y materiales</div>',
            unsafe_allow_html=True
        )

        form_state["observaciones"] = st.text_area(
            "Observaciones",
            value=form_state.get("observaciones", ""),
            height=130
        )

        usar_materiales = st.checkbox(
            "Agregar materiales utilizados",
            value=form_state.get("usar_materiales", False)
        )

        form_state["usar_materiales"] = usar_materiales

        if usar_materiales:
            df_materiales = st.data_editor(
                pd.DataFrame(
                    form_state.get(
                        "materiales",
                        [{"Cantidad": "", "Descripción": ""}]
                    )
                ),
                num_rows="dynamic",
                use_container_width=True
            )

            form_state["materiales"] = df_materiales.to_dict(orient="records")
        else:
            form_state["materiales"] = []

        st.success("Observaciones/materiales guardados temporalmente.")

    elif paso == "5. PDF y correo":
        st.markdown(
            '<div class="section-title">5. Generar PDF y enviar correo</div>',
            unsafe_allow_html=True
        )

        contrato = form_state.get("contrato", "")
        folio = form_state.get("folio", "")
        fecha_ejecucion = form_state.get("fecha_ejecucion", datetime.now())
        sucursal = form_state.get("sucursal", "")
        direccion = form_state.get("direccion", "")
        ciudad = form_state.get("ciudad", "")
        oficina = form_state.get("oficina", "")
        tecnico = form_state.get("tecnico", "")
        supervisor = form_state.get("supervisor", "")
        tipo_servicio = form_state.get("tipo_servicio", "")
        estatus_final = form_state.get("estatus_final", "")
        seccion = form_state.get("seccion", "")
        descripcion = form_state.get("descripcion", "")
        actividades = form_state.get("actividades", "")
        observaciones = form_state.get("observaciones", "")

        materiales = form_state.get("materiales", [])

        if materiales:
            df_materiales = pd.DataFrame(materiales)
        else:
            df_materiales = pd.DataFrame(columns=["Cantidad", "Descripción"])

        evidencias = {}

        todas_evidencias = (
            EVIDENCIAS_OBLIGATORIAS
            + EVIDENCIAS_DOCUMENTALES
            + EVIDENCIAS_OPCIONALES
        )

        for evidencia in todas_evidencias:
            key = f"evidencia_{evidencia}"
            evidencias[evidencia] = st.session_state.get(key, [])

        faltantes = validar_campos_obligatorios(
            contrato=contrato,
            folio=folio,
            sucursal=sucursal,
            tecnico=tecnico,
            seccion=seccion,
            actividades=actividades,
            evidencias=evidencias,
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
                    Datos mínimos completos. Puedes generar el PDF.
                </div>
                """,
                unsafe_allow_html=True
            )

        permitir_incompleto = st.checkbox(
            "Permitir generar PDF aunque falten campos/evidencias obligatorias",
            value=True
        )

        puede_generar = permitir_incompleto or not faltantes

        contrato_config = CONTRATOS_CONFIG.get(
            contrato,
            {"destinatarios": ["gerardo.mendez@besco.mx"]}
        )

        destinatarios_base = contrato_config.get(
            "destinatarios",
            ["gerardo.mendez@besco.mx"]
        )

        if "gerardo.mendez@besco.mx" not in destinatarios_base:
            destinatarios_base.append("gerardo.mendez@besco.mx")

        st.info(f"Destinatarios automáticos: {', '.join(destinatarios_base)}")

        correos_extra = st.text_input(
            "Correos adicionales separados por coma",
            value=form_state.get("correos_extra", "")
        )

        form_state["correos_extra"] = correos_extra

        generar = st.button(
            "📄 Generar PDF",
            type="primary",
            use_container_width=True,
            disabled=not puede_generar
        )

        if generar:
            with st.spinner("Generando PDF y comprimiendo imágenes..."):
                try:
                    pdf_path = crear_pdf_reporte(
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

                    st.session_state["contrato_pdf_path"] = pdf_path
                    st.session_state["contrato_nombre_pdf"] = nombre_pdf
                    st.session_state["contrato_fecha_str"] = fecha_ejecucion.strftime("%d/%m/%Y")
                    st.session_state["contrato_destinatarios"] = destinatarios_base
                    st.session_state["contrato_correo_extra"] = correos_extra
                    st.session_state["contrato_email_data"] = {
                        "contrato": contrato,
                        "folio": folio,
                        "sucursal": sucursal,
                        "oficina": oficina,
                    }

                    st.success("PDF generado correctamente.")

                except Exception as error:
                    st.error(f"No se pudo generar el PDF: {error}")
                    st.exception(error)

        if "contrato_pdf_path" in st.session_state:
            pdf_path = st.session_state["contrato_pdf_path"]
            nombre_pdf = st.session_state["contrato_nombre_pdf"]

            with open(pdf_path, "rb") as file:
                st.download_button(
                    "⬇️ Descargar PDF",
                    data=file,
                    file_name=nombre_pdf,
                    mime="application/pdf",
                    use_container_width=True
                )

            st.markdown(
                """
                <div class="info-box">
                    El PDF ya fue generado. Si tienes buena conexión, puedes enviarlo por correo.
                    Si falla el correo, descarga el PDF y compártelo manualmente.
                </div>
                """,
                unsafe_allow_html=True
            )

            enviar = st.button(
                "📨 Enviar reporte por correo",
                use_container_width=True
            )

            if enviar:
                email_data = st.session_state["contrato_email_data"]

                with st.spinner("Enviando correo..."):
                    enviado, mensaje = enviar_correo_reporte(
                        pdf_path=st.session_state["contrato_pdf_path"],
                        contrato=email_data["contrato"],
                        folio=email_data["folio"],
                        sucursal=email_data["sucursal"],
                        oficina=email_data["oficina"],
                        nombre_archivo=st.session_state["contrato_nombre_pdf"],
                        correos_extra=st.session_state["contrato_correo_extra"],
                        fecha_ejecucion=st.session_state["contrato_fecha_str"],
                        lista_destinatarios=st.session_state["contrato_destinatarios"],
                    )

                if enviado:
                    st.success(mensaje)
                else:
                    st.warning(mensaje)

    st.divider()

    st.markdown(
        """
        <div class="footer-text">
            Sistema Operativo - Grupo Besco | Reporte Fotográfico por Contrato
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
