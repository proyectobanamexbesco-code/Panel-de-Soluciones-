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
        "destinatarios": ["gerardo.mendez@besco.mx"],
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
        "destinatarios": ["gerardo.mendez@besco.mx"],
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
# ALCANCES
# =========================================================
ALCANCES = [
    ("01_Electrico", "Instalaciones eléctricas y tableros"),
    ("02_Canceleria_Vidrieria", "Perfiles, cristales y herrajes"),
    ("03_Hidrosanitaria", "Acometida, bombeo, pluviales"),
    ("04_Mobiliario", "Mobiliario y cerrajería básica"),
    ("05_Generales", "Acabados, limpieza y reparaciones"),
    ("06.1_AA_Paquetes", "A/A integrales/paquetes"),
    ("06.2_AA_Divididos", "Mini-split/Fan & Coil"),
    ("06.3_Chillers_Manej", "Chillers/Manejadora"),
    ("06.4_Manejadoras_AireLav", "Manejadoras de aire lavado"),
    ("06.5_AA_menor_3TR", "Aire acondicionado menor a 3 TR"),
    ("07_UPS", "Revisión de UPS"),
    ("09_Depositos_Agua", "Cisternas y tinacos"),
    ("13_Reportes", "Gestión documental"),
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

    lim*io = str(nombre)

    for caracter*in invalidos:
        limpio = lim*io.replace(caracter, "_")

    lim*io = limpio.replace(" ", "_")

   *return limpio


def dividir_texto(*exto, max_chars=90):
    palabras * limpiar_texto(texto).split()
    *ineas = []
    linea_actual = ""

*   for palabra in palabras:
      * if len(linea_actual) + len(palabr*) + 1 <= max_chars:
            if*linea_actual:
                line*_actual += " " + palabra
         *  else:
                linea_actu*l = palabra
        else:
        *   lineas.append(linea_actual)
   *        linea_actual = palabra

  * if linea_actual:
        lineas.a*pend(linea_actual)

    return lin*as


def comprimir_imagen_a_temp(u*loaded_file):
    uploaded_file.se*k(0)

    imagen = Image.open(uplo*ded_file).convert("RGB")
    image*.thumbnail(MAX_IMAGE_SIZE)

    te*p_img = tempfile.NamedTemporaryFil*(delete=False, suffix=".jpg")
    *emp_img.close()

    imagen.save(
*       temp_img.name,
        form*t="JPEG",
        quality=IMAGE_QU*LITY,
        optimize=True
    )
*    return temp_img.name


def con*ar_archivos(archivos):
    if not *rchivos:
        return 0

    ret*rn len(archivos)


def mostrar_est*do(nombre, archivos):
    cantidad*= contar_archivos(archivos)

    i* cantidad == 0:
        st.caption*f"{nombre}: sin archivos cargados.*)
    elif cantidad <= MAX_FOTOS_P*R_SECCION:
        st.success(f"{n*mbre}: {cantidad} archivo(s) carga*o(s).")
    else:
        st.warni*g(
            f"{nombre}: {cantid*d} archivo(s) cargado(s). "
      *     f"Se integrarán máximo {MAX_F*TOS_POR_SECCION} para mantener lig*ro el PDF."
        )


def obtene*_descripcion(seccion):
    for sec* desc in ALCANCES:
        if sec *= seccion:
            return desc*
    return ""


# ===============*==================================*======
# PDF
# ===================*==================================*==
def encabezado_pdf(c, titulo):
*   y = 750

    c.setFillColor(col*rs.HexColor("#1E3A5F"))
    c.setF*nt("Helvetica-Bold", 15)
    c.dra*String(MARGIN_LEFT, y, limpiar_tex*o(titulo))

    y -= 18

    c.set*illColor(colors.HexColor("#5B6573"*)
    c.setFont("Helvetica", 9)
  * c.drawString(
        MARGIN_LEFT*
        y,
        f"Generado el *datetime.now().strftime('%d/%m/%Y *H:%M:%S')}"
    )

    y -= 20

  * c.setStrokeColor(colors.HexColor(*#D9E2EC"))
    c.line(MARGIN_LEFT,*y, PDF_WIDTH - MARGIN_RIGHT, y)

 *  y -= 25

    return y


def nuev*_pagina(c, y, espacio=120):
    if*y < espacio:
        c.showPage()
*       y = encabezado_pdf(c, "REPO*TE FOTOGRÁFICO - CONTINUACIÓN")

 *  return y


def titulo_seccion(c,*titulo, y):
    y = nueva_pagina(c* y, 80)

    c.setFont("Helvetica-*old", 13)
    c.setFillColor(color*.HexColor("#1E3A5F"))
    c.drawSt*ing(MARGIN_LEFT, y, limpiar_texto(*itulo))

    y -= 18

    return y*

def linea_pdf(c, etiqueta, valor* y):
    y = nueva_pagina(c, y, 70*

    c.setFont("Helvetica-Bold", *)
    c.setFillColor(colors.HexCol*r("#1E3A5F"))
    c.drawString(MAR*IN_LEFT, y, limpiar_texto(f"{etiqu*ta}:"))

    c.setFont("Helvetica"* 9)
    c.setFillColor(colors.blac*)
    c.drawString(MARGIN_LEFT + 1*5, y, limpiar_texto(valor))

    y*-= 15

    return y


def bloque_t*xto_pdf(c, titulo, texto, y):
    * = titulo_seccion(c, titulo, y)

 *  if not texto:
        texto = "S*n información capturada."

    c.s*tFont("Helvetica", 9)
    c.setFil*Color(colors.black)

    for linea*in dividir_texto(texto):
        y*= nueva_pagina(c, y, 70)
        c*drawString(MARGIN_LEFT, y, limpiar*texto(linea))
        y -= 13

   *y -= 10

    return y


def imagen*pdf(c, titulo, uploaded_file, y):
*   if uploaded_file is None:
     *  return y

    y = nueva_pagina(c* y, 240)

    c.setFont("Helvetica*Bold", 10)
    c.setFillColor(colo*s.HexColor("#1E3A5F"))
    c.drawS*ring(MARGIN_LEFT, y, limpiar_texto*titulo))

    y -= 10

    temp_pa*h = None

    try:
        temp_pa*h = comprimir_imagen_a_temp(upload*d_file)
        img_reader = Image*eader(temp_path)

        img_w, i*g_h = img_reader.getSize()

      * ancho_max = 250
        alto_max * 160

        ratio = min(ancho_ma* / img_w, alto_max / img_h)

     *  draw_w = img_w * ratio
        d*aw_h = img_h * ratio

        y -=*draw_h + 8

        c.drawImage(
 *          img_reader,
            *ARGIN_LEFT,
            y,
       *    width=draw_w,
            heig*t=draw_h,
            preserveAspe*tRatio=True,
            mask="aut*"
        )

        y -= 18

    *xcept Exception as error:
        *.setFont("Helvetica", 8)
        c*setFillColor(colors.red)
        c*drawString(
            MARGIN_LEF*,
            y - 20,
            *impiar_texto(f"No se pudo insertar*imagen: {error}")
        )
      * y -= 40

    finally:
        if *emp_path and os.path.exists(temp_p*th):
            try:
            *   os.remove(temp_path)
          * except Exception:
               *pass

    return y


def crear_pdf*
    contrato,
    folio,
    fech*_ejecucion,
    sucursal,
    dire*cion,
    ciudad,
    oficina,
   *tecnico,
    supervisor,
    tipo_*ervicio,
    estatus_final,
    se*cion,
    descripcion,
    activid*des,
    observaciones,
    df_mat*riales,
    evidencias,
    destin*tarios,
):
    temp_pdf = tempfile*NamedTemporaryFile(delete=False, s*ffix=".pdf")
    pdf_path = temp_p*f.name
    temp_pdf.close()

    c*= canvas.Canvas(pdf_path, pagesize*letter)

    y = encabezado_pdf(c,*"REPORTE FOTOGRÁFICO POR CONTRATO"*

    y = titulo_seccion(c, "Datos*generales", y)

    y = linea_pdf(*, "Contrato", contrato, y)
    y =*linea_pdf(c, "Folio / Ticket / OT"* folio, y)
    y = linea_pdf(c, "F*cha de ejecución", fecha_ejecucion*strftime("%d/%m/%Y"), y)
    y = l*nea_pdf(c, "Sucursal / Inmueble", *ucursal, y)
    y = linea_pdf(c, "*irección", direccion if direccion *lse "-", y)
    y = linea_pdf(c, "*iudad", ciudad if ciudad else "-",*y)
    y = linea_pdf(c, "Oficina r*sponsable", oficina if oficina els* "-", y)
    y = linea_pdf(c, "Téc*ico asignado", tecnico, y)
    y =*linea_pdf(c, "Supervisor", supervi*or if supervisor else "-", y)
    * = linea_pdf(c, "Tipo de servicio"* tipo_servicio, y)
    y = linea_p*f(c, "Estatus final", estatus_fina*, y)

    y -= 8

    y = titulo_s*ccion(c, "Alcance del servicio", y*
    y = linea_pdf(c, "Sección", s*ccion, y)
    y = linea_pdf(c, "De*cripción", descripcion, y)

    y * bloque_texto_pdf(c, "Actividades *ealizadas", actividades, y)

    i* df_materiales is not None and not*df_materiales.empty:
        y = t*tulo_seccion(c, "Materiales utiliz*dos", y)

        for _, row in df*materiales.iterrows():
           *cantidad = str(row.get("Cantidad",*"")).strip()
            descripci*n_material = str(row.get("Descripc*ón", "")).strip()

            if *escripcion_material:
             *  y = linea_pdf(
                 *  c,
                    "Material*,
                    f"{cantidad}*- {descripcion_material}",
       *            y
                )

 *      y -= 8

    y = bloque_texto*pdf(c, "Observaciones", observacio*es, y)

    y = titulo_seccion(c, *Evidencias fotográficas", y)

    *ay_evidencias = False

    for nom*re_evidencia, archivos in evidenci*s.items():
        if archivos:
  *         hay_evidencias = True

  *         for index, archivo in enu*erate(archivos[:MAX_FOTOS_POR_SECCION], start=1):
                if *asattr(archivo, "type") and archiv*.type == "application/pdf":
      *             y = linea_pdf(
      *                 c,
              *         nombre_evidencia,
       *                f"PDF adjunto regi*trado: {archivo.name}",
          *             y
                   *)
                else:
          *         y = imagen_pdf(
         *              c,
                 *      f"{nombre_evidencia} - Foto *index}",
                        a*chivo,
                        y
 *                  )

            i* len(archivos) > MAX_FOTOS_POR_SEC*ION:
                y = linea_pdf*
                    c,
          *         nombre_evidencia,
       *            f"Se integraron {MAX_F*TOS_POR_SECCION} de {len(archivos)* archivos.",
                    y*                )

    if not hay_*videncias:
        y = linea_pdf(c* "Evidencias", "No se adjuntaron e*idencias.", y)

    y = bloque_tex*o_pdf(
        c,
        "Destina*arios configurados",
        "\n".*oin(destinatarios) if destinatario* else "Sin destinatarios configura*os.",
        y
    )

    y = nue*a_pagina(c, y, 80)

    c.setStrok*Color(colors.HexColor("#D9E2EC"))
*   c.line(MARGIN_LEFT, y, PDF_WIDT* - MARGIN_RIGHT, y)

    y -= 18

*   c.setFont("Helvetica", 8)
    c*setFillColor(colors.HexColor("#7B8*94"))
    c.drawString(
        MA*GIN_LEFT,
        y,
        "Sist*ma Operativo - Grupo Besco | Repor*e generado automáticamente"
    )
*    c.save()

    return pdf_path
*
# ===============================*=========================
# CORREO*# ================================*========================
def envia*_correo(
    pdf_path,
    contrat*,
    folio,
    sucursal,
    ofi*ina,
    nombre_archivo,
    corre*s_extra,
    fecha_ejecucion,
    *estinatarios_base,
):
    try:
   *    if "EMAIL_SENDER" not in st.se*rets or "EMAIL_PASSWORD" not in st*secrets:
            return False,*"Faltan EMAIL_SENDER o EMAIL_PASSW*RD en Secrets."

        remitente*= st.secrets["EMAIL_SENDER"]
     *  password = st.secrets["EMAIL_PASSWORD"]

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
# VALIDACIÓN
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
# APP
# =========================================================
def main():
    aplicar_estilos()

    st.markdown(
        """
        <div class="titulo">📷 Reporte Fotográfico por Contrato</div>
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
            Versión ligera para celular. Primero genera el PDF, después descárgalo o envíalo por correo.
            Las fotos se comprimen automáticamente.
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
        "Fecha de ejecución",
        datetime.now()
    )

    sucursal = st.text_input("Sucursal / Inmueble")
    direccion = st.text_input("Dirección")
    ciudad = st.text_input("Ciudad")
    oficina = st.text_input("Oficina responsable")
    tecnico = st.text_input("Técnico asignado")
    supervisor = st.text_input("Supervisor")

    st.divider()

    st.subheader("2. Alcance")

    labels_alcances = [
        f"{seccion} - {descripcion}"
        for seccion, descripcion in ALCANCES
    ]

    alcance_label = st.selectbox(
        "Selecciona la sección del alcance",
        labels_alcances
    )

    seccion = alcance_label.split(" - ")[0].strip()
    descripcion = obtener_descripcion(seccion)

    st.markdown(
        f"""
        <div class="info-box">
            <strong>Sección:</strong> {seccion}<br>
            <strong>Descripción:</strong> {descripcion}
        </div>
        """,
        unsafe_allow_html=True
    )

    actividades_default = (
        f"Se ejecutan actividades correspondientes a la sección {seccion}: {descripcion}."
    )

    actividades = st.text_area(
        "Actividades realizadas",
        value=actividades_default,
        height=130
    )

    st.divider()

    st.subheader("3. Evidencias fotográficas")

    st.markdown(
        """
        <div class="warning-box">
            No se muestran vistas previas para mantener ligera la app.
            Se recomienda máximo 6 fotos por sección.
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
            pd.DataFrame(columns=["Cantidad", "Descripción"]),
            num_rows="dynamic",
            use_container_width=True
        )
    else:
        df_materiales = pd.DataFrame(columns=["Cantidad", "Descripción"])

    st.divider()

    st.subheader("5. Generar PDF y enviar correo")

    destinatarios_base = config["destinatarios"]

    if "gerardo.mendez@besco.mx" not in destinatarios_base:
        destinatarios_base.append("gerardo.mendez@besco.mx")

    st.info(f"Destinatarios automáticos: {', '.join(destinatarios_base)}")

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

    generar = st.button(
        "📄 Generar PDF",
        type="primary",
        use_container_width=True,
        disabled=not puede_generar
    )

    if generar:
        with st.spinner("Generando PDF y comprimiendo imágenes..."):
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
            Sistema Operativo - Grupo Besco | Reporte Fotográfico por Contrato
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
