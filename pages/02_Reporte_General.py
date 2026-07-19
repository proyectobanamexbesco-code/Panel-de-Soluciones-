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
# ESTILOS LIGEROS PARA CELULAR
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
    """
    Comprime imagen para hacer más ligero el PDF.
    Ideal para fotos tomadas desde celular.
    """
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
    skew = contar_archivos(archivos)

    if skew == 0:
        st.caption(f"{nombre}: sin archivos cargados.")
    elif skew <= MAX_FOTOS_RECOMENDADAS:
        st.success(f"{nombre}: {skew} archivo(s) cargado(s).")
    else:
        st.warning(
            f"{nombre}: {skew} archivo(s) cargado(s). "
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

    return pdf_bytes, f_ejec_str


# =========================================================
# DATOS FIJOS
# =========================================================
LISTA_OFICINAS = [
    "Acapulco",
    "Toluca",
    "Pachuca",
    "Michoacán",
    "Zonas/ CDMX",
    "CDMX",
    "Ben & Company",
    "BX+",
    "Emerson",
    "Odoo",
    "Tampico",
    "Telmex",
]

MAPEO_CORREOS = {
    "Acapulco": [
        "itzallana.vazquez@besco.mx",
        "gerardo.fuentes@besco.mx",
    ],
    "Toluca": [
        "policarpo.rosaliano@besco.mx",
        "monica.iniestra@besco.mx",
    ],
    "Pachuca": [
        "german.constantino@besco.mx",
    ],
    "Michoacán": [
        "cristobal.rodriguez@besco.mx",
        "ximena.acosta@besco.mx",
        "javier.zamano@besco.mx",
    ],
    "Zonas/ CDMX": [
        "german.constantino@besco.mx",
        "andres.mayagoitia@besco.mx",
        "brenda.cervantes@besco.mx",
    ],
    "CDMX": [
        "gerardo.mendez@besco.mx",
        "alejandro.ramirez@besco.mx",
    ],
    "Ben & Company": [
        "gerardo.mendez@besco.mx",
        "alejandro.ramirez@besco.mx",
    ],
    "BX+": [
        "gerardo.mendez@besco.mx",
        "alejandro.ramirez@besco.mx",
        "patricia.cortes@besco.mx",
    ],
    "Emerson": [
        "gerardo.mendez@besco.mx",
        "alejandro.ramirez@besco.mx",
        "patricia.cortes@besco.mx",
    ],
    "Odoo": [
        "gerardo.mendez@besco.mx",
        "alejandro.ramirez@besco.mx",
        "dorian.rodriguez@besco.mx",
    ],
    "Tampico": [
        "ingrid.lucio@besco.mx",
        "joel.perez@besco.mx",
        "gerardo.mendez@besco.mx",
    ],    
    "Telmex": [
        "juan.perez@besco.mx",
        "dario.perez@besco.mx",
        "gerardo.mendez@besco.mx"
    ],
}

LEYENDAS_DEFAULT = {
    "Conservación": (
        "SE REALIZA REAPRIETE DE TORNILLERIA Y LUBRICACION DE CHAPAS, "
        "BISAGRAS, SE HACE REVISION DE ESTADO DE PINTURA, PISOS, "
        "EXTINTORES Y MOBILIARIO."
    ),
    "Hidrosanitario": (
        "SE REALIZA REVISION DE CESPOL, MEZCLADORA, MANGUERAS, LLAVES, "
        "WC, DESPACHADORES, EXTRACTORES Y CONEXIONES, SE DEJA FUNCIONANDO "
        "CORRECTAMENTE."
    ),
    "Tableros Eléctricos": (
        "SE REALIZA LIMPIEZA, REAPRIETE DE TORNILLERIA, TOMA DE AMPERAJES "
        "Y VOLTAJES, SE DEJA FUNCIONANDO CORRECTAMENTE."
    ),
    "Iluminación": (
        "SE REALIZA REVISION GENERAL DE LAMPARAS, SE CAMBIAN LAMPARAS "
        "FUNDIDAS, SE DEJA FUNCIONANDO CORRECTAMENTE."
    ),
    "Aire Acondicionado": (
        "SE REALIZA LIMPIEZA GENERAL DE SERPENTINES, TOMA DE PRESION DE "
        "REFRIGERANTE, VOLTAJES, AMPERAJES, REAPRIETE DE CONEXIONES, "
        "LIMPIEZA DE FILTROS, SE DEJA FUNCIONANDO CORRECTAMENTE."
    ),
}

CATEGORIAS_OPCIONES = [
    "Ninguna",
    "Aire Acondicionado",
    "Tableros Eléctricos",
    "Hidroneumático",
    "Conservación",
    "Hidrosanitario",
    "Iluminación",
    "Otros",
]


# =========================================================
# INTERFAZ PRINCIPAL
# =========================================================
def main():
    aplicar_estilos_ligeros()

    st.markdown(
        """
        <div class="main-title">📑 Reporte General BESCO</div>
        <div class="subtitle">
            Versión ligera para celular: captura datos, evidencias, genera PDF y envía correo opcionalmente.
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
            Recomendación para Android: usa pocas fotos por equipo, evita imágenes repetidas
            y genera primero el PDF antes de enviarlo por correo.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">1. Identificación General del Servicio</div>',
        unsafe_allow_html=True
    )

    cliente = st.text_input("Cliente")
    folio = st.text_input("Folio / OT / TK", max_chars=30)
    fecha_ejecucion = st.date_input("Fecha de Ejecución", datetime.now())

    sucursal = st.text_input("Sucursal / Inmueble")

    oficina = st.selectbox(
        "Oficina Responsable",
        LISTA_OFICINAS
    )

    tecnico = st.text_input("Técnico Asignado")
    supervisor = st.text_input("Supervisor")

    tipo_serv = st.selectbox(
        "Servicio",
        ["Preventivo", "Correctivo", "Emergencia"]
    )

    referencia = st.selectbox(
        "Referencia",
        ["Con Ticket", "Sin Ticket"]
    )

    st.markdown(
        '<div class="section-title">2. Evidencia Documental</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="warning-box">
            Puedes subir hasta 4 fotos del folio BESCO y/o archivos PDF.
            Para celular se recomienda no subir archivos demasiado pesados.
        </div>
        """,
        unsafe_allow_html=True
    )

    archivos_folio = st.file_uploader(
        "Subir Folio BESCO",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True
    )

    mostrar_estado_fotos("Folio BESCO", archivos_folio)

    st.markdown(
        '<div class="section-title">3. Equipos a Reportar</div>',
        unsafe_allow_html=True
    )

    num_equipos = st.number_input(
        "¿Cuántos equipos se atendieron?",
        min_value=1,
        max_value=MAX_EQUIPOS,
        value=1
    )

    equipos_data = []

    for i in range(num_equipos):
        expanded_default = True if i == 0 else False

        with st.expander(
            f"Equipo {i + 1}",
            expanded=expanded_default
        ):
            esp = st.selectbox(
                "Categoría",
                CATEGORIAS_OPCIONES,
                key=f"esp_{i}"
            )

            estatus = st.selectbox(
                "Estatus Final",
                [
                    "Operando correctamente",
                    "Operando con observaciones",
                    "No queda operando",
                ],
                key=f"est_{i}"
            )

            meds = {}
            otros = ""

            if esp == "Aire Acondicionado":
                st.caption("Mediciones de aire acondicionado")

                meds["Succión"] = st.text_input("Succión", key=f"s_{i}")
                meds["Descarga"] = st.text_input("Descarga", key=f"d_{i}")
                meds["Salida"] = st.text_input("Salida", key=f"t_{i}")
                meds["Amperaje"] = st.text_input("Amperaje", key=f"a_{i}")

            elif esp == "Otros":
                otros = st.text_area(
                    "Detalles / Mediciones",
                    key=f"o_{i}"
                )

            tag = st.text_input("TAG", key=f"tg_{i}")
            marca = st.text_input("Marca", key=f"mr_{i}")
            cap = st.text_input("Capacidad", key=f"cp_{i}")

            texto_defecto = LEYENDAS_DEFAULT.get(esp, "")

            # CORRECCIÓN AQUÍ: Cambiada la clave dinámica por f"act_{i}"
            actividades = st.text_area(
                "Actividades Realizadas",
                value=texto_defecto,
                height=100,
                key=f"act_{i}"
            )

            com = st.text_area(
                "Comentarios Extras",
                height=80,
                key=f"com_{i}"
            )

            st.markdown(
                """
                <div class="warning-box">
                    Para mantener ligero el reporte, se integrarán máximo 6 fotos de ANTES
                    y 6 fotos de DESPUÉS por equipo.
                </div>
                """,
                unsafe_allow_html=True
            )

            fa = st.file_uploader(
                "Fotos ANTES",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"fa_{i}"
            )

            mostrar_estado_fotos(f"Fotos ANTES equipo {i + 1}", fa)

            fd = st.file_uploader(
                "Fotos DESPUÉS",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"fd_{i}"
            )

            mostrar_estado_fotos(f"Fotos DESPUÉS equipo {i + 1}", fd)

            equipos_data.append(
                {
                    "numero": i + 1,
                    "esp": esp,
                    "estatus": estatus,
                    "actividades": actividades,
                    "meds": meds,
                    "otros": otros,
                    "tag": tag,
                    "marca": marca,
                    "cap": cap,
                    "fa": fa or [],
                    "fd": fd or [],
                }
            )

    st.markdown(
        '<div class="section-title">4. Materiales Utilizados</div>',
        unsafe_allow_html=True
    )

    if "df_materiales" not in st.session_state:
        st.session_state.df_materiales = pd.DataFrame(
            columns=["Cantidad", "Descripción"]
        )

    df_mat = st.data_editor(
        st.session_state.df_materiales,
        num_rows="dynamic",
        key="editor_materiales",
        use_container_width=True
    )

    st.markdown(
        '<div class="section-title">5. Finalizar Reporte</div>',
        unsafe_allow_html=True
    )

    correos_defecto = MAPEO_CORREOS.get(oficina, [])

    st.write("**Destinatarios automáticos de la oficina:**")
    if correos_defecto:
        for c in correos_defecto:
            st.markdown(f"- `{c}`")
    else:
        st.caption("No hay correos asignados por defecto a esta oficina.")

    correos_extra = st.text_input(
        "Correos adicionales (separados por coma)",
        help="ejemplo1@besco.mx, ejemplo2@besco.mx"
    )

    if st.button("🚀 Generar PDF y Enviar Reporte", use_container_width=True):
        if not cliente:
            st.error("Por favor, ingresa el nombre del Cliente.")
            return

        if not folio:
            st.error("Por favor, ingresa el número de Folio / OT / TK.")
            return

        with st.spinner("Generando documento PDF optimizado..."):
            pdf_bytes, f_ejec_str = generar_pdf(
                cliente=cliente,
                folio=folio,
                fecha_ejecucion=fecha_ejecucion,
                oficina=oficina,
                sucursal=sucursal,
                tecnico=tecnico,
                supervisor=supervisor,
                tipo_serv=tipo_serv,
                referencia=referencia,
                equipos_data=equipos_data,
                df_mat=df_mat,
                archivos_folio=archivos_folio
            )

        st.markdown(
            '<div class="ok-box">✅ ¡PDF generado con éxito! Puedes descargarlo abajo.</div>',
            unsafe_allow_html=True
        )

        nombre_limpio = limpiar_nombre_archivo(f"Reporte_{cliente}_{folio}.pdf")

        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_bytes,
            file_name=nombre_limpio,
            mime="application/pdf",
            use_container_width=True
        )

        with st.spinner("Enviando correo electrónico a los destinatarios..."):
            exito = enviar_correo(
                pdf_bytes=pdf_bytes,
                cliente=cliente,
                folio=folio,
                sucursal=sucursal,
                oficina=oficina,
                nombre_archivo=nombre_limpio,
                correos_extra=correos_extra,
                fecha_ejec=f_ejec_str,
                lista_destinatarios=correos_defecto
            )

            if exito:
                st.balloons()
                st.success("✉️ Reporte enviado exitosamente por correo electrónico.")


if __name__ == "__main__":
    main()
