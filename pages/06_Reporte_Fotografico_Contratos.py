import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import smtplib
from email.message import EmailMessage
import io
import tempfile
import contextlib
from pypdf import PdfWriter


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "Reporte Fotográfico por Contrato"
PAGE_ICON = "📷"
LAYOUT = "centered"

MAX_FOTOS_RECOMENDADAS = 6
MAX_IMAGE_SIZE = (1100, 1100)
IMAGE_QUALITY = 65

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGO_PATH = os.path.join(ROOT_DIR, "logo besco 2026.jpeg")


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
def limpiar_texto(texto):
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
        "é": "e",
        "É": "E",
        "á": "a",
        "Á": "A",
        "í": "i",
        "Í": "I",
        "ó": "o",
        "Ó": "O",
        "ú": "u",
        "Ú": "U",
        "ñ": "n",
        "Ñ": "N",
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    return texto.encode("latin-1", "replace").decode("latin-1")


def limpiar_nombre_archivo(nombre: str) -> str:
    invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")", "&"]

    lim*io = nombre

    for caracter in i*validos:
        limpio = limpio.r*place(caracter, "_")

    limpio =*limpio.replace(" ", "_")

    retu*n limpio


@contextlib.contextmana*er
def archivo_temporal(suffix=".j*g"):
    tmp = tempfile.NamedTempo*aryFile(delete=False, suffix=suffi*)
    tmp.close()

    try:
      * yield tmp.name
    finally:
     *  with contextlib.suppress(FileNot*oundError):
            os.remove(*mp.name)


def comprimir_imagen_a_*emp(file_obj, max_size=MAX_IMAGE_S*ZE, quality=IMAGE_QUALITY):
    fi*e_obj.seek(0)

    img = Image.ope*(file_obj).convert("RGB")
    img.*humbnail(max_size)

    tmp = temp*ile.NamedTemporaryFile(delete=Fals*, suffix=".jpg")
    tmp.close()

*   img.save(
        tmp.name,
   *    format="JPEG",
        quality*quality,
        optimize=True
   *)

    return tmp.name


def conta*_archivos(archivos) -> int:
    if*not archivos:
        return 0

  * return len(archivos)


def mostra*_estado_archivos(nombre: str, arch*vos) -> None:
    cantidad = conta*_archivos(archivos)

    if cantid*d == 0:
        st.caption(f"{nomb*e}: sin archivos cargados.")
    e*if cantidad <= MAX_FOTOS_RECOMENDA*AS:
        st.success(f"{nombre}:*{cantidad} archivo(s) cargado(s)."*
    else:
        st.warning(
   *        f"{nombre}: {cantidad} arc*ivo(s) cargado(s). "
            f*Para celular se recomienda máximo *MAX_FOTOS_RECOMENDADAS}."
        *


def obtener_descripcion_alcance*seccion: str) -> str:
    for alca*ce in ALCANCES:
        if alcance*"Seccion"] == seccion:
           *return alcance["Descripcion"]

   *return ""


def obtener_alcance_la*el(alcance: dict) -> str:
    retu*n f"{alcance['Seccion']} - {alcanc*['Descripcion']}"


def obtener_se*cion_desde_label(label: str) -> st*:
    if " - " in label:
        r*turn label.split(" - ")[0].strip()*
    return label.strip()


