import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import sys
import smtplib
from email.message import EmailMessage
import io
import tempfile
import contextlib
from pypdf import PdfWriter

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
PAGE_TITLE = "BESCO | Reporte General"
PAGE_ICON = "📑"
LAYOUT = "centered"

MAX_EQUIPOS = 10
MAX_FOTOS_RECOMENDADAS = 6

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
# ESTILOS OSCUROS (TEMA EJECUTIVO BESCO) CON INPUTS BLANCOS
# =========================================================
def aplicar_estilos_oscuros() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0B1421 !important;
        }
        
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }

        /* ===== BARRA LATERAL IZQUIERDA (SIDEBAR) ===== */
        [data-testid="stSidebar"] {
            background-color: #162032 !important;
            border-right: 1px solid #334155 !important;
        }
        [data-testid="stSidebarNav"] {
            background-color: #162032 !important;
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }
        [data-testid="stSidebarNav"] span {
            color: #F8FAFC !important;
            font-weight: 500 !important;
        }
        [data-testid="stSidebarNav"] li:hover {
            background-color: #1E293B !important;
        }
        [data-testid="stSidebarNav"] [aria-current="page"] {
            background-color: #363C98 !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebarNav"] [aria-current="page"] span {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }

        .block-container {
            padding-top: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            max-width: 900px;
        }

        .main-title {
            text-align: center;
            color: #FFFFFF;
            font-size: 1.8rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            text-align: center;
            color: #94A3B8;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #E2E8F0;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
            border-bottom: 1px solid #334155;
            padding-bottom: 0.3rem;
        }

        .info-box {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 1rem;
            color: #E2E8F0;
            font-size: 0.9rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }

        .warning-box {
            background-color: #422006;
            border: 1px solid #78350F;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            color: #FDE047;
            font-size: 0.9rem;
        }

        .ok-box {
            background-color: #064E3B;
            border: 1px solid #065F46;
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            margin-bottom: 10px;
            color: #6EE7B7;
            font-size: 0.9rem;
        }

        /* FIX DE CONTRASTE: Inputs, Textareas, Date, Selectbox con FONDO BLANCO Y LETRA NEGRA */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] > div:hover,
        div[data-baseweb="select"] > div:focus-within {
            background-color: #FFFFFF !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
        }
        
        input, textarea, 
        div[data-baseweb="select"] span, 
        div[data-baseweb="select"] div {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            font-weight: 500 !important;
        }
        
        input::placeholder, textarea::placeholder {
            color: #64748B !important;
            opacity: 1 !important;
            -webkit-text-fill-color: #64748B !important;
        }

        div[data-baseweb="popover"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #475569 !important;
        }
        
        ul[role="listbox"] li {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        
        ul[role="listbox"] li:hover {
            background-color: #E2E8F0 !important;
        }

        [data-testid="stExpander"] {
            background-color: #162032 !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
        }
        
        [data-testid="stExpander"] summary p {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        [data-testid="stDataFrame"] {
            background-color: #1E293B !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
        }

        label, .stMarkdown, .stText, p {
            color: #E2E8F0 !important;
        }

        div.stButton > button {
            background-color: #363C98 !important; 
            color: white !important;
            border: 1px solid #282D75 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }
        div.stButton > button:hover {
            background-color: #4C52BC !important;
            border: 1px solid #363C98 !important;
            transform: translateY(-2px);
        }
        
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #E31837 !important;
            border: 1px solid #B01028 !important;
            box-shadow: 0 4px 6px -1px rgba(227, 24, 55, 0.4);
        }
        div.stButton > button[data-testid="baseButton-primary"]:hover {
            background-color: #FA2A4A !important;
            border: 1px solid #E31837 !important;
        }

        .footer-text {
            text-align: center;
            color: #64748B;
            font-size: 0.8rem;
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# UTILIDADES GENERALES
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

@contextlib.contextmanager
def archivo_temporal(suffix=".jpg"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()

    try:
        yield tmp.name
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp.name)

def comprimir_imagen_a_temp(file_obj, max_size=(1100, 1100), quality=65):
    file_obj.seek(0)
    img = Image.open(file_obj).convert("RGB")
    img.thumbnail(max_size)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    tmp.close()

    img.save(
        tmp.name,
        format="JPEG",
        quality=quality,
        optimize=True
    )

    return tmp.name

def contar_archivos(archivos) -> int:
    if not archivos:
        return 0
    return len(archivos)

def mostrar_estado_fotos(nombre: str, archivos) -> None:
    cantidad = contar_archivos(archivos)

    if cantidad == 0:
        st.caption(f"{nombre}: sin archivos cargados.")
    elif cantidad <= MAX_FOTOS_RECOMENDADAS:
        st.success(f"{nombre}: {cantidad} archivo(s) cargado(s).")
    else:
        st.warning(
            f"{nombre}: {cantidad} archivo(s) cargado(s). "
            f"Para celular se recomienda máximo {MAX_FOTOS_RECOMENDADAS}."
        )

def limpiar_nombre_archivo(nombre: str) -> str:
    caracteres_invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    limpio = nombre

    for caracter in caracteres_invalidos:
        limpio = limpio.replace(caracter, "_")

    limpio = limpio.replace(" ", "_")
    limpio = limpio.replace("&", "y")

    return limpio

# =========================================================
# CLASE PDF
# =========================================================
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(left=12, top=12, right=12)

    def header(self):
        try:
            if os.path.exists(LOGO_PATH):
                img_logo = Image.open(LOGO_PATH).convert("RGB")
                orig_w, orig_h = img_logo.size
                final_h = 18
                final_w = orig_w * (final_h / orig_h)

                with archivo_temporal(suffix=".jpg") as tmp_logo:
                    img_logo.thumbnail((800, 800))
                    img_logo.save(tmp_logo, format="JPEG", quality=75, optimize=True)
                    self.image(tmp_logo, x=12, y=8, w=final_w, h=final_h)
        except Exception:
            pass

        self.set_font("Arial", "B", 11)
        self.set_text_color(30, 58, 95)
        self.set_xy(0, 10)
        self.cell(
            self.w - 12,
            6,
            limpiar_texto("REPORTE DE SERVICIO TECNICO"),
            0,
            1,
            "R"
        )

        self.set_font("Arial", "", 8)
        self.set_text_color(120, 120, 120)
        self.set_x(0)
        self.cell(
            self.w - 12,
            5,
            limpiar_texto(f"Emision: {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
            0,
            1,
            "R"
        )

        self.set_draw_color(226, 24, 54)
        self.set_line_width(0.6)
        self.line(12, 31, self.w - 12, 31)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.ln(24)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(200, 200, 200)
        self.line(12, self.get_y(), self.w - 12, self.get_y())
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0,
            8,
            limpiar_texto(f"Pagina {self.page_no()} | Documento confidencial BESCO"),
            0,
            0,
            "C"
        )

    def add_custom_section(self, title):
        if self.get_y() > 245:
            self.add_page()

        self.set_fill_color(30, 58, 95)
        self.set_font("Arial", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(4, 8, "", 0, 0, "L", fill=True)

        self.set_fill_color(226, 24, 54)
        self.cell(2, 8, "", 0, 0, "L", fill=True)

        self.set_fill_color(30, 58, 95)
        self.cell(
            self.w - 30,
            8,
            limpiar_texto(f"  {self.section_count}. {title.upper()}"),
            0,
            1,
            "L",
            fill=True
        )

        self.section_count += 1
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def tabla_info(self, datos):
        self.set_font("Arial", "", 9)
        col_label = 50
        col_valor = self.w - 12 - 12 - col_label

        for etiqueta, valor in datos:
            self.set_font("Arial", "B", 9)
            self.set_fill_color(240, 243, 248)
            self.cell(col_label, 7, limpiar_texto(etiqueta), 1, 0, "L", fill=True)

            self.set_font("Arial", "", 9)
            self.set_fill_color(255, 255, 255)
            self.cell(col_valor, 7, limpiar_texto(str(valor)), 1, 1, "L", fill=True)

        self.ln(3)

    def tabla_mediciones(self, meds):
        if not meds:
            return

        self.set_font("Arial", "B", 8)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)

        ancho = (self.w - 24) / len(meds)

        for k in meds:
            self.cell(ancho, 7, limpiar_texto(k), 1, 0, "C", fill=True)

        self.ln()

        self.set_font("Arial", "", 8)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)

        for v in meds.values():
            self.cell(ancho, 7, limpiar_texto(str(v) if v else "-"), 1, 0, "C")

        self.ln(5)

    def bloque_texto(self, etiqueta, contenido, color_fondo=(248, 248, 252)):
        if not contenido:
            return

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

    def photo_grid(self, title, photos):
        if not photos:
            return

        if self.get_y() > 250:
            self.add_page()

        self.set_font("Arial", "BI", 9)
        self.set_text_color(30, 58, 95)
        self.cell(0, 6, limpiar_texto(f"  Fotografias - {title}"), 0, 1, "L")
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
                self.cell(0, 6, limpiar_texto(f"  Fotografias cont. - {title}"), 0, 1, "L")
                self.set_text_color(0, 0, 0)
                self.ln(1)

            y_fila = self.get_y()

            for col, foto in enumerate(fila):
                foto_num += 1

                try:
                    tmp_img = comprimir_imagen_a_temp(
                        foto,
                        max_size=(1100, 1100),
                        quality=65
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

    def folio_grid(self, title, photo_files):
        if not photo_files:
            return

        fotos_limitadas = photo_files[:4]

        for i, foto in enumerate(fotos_limitadas):
            try:
                self.add_page()
                self.add_custom_section(f"{title} - Evidencia {i + 1}")

                tmp_img = comprimir_imagen_a_temp(
                    foto,
                    max_size=(1300, 1300),
                    quality=70
                )

                img = Image.open(tmp_img).convert("RGB")
                avail_w, avail_h = 186, 210
                img_w, img_h = img.size

                escala = min(avail_w / img_w, avail_h / img_h)
                final_w = img_w * escala
                final_h = img_h * escala

                x_center = 12 + (avail_w - final_w) / 2
                self.image(
                    tmp_img,
                    x=x_center,
                    y=self.get_y() + 5,
                    w=final_w,
                    h=final_h
                )

                with contextlib.suppress(FileNotFoundError):
                    os.remove(tmp_img)

            except Exception:
                self.set_font("Arial", "I", 9)
                self.cell(
                    0,
                    8,
                    limpiar_texto(f"[Error al cargar folio {i + 1}]"),
                    0,
                    1
                )

    def separador_equipo(self):
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(12, self.get_y(), self.w - 12, self.get_y())
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.ln(5)

# =========================================================
# ENVÍO DE CORREO
# =========================================================
def enviar_correo(
    pdf_bytes,
    cliente,
    folio,
    sucursal,
    oficina,
    nombre_archivo,
    correos_extra,
    fecha_ejec,
    lista_destinatarios
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
            f"Reporte Tecnico BESCO: {cliente} | TK: {folio} | Of: {oficina}"
        )
        msg["From"] = remitente
        msg["To"] = ", ".join(destinatarios)

        msg.set_content(
            limpiar_texto(
                f"Se ha generado un nuevo reporte desde el Sistema de Evidencia Tecnica BESCO.\n\n"
                f"Fecha Ejecucion: {fecha_ejec}\n"
                f"Oficina: {oficina}\n"
                f"Cliente: {cliente}\n"
                f"Folio: {folio}\n"
                f"Sucursal: {sucursal}"
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
# GENERACIÓN DEL PDF
# =========================================================
def generar_pdf(
    cliente,
    folio,
    fecha_ejecucion,
    oficina,
    sucursal,
    tecnico,
    supervisor,
    tipo_serv,
    referencia,
    equipos_data,
    df_mat,
    archivos_folio
):
    pdf = BESCO_PDF()
    pdf.add_page()

    pdf.add_custom_section("Informacion General del Servicio")

    f_ejec_str = fecha_ejecucion.strftime("%d/%m/%Y")

    color_op = {
        "Operando correctamente": (0, 150, 80),
        "Operando con observaciones": (200, 130, 0),
        "No queda operando": (200, 30, 30),
    }

    datos_generales = [
        ("Cliente", cliente),
        ("Folio / OT / TK", folio),
        ("Fecha de Ejecucion", f_ejec_str),
        ("Oficina Responsable", oficina),
        ("Sucursal / Inmueble", sucursal if sucursal else "-"),
        ("Tecnico Asignado", tecnico if tecnico else "-"),
        ("Supervisor", supervisor if supervisor else "-"),
        ("Tipo de Servicio", f"{tipo_serv} ({referencia})"),
    ]

    pdf.tabla_info(datos_generales)

    if len(equipos_data) > 1:
        pdf.add_custom_section("Resumen de Equipos")
        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(30, 58, 95)
        pdf.set_text_color(255, 255, 255)

        pdf.cell(10, 7, "#", 1, 0, "C", fill=True)
        pdf.cell(50, 7, "Categoria", 1, 0, "C", fill=True)
        pdf.cell(30, 7, "TAG", 1, 0, "C", fill=True)
        pdf.cell(96, 7, "Estatus Final", 1, 1, "C", fill=True)

        pdf.set_text_color(0, 0, 0)

        for eq in equipos_data:
            pdf.set_font("Arial", "", 9)
            r, g, b = color_op.get(eq["estatus"], (0, 0, 0))

            pdf.cell(10, 6, str(eq["numero"]), 1, 0, "C")
            pdf.cell(50, 6, limpiar_texto(eq["esp"]), 1, 0, "L")
            pdf.cell(30, 6, limpiar_texto(eq["tag"] or "-"), 1, 0, "C")

            pdf.set_text_color(r, g, b)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(96, 6, limpiar_texto(eq["estatus"]), 1, 1, "L")
            pdf.set_text_color(0, 0, 0)

        pdf.ln(4)

    for eq in equipos_data:
        if pdf.get_y() > 230:
            pdf.add_page()

        pdf.add_custom_section(f"Equipo {eq['numero']}: {eq['esp']}")

        datos_eq = []

        if eq["tag"]:
            datos_eq.append(("TAG", eq["tag"]))

        if eq["marca"]:
            datos_eq.append(("Marca", eq["marca"]))

        if eq["cap"]:
            datos_eq.append(("Capacidad", eq["cap"]))

        r, g, b = color_op.get(eq["estatus"], (0, 0, 0))
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(r, g, b)
        pdf.cell(
            0,
            7,
            limpiar_texto(f"  Estatus Final: {eq['estatus']}"),
            0,
            1,
            "L"
        )
        pdf.set_text_color(0, 0, 0)

        if datos_eq:
            pdf.tabla_info(datos_eq)

        valid_meds = {
            k: v
            for k, v in eq["meds"].items()
            if v
        }

        if valid_meds:
            pdf.tabla_mediciones(valid_meds)

        if eq["otros"]:
            pdf.bloque_texto("Detalles / Mediciones", eq["otros"])

        if eq["actividades"]:
            pdf.bloque_texto("Actividades Realizadas", eq["actividades"])

        if eq["com"]:
            pdf.bloque_texto(
                "Comentarios Extras",
                eq["com"],
                color_fondo=(255, 252, 240)
            )

        pdf.photo_grid(f"ANTES - Equipo {eq['numero']}", eq["fa"])
        pdf.photo_grid(f"DESPUES - Equipo {eq['numero']}", eq["fd"])

        pdf.separador_equipo()

    df_c = df_mat.copy()

    if not df_c.empty and "Descripción" in df_c.columns:
        df_c = df_c.dropna(subset=["Descripción"])

        if not df_c.empty:
            if pdf.get_y() > 220:
                pdf.add_page()

            pdf.add_custom_section("Materiales Utilizados")

            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(30, 58, 95)
            pdf.set_text_color(255, 255, 255)

            pdf.cell(30, 7, "CANTIDAD", 1, 0, "C", fill=True)
            pdf.cell(
                pdf.w - 54,
                7,
                limpiar_texto("DESCRIPCION"),
                1,
                1,
                "C",
                fill=True
            )

            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "", 9)

            for idx, (_, row) in enumerate(df_c.iterrows()):
                fill = idx % 2 == 0

                if fill:
                    pdf.set_fill_color(245, 247, 252)
                else:
                    pdf.set_fill_color(255, 255, 255)

                pdf.cell(
                    30,
                    7,
                    limpiar_texto(str(row.get("Cantidad", ""))),
                    1,
                    0,
                    "C",
                    fill=fill
                )
                pdf.cell(
                    pdf.w - 54,
                    7,
                    limpiar_texto(str(row.get("Descripción", ""))),
                    1,
                    1,
                    "L",
                    fill=fill
                )

    archivos_folio = archivos_folio or []

    fotos_folio = [
        f for f in archivos_folio
        if f and hasattr(f, "type") and "image" in f.type
    ]

    if fotos_folio:
        pdf.folio_grid("FOLIO BESCO", fotos_folio)

    salida_pdf = pdf.output(dest="S")

    if isinstance(salida_pdf, bytes):
        pdf_bytes = salida_pdf
    else:
        pdf_bytes = salida_pdf.encode("latin-1", "replace")

    pdfs_folio = [
        f for f in archivos_folio
        if f and hasattr(f, "type") and f.type == "application/pdf"
    ]

    if pdfs_folio:
        writer = PdfWriter()
        writer.append(io.BytesIO(pdf_bytes))

        for p in pdfs_folio:
            p.seek(0)
            writer.append(p)

        out = io.BytesIO()
        writer.write(out)
        pdf_bytes = out.getvalue()

    return pdf_bytes, f_ej