# ====*==================================*=================
# PDF
# ========*==================================*=============
class ReporteContrat*PDF(FPDF):
    def __init__(self):*        super().__init__()
       *self.section_count = 1
        sel*.set_auto_page_break(auto=True, ma*gin=25)
        self.set_margins(l*ft=12, top=12, right=12)

    def *eader(self):
        try:
        *   if os.path.exists(LOGO_PATH):
 *              img_logo = Image.ope*(LOGO_PATH).convert("RGB")
       *        orig_w, orig_h = img_logo.*ize
                final_h = 18
 *              final_w = orig_w * (*inal_h / orig_h)

                *ith archivo_temporal(suffix=".jpg"* as tmp_logo:
                    *mg_logo.thumbnail((800, 800))
    *               img_logo.save(tmp_l*go, format="JPEG", quality=75, opt*mize=True)
                    sel*.image(tmp_logo, x=12, y=8, w=fina*_w, h=final_h)
        except Exce*tion:
            pass

        se*f.set_font("Arial", "B", 11)
     *  self.set_text_color(30, 58, 95)
*       self.set_xy(0, 10)
        *elf.cell(
            self.w - 12,*            6,
            limpiar*texto("REPORTE FOTOGRAFICO POR CON*RATO"),
            0,
           *1,
            "R"
        )

    *   self.set_font("Arial", "", 8)
 *      self.set_text_color(120, 120* 120)
        self.set_x(0)
      * self.cell(
            self.w - 1*,
            5,
            limpi*r_texto(f"Emision: {datetime.now()*strftime('%d/%m/%Y %H:%M')}"),
   *        0,
            1,
        *   "R"
        )

        self.set*draw_color(226, 24, 54)
        se*f.set_line_width(0.6)
        self*line(12, 31, self.w - 12, 31)
    *   self.set_line_width(0.2)
      * self.set_draw_color(0, 0, 0)
    *   self.ln(24)

    def footer(sel*):
        self.set_y(-15)
       *self.set_draw_color(200, 200, 200)*        self.line(12, self.get_y()* self.w - 12, self.get_y())

     *  self.set_font("Arial", "I", 8)
 *      self.set_text_color(150, 150* 150)
        self.cell(
         *  0,
            8,
            li*piar_texto(f"Pagina {self.page_no(*} | Documento confidencial BESCO")*
            0,
            0,
   *        "C"
        )

    def add*custom_section(self, title):
     *  if self.get_y() > 245:
         *  self.add_page()

        self.se*_fill_color(30, 58, 95)
        se*f.set_font("Arial", "B", 10)
     *  self.set_text_color(255, 255, 25*)

        self.cell(4, 8, "", 0, *, "L", fill=True)

        self.se*_fill_color(226, 24, 54)
        s*lf.cell(2, 8, "", 0, 0, "L", fill=*rue)

        self.set_fill_color(*0, 58, 95)
        self.cell(
    *       self.w - 30,
            8,*            limpiar_texto(f"  {sel*.section_count}. {title.upper()}")*
            0,
            1,
   *        "L",
            fill=True*        )

        self.section_co*nt += 1
        self.ln(3)
       *self.set_text_color(0, 0, 0)

    *ef tabla_info(self, datos):
        self.set_font("Arial", "", 9)

        col_label = 52
        col_valor = self.w - 24 - col_label

        for etiqueta, valor in datos:
            self.set_font("Arial", "B", 9)
            self.set_fill_color(240, 243, 248)
            self.cell(col_label, 7, limpiar_texto(etiqueta), 1, 0, "L", fill=True)

            self.set_font("Arial", "", 9)
            self.set_fill_color(255, 255, 255)
            self.cell(col_valor, 7, limpiar_texto(str(valor)), 1, 1, "L", fill=True)

        self.ln(3)

    def bloque_texto(self, etiqueta, contenido, color_fondo=(248, 248, 252)):
        if not contenido:
            return

        if self.get_y() > 245:
            self.add_page()

        self.set_font("Arial", "B", 9)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, limpiar_texto(f"  {etiqueta}"), 0, 1, "L", fill=True)

        self.set_font("Arial", "", 9)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(*color_fondo)
        self.multi_cell(0, 5, limpiar_texto(contenido), border=1, fill=True)
        self.ln(3)

        self.set_text_color(0, 0, 0)

    def tabla_materiales(self, df_mat):
        if df_mat is None or df_mat.empty:
            return

        if "Descripción" not in df_mat.columns:
            return

        df_c = df_mat.dropna(subset=["Descripción"])

        if df_c.empty:
            return

        if self.get_y() > 220:
            self.add_page()

        self.add_custom_section("Materiales utilizados")

        self.set_font("Arial", "B", 9)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)

        self.cell(30, 7, "CANTIDAD", 1, 0, "C", fill=True)
        self.cell(self.w - 54, 7, "DESCRIPCION", 1, 1, "C", fill=True)

        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "", 9)

        for idx, (_, row) in enumerate(df_c.iterrows()):
            fill = idx % 2 == 0

            if fill:
                self.set_fill_color(245, 247, 252)
            else:
                self.set_fill_color(255, 255, 255)

            self.cell(
                30,
                7,
                limpiar_texto(str(row.get("Cantidad", ""))),
                1,
                0,
                "C",
                fill=fill
            )

            self.cell(
                self.w - 54,
                7,
                limpiar_texto(str(row.get("Descripción", ""))),
                1,
                1,
                "L",
                fill=fill
            )

        self.ln(3)

    def photo_grid(self, title, photos):
        if not photos:
            return

        if self.get_y() > 250:
            self.add_page()

        self.set_font("Arial", "BI", 9)
        self.set_text_color(30, 58, 95)
        self.cell(0, 6, limpiar_texto(f"  Evidencia fotografica - {title}"), 0, 1, "L")
        self.set_text_color(0, 0, 0)
        self.ln(1)

        max_w = 88
        max_h = 62
        pie_h = 5
        gap_v = 4
        fila_h = max_h + pie_h + gap_v
        margen_x = 12
        col_paso = 95

        fotos_limitadas = photos[:MAX_FOTOS_RECOMENDADAS]
        filas = [fotos_limitadas[i:i + 2] for i in range(0, len(fotos_limitadas), 2)]

        foto_num = 0

        for fila in filas:
            if self.get_y() + fila_h > 272:
                self.add_page()
                self.set_font("Arial", "BI", 9)
                self.set_text_color(30, 58, 95)
                self.cell(0, 6, limpiar_texto(f"  Evidencia fotografica cont. - {title}"), 0, 1, "L")
                self.set_text_color(0, 0, 0)
                self.ln(1)

            y_fila = self.get_y()

            for col, foto in enumerate(fila):
                foto_num += 1

                try:
                    tmp_img = comprimir_imagen_a_temp(
                        foto,
                        max_size=MAX_IMAGE_SIZE,
                        quality=IMAGE_QUALITY
                    )

                    img = Image.open(tmp_img).convert("RGB")
                    img_w, img_h = img.size

                    escala = min(max_w / img_w, max_h / img_h)
                    final_w = img_w * escala
                    final_h = img_h * escala

                    x_celda = margen_x + col * col_paso
                    x_img = x_celda + (max_w - final_w) / 2
                    y_img = y_fila + (max_h - final_h) / 2

                    self.image(tmp_img, x=x_img, y=y_img, w=final_w, h=final_h)

                    with contextlib.suppress(FileNotFoundError):
                        os.remove(tmp_img)

                    self.set_xy(x_celda, y_fila + max_h + 1)
                    self.set_font("Arial", "I", 7)
                    self.set_text_color(100, 100, 100)
                    self.cell(
                        max_w,
                        pie_h - 1,
                        limpiar_texto(f"Foto {foto_num} - {title}"),
                        0,
                        0,
                        "C"
                    )
                    self.set_text_color(0, 0, 0)

                except Exception:
                    self.set_xy(margen_x + col * col_paso, y_fila)
                    self.set_font("Arial", "I", 8)
                    self.cell(
                        max_w,
                        max_h,
                        limpiar_texto(f"[Error imagen {foto_num}]"),
                        1,
                        0,
                        "C"
                    )

            self.set_y(y_fila + fila_h)

        if len(photos) > MAX_FOTOS_RECOMENDADAS:
            self.set_font("Arial", "I", 8)
            self.set_text_color(120, 120, 120)
            self.multi_cell(
                0,
                5,
                limpiar_texto(
                    f"Nota: Se integraron las primeras {MAX_FOTOS_RECOMENDADAS} fotos "
                    f"de {len(photos)} para mantener ligero el reporte."
                )
            )
            self.set_text_color(0, 0, 0)

        self.ln(3)


# =========================================================
# GENERAR PDF
# =========================================================
def generar_pdf_reporte(
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
    correos_destino,
):
    pdf = ReporteContratoPDF()
    pdf.add_page()

    fecha_str = fecha_ejecucion.strftime("%d/%m/%Y")

    pdf.add_custom_section("Datos generales")

    datos_generales = [
        ("Contrato", contrato),
        ("Folio / Ticket / OT", folio),
        ("Fecha de ejecucion", fecha_str),
        ("Sucursal / Inmueble", sucursal if sucursal else "-"),
        ("Direccion", direccion if direccion else "-"),
        ("Ciudad", ciudad if ciudad else "-"),
        ("Oficina responsable", oficina if oficina else "-"),
        ("Tecnico asignado", tecnico if tecnico else "-"),
        ("Supervisor", supervisor if supervisor else "-"),
        ("Tipo de servicio", tipo_servicio),
        ("Estatus final", estatus_final),
    ]

    pdf.tabla_info(datos_generales)

    pdf.add_custom_section("Alcance del reporte")

    datos_alcance = [
        ("Seccion", seccion),
        ("Descripcion", descripcion),
    ]

    pdf.tabla_info(datos_alcance)

    pdf.bloque_texto("Actividades realizadas", actividades)
    pdf.tabla_materiales(df_materiales)
    pdf.bloque_texto("Observaciones", observaciones if observaciones else "Sin observaciones.")

    pdf.add_custom_section("Evidencias fotograficas")

    for nombre_evidencia, archivos in evidencias.items():
        if archivos:
            pdf.photo_grid(nombre_evidencia, archivos)

    pdf.add_custom_section("Destinatarios")

    pdf.bloque_texto(
        "Correos configurados",
        "\n".join(correos_destino) if correos_destino else "Sin destinatarios configurados."
    )

    salida_pdf = pdf.output(dest="S")

    if isinstance(salida_pdf, bytes):
        pdf_bytes = salida_pdf
    else:
        pdf_bytes = salida_pdf.encode("latin-1", "replace")

    return pdf_bytes, fecha_str


# =========================================================
# ENVÍO DE CORREO
# =========================================================
def enviar_correo_reporte(
    pdf_bytes,
    contrato,
    folio,
    sucursal,
    oficina,
    nombre_archivo,
    correos_extra,
    fecha_ejecucion,
    lista_destinatarios,
):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            st.error(
                "Error de configuración: No se encontraron EMAIL_SENDER o EMAIL_PASSWORD en Secrets."
            )
            return False

        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]

        extra = [
            c.strip()
            for c in correos_extra.split(",")
            if c.strip()
        ] if correos_extra else []

        destinatarios = list(set(lista_destinatarios + extra))

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
                f"Fecha Ejecucion: {fecha_ejecucion}\n"
                f"Oficina: {oficina}\n"
                f"Folio / Ticket / OT: {folio}\n"
                f"Sucursal / Inmueble: {sucursal}\n\n"
                f"Se adjunta el PDF del reporte."
            )
        )

        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=nombre_archivo
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)

        return True

    except Exception as error:
        st.error(f"Error de conexión SMTP: {error}")
        return False


# =========================================================
# VALIDACIONES
# =========================================================
def validar_campos_obligatorios(
    contrato,
    folio,
    sucursal,
    tecnico,
    seccion,
    actividades,
    evidencias,
):
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
# MAIN
# =========================================================
def main():
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

    if "contrato_reporte" not in st.session_state:
        st.session_state["contrato_reporte"] = {}

    form_state = st.session_state["contrato_reporte"]

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

        evidencias = {}

        st.markdown("### Evidencias obligatorias")

        for evidencia in EVIDENCIAS_OBLIGATORIAS:
            archivos = st.file_uploader(
                evidencia,
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"evidencia_{evidencia}"
            )

            evidencias[evidencia] = archivos
            mostrar_estado_archivos(evidencia, archivos)

        st.markdown("### Evidencia documental")

        for evidencia in EVIDENCIAS_DOCUMENTALES:
            archivos = st.file_uploader(
                evidencia,
                type=["jpg", "jpeg", "png", "pdf"],
                accept_multiple_files=True,
                key=f"evidencia_{evidencia}"
            )

            evidencias[evidencia] = archivos
            mostrar_estado_archivos(evidencia, archivos)

        st.markdown("### Evidencias opcionales")

        for evidencia in EVIDENCIAS_OPCIONALES:
            archivos = st.file_uploader(
                evidencia,
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"evidencia_{evidencia}"
            )

            evidencias[evidencia] = archivos
            mostrar_estado_archivos(evidencia, archivos)

        form_state["evidencias_keys_initialized"] = True

        st.success("Evidencias cargadas temporalmente en la sesión de Streamlit.")

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
                    pdf_bytes, fecha_str = generar_pdf_reporte(
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
                        correos_destino=destinatarios_base,
                    )

                    nombre_pdf = limpiar_nombre_archivo(
                        f"Reporte_Fotografico_{contrato}_{seccion}_{folio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    )

                    st.session_state["contrato_pdf_bytes"] = pdf_bytes
                    st.session_state["contrato_nombre_pdf"] = nombre_pdf
                    st.session_state["contrato_fecha_str"] = fecha_str
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

        if "contrato_pdf_bytes" in st.session_state:
            pdf_bytes = st.session_state["contrato_pdf_bytes"]
            nombre_pdf = st.session_state["contrato_nombre_pdf"]

            st.download_button(
                "⬇️ Descargar PDF",
                data=pdf_bytes,
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
                    enviado = enviar_correo_reporte(
                        pdf_bytes=st.session_state["contrato_pdf_bytes"],
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
                    st.success("Reporte enviado correctamente por correo.")
                else:
                    st.warning(
                        "El PDF fue generado, pero no se pudo enviar el correo. "
                        "Descárgalo y compártelo manualmente."
                    )

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
