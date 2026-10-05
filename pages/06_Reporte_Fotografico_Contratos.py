import os
import io
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

try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    import googleapiclient.http
except Exception:
    build = None
    Credentials = None


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
LOGO_PATH = os.path.join(ROOT_DIR, "logo besco 2026.jpeg")

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
        {"numero": 1, "momento": "Arribo", "actividad": "Presentarse con gerente encargado. Confirmar OT/folio y alcance de visita."},
        {"numero": 2, "momento": "Seguridad", "actividad": "Induccion rapida: zonas restringidas, riesgos, energia, alturas y agua."},
        {"numero": 3, "momento": "Reconocimiento", "actividad": "Recorrido inicial por areas aplicables segun CHECK LIST."},
        {"numero": 4, "momento": "01_Electrico", "actividad": "Instalaciones electricas y tableros."},
        {"numero": 5, "momento": "02_Canceleria_Vidrieria", "actividad": "Perfiles, cristales y herrajes."},
        {"numero": 6, "momento": "03_Hidrosanitaria", "actividad": "Acometida y bajadas pluviales."},
        {"numero": 7, "momento": "03_Hidrosanitaria_Bombeo", "actividad": "Sistema de bombeo. Evidencia opcional."},
        {"numero": 8, "momento": "04_Mobiliario", "actividad": "Mobiliario y cerrajeria basica."},
        {"numero": 9, "momento": "05_Generales", "actividad": "Acabados, limpieza, pintura y reparaciones generales."},
        {"numero": 10, "momento": "06_AA_Parametros", "actividad": "Equipos de aire acondicionado con toma de parametros."},
        {"numero": 11, "momento": "07_UPS", "actividad": "Revision de UPS y toma de parametros."},
        {"numero": 12, "momento": "09_Depositos_Agua_Cisterna", "actividad": "Depositos de agua: cisterna."},
        {"numero": 13, "momento": "09_Depositos_Agua_Tinacos", "actividad": "Depositos de agua: tinacos."},
        {"numero": 14, "momento": "Desviaciones", "actividad": "Documentar hallazgos con causa, impacto y recomendacion."},
        {"numero": 15, "momento": "Limpieza y pruebas", "actividad": "Retirar residuos, normalizar areas y probar equipos intervenidos."},
    ],
    "MacStore": [
        {"numero": 1, "momento": "Arribo", "actividad": "Presentarse en tienda y confirmar folio, alcance y responsable en sitio."},
        {"numero": 2, "momento": "Inspeccion inicial", "actividad": "Realizar recorrido inicial y levantar evidencia del area intervenida."},
        {"numero": 3, "momento": "Ejecucion", "actividad": "Ejecutar actividades correctivas, preventivas o de levantamiento."},
        {"numero": 4, "momento": "Pruebas", "actividad": "Validar funcionamiento, limpieza del area y condiciones finales."},
        {"numero": 5, "momento": "Cierre", "actividad": "Documentar hallazgos, evidencias, actividades y cierre con responsable."},
    ],
    "Samsung": [
        {"numero": 1, "momento": "Arribo", "actividad": "Presentarse en sitio y confirmar folio, alcance y responsable."},
        {"numero": 2, "momento": "Diagnostico", "actividad": "Realizar diagnostico inicial y documentar condiciones encontradas."},
        {"numero": 3, "momento": "Ejecucion", "actividad": "Ejecutar instalacion, validacion, retiro o correccion segun servicio."},
        {"numero": 4, "momento": "Pruebas", "actividad": "Realizar pruebas de funcionamiento y documentar resultado."},
        {"numero": 5, "momento": "Reporte", "actividad": "Registrar evidencias, observaciones y cierre del servicio."},
    ],
}


# =========================================================
# ESTILOS OSCUROS / EJECUTIVOS BESCO
# =========================================================
def aplicar_estilos():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0B1421 !important;
        }
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        [data-testid="stSidebar"] {
            background-color: #162032 !important;
            border-right: 1px solid #334155 !important;
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-left: 1rem;
            padding-right: 1rem;
            padding-bottom: 2rem;
            max-width: 850px;
        }
        .titulo {
            text-align: center;
            color: #FFFFFF;
            font-size: 1.7rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }
        .subtitulo {
            text-align: center;
            color: #94A3B8;
            font-size: 0.95rem;
            margin-bottom: 1.2rem;
        }
        .info-box {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 12px;
            color: #E2E8F0;
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .warning-box {
            background-color: #422006;
            border: 1px solid #78350F;
            border-radius: 12px;
            padding: 12px;
            color: #FDE047;
            font-size: 0.9rem;
            margin: 10px 0;
        }
        .ok-box {
            background-color: #064E3B;
            border: 1px solid #065F46;
            border-radius: 12px;
            padding: 12px;
            color: #6EE7B7;
            font-size: 0.9rem;
            margin: 10px 0;
        }
        .optional-box {
            background-color: #162032;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 10px;
            color: #94A3B8;
            font-size: 0.85rem;
            margin: 8px 0;
        }
        div[data-baseweb="input"] > div, 
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
        }
        input, textarea, div[data-baseweb="select"] span {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            font-weight: 500 !important;
        }
        label, .stMarkdown, p {
            color: #E2E8F0 !important;
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
        div.stButton > button {
            background-color: #363C98 !important; 
            color: white !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        div.stButton > button[data-testid="baseButton-primary"] {
            background-color: #E31837 !important;
        }
        .footer {
            text-align: center;
            color: #64748B;
            font-size: 0.8rem;
            padding-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# INTEGRACION GOOGLE DRIVE
# =========================================================
def obtener_cliente_drive():
    if Credentials is None or build is None:
        return None
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        if "gcp_service_account" not in st.secrets:
            return None
        info = dict(st.secrets["gcp_service_account"])
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return build('drive', 'v3', credentials=creds)
    except Exception:
        return None

def listar_fotos_desde_drive(folio_busqueda):
    try:
        service = obtener_cliente_drive()
        if not service or "google_config" not in st.secrets:
            return []
        id_carpeta_raiz = st.secrets["google_config"]["id_carpeta_raiz_drive"]
        
        query = f"'{id_carpeta_raiz}' in parents and mimeType contains 'image/' and trashed = false"
        if folio_busqueda:
            query += f" and name contains '{folio_busqueda}'"

        results = service.files().list(
            q=query,
            pageSize=50,
            fields="files(id, name, thumbnailLink)"
        ).execute()
        return results.get('files', [])
    except Exception:
        return []

def descargar_imagen_drive_a_bytes(file_id):
    try:
        service = obtener_cliente_drive()
        if not service:
            return None
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()
    except Exception:
        return None


# =========================================================
# UTILIDADES
# =========================================================
def normalizar_texto(texto):
    if texto is None:
        return ""
    valor = str(texto)
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "ü": "u", "Ü": "U", "•": "-",
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
        "\u2013": "-", "\u2014": "-", "\u200b": "", "\r": "", "°": " grados",
    }
    for original, nuevo in reemplazos.items():
        valor = valor.replace(original, nuevo)
    return valor

def crear_nombre_archivo(nombre):
    valor = normalizar_texto(nombre)
    invalidos = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "(", ")", "&"]
    for caracter in invalidos:
        valor = valor.replace(caracter, "_")
    return valor.replace(" ", "_")

def dividir_texto(texto, max_chars=90):
    texto_limpio = normalizar_texto(texto)
    if not texto_limpio.strip():
        return ["Sin informacion capturada."]
    lineas = textwrap.wrap(texto_limpio, width=max_chars, break_long_words=False, replace_whitespace=False)
    return lineas if lineas else ["Sin informacion capturada."]

def comprimir_imagen_a_temp(uploaded_file):
    uploaded_file.seek(0)
    imagen = Image.open(uploaded_file).convert("RGB")
    imagen.thumbnail(MAX_IMAGE_SIZE)
    temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_img.close()
    imagen.save(temp_img.name, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
    return temp_img.name

def existe_logo_besco():
    return os.path.exists(LOGO_PATH)

def crear_logo_temporal():
    imagen = Image.open(LOGO_PATH).convert("RGB")
    imagen.thumbnail((1200, 1200))
    temp_logo = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_logo.close()
    imagen.save(temp_logo.name, format="JPEG", quality=95, optimize=True)
    return temp_logo.name

def hay_fotos_en_item(evidencia):
    return any([
        evidencia.get("antes_1") is not None,
        evidencia.get("antes_2") is not None,
        evidencia.get("despues_1") is not None,
        evidencia.get("despues_2") is not None,
    ])

def hay_fotos_antes(evidencia):
    return any([evidencia.get("antes_1") is not None, evidencia.get("antes_2") is not None])

def hay_fotos_despues(evidencia):
    return any([evidencia.get("despues_1") is not None, evidencia.get("despues_2") is not None])


# =========================================================
# PDF
# =========================================================
def encabezado_pdf(c, titulo):
    title_y, line_y, title_x = 750, 680, MARGIN_LEFT
    logo_temp = None

    if existe_logo_besco():
        try:
            logo_temp = crear_logo_temporal()
            logo_reader = ImageReader(logo_temp)
            logo_w, logo_h = logo_reader.getSize()
            ratio = min(213 / logo_w, 83 / logo_h)
            c.drawImage(logo_reader, MARGIN_LEFT, 695, width=logo_w * ratio, height=logo_h * ratio, preserveAspectRatio=True, mask="auto")
            title_x = MARGIN_LEFT + 235
        except Exception:
            title_x = MARGIN_LEFT
        finally:
            if logo_temp and os.path.exists(logo_temp):
                with contextlib.suppress(Exception):
                    os.remove(logo_temp)

    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(title_x, title_y, normalizar_texto(titulo))

    c.setFillColor(colors.HexColor("#5B6573"))
    c.setFont("Helvetica", 9)
    c.drawString(title_x, title_y - 18, f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    c.setStrokeColor(colors.HexColor("#D9E2EC"))
    c.line(MARGIN_LEFT, line_y, PDF_WIDTH - MARGIN_RIGHT, line_y)
    return line_y - 25

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
    return y - 18

def linea_pdf(c, etiqueta, valor, y):
    y = nueva_pagina(c, y, 70)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1E3A5F"))
    c.drawString(MARGIN_LEFT, y, normalizar_texto(f"{etiqueta}:"))
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(MARGIN_LEFT + 125, y, normalizar_texto(valor))
    return y - 15

def bloque_texto_pdf(c, titulo, texto, y):
    y = titulo_seccion(c, titulo, y)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    for linea in dividir_texto(texto):
        y = nueva_pagina(c, y, 70)
        c.drawString(MARGIN_LEFT, y, normalizar_texto(linea))
        y -= 13
    return y - 10

def dibujar_imagen_en_celda(c, uploaded_file, x, y, ancho, alto):
    temp_path = None
    try:
        temp_path = comprimir_imagen_a_temp(uploaded_file)
        img_reader = ImageReader(temp_path)
        img_w, img_h = img_reader.getSize()
        ratio = min(ancho / img_w, alto / img_h)
        c.drawImage(img_reader, x + (ancho - img_w * ratio) / 2, y + (alto - img_h * ratio) / 2, width=img_w * ratio, height=img_h * ratio, preserveAspectRatio=True, mask="auto")
    except Exception:
        c.setStrokeColor(colors.HexColor("#B8C2CC"))
        c.setFillColor(colors.HexColor("#F4F6F8"))
        c.rect(x, y, ancho, alto, fill=1, stroke=1)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + ancho / 2, y + alto / 2, "Error imagen")
    finally:
        if temp_path and os.path.exists(temp_path):
            with contextlib.suppress(Exception):
                os.remove(temp_path)

def fila_dos_fotos_pdf(c, titulo_izq, archivo_izq, titulo_der, archivo_der, y):
    if archivo_izq is None and archivo_der is None:
        return y
    alto_img = 145
    y = nueva_pagina(c, y, alto_img + 56)
    ancho_celda = (PDF_WIDTH - MARGIN_LEFT - MARGIN_RIGHT - 18) / 2
    x_izq = MARGIN_LEFT
    x_der = MARGIN_LEFT + ancho_celda + 18

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
    return y_img - 18

def crear_pdf(contrato, folio, fecha_ejecucion, sucursal, direccion, ciudad, oficina, tecnico, supervisor, tipo_servicio, estatus_final, alcance_items, evidencias_por_item, observaciones, df_materiales, destinatarios):
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

    y = titulo_seccion(c, "Alcance y evidencias fotograficas", y)
    total_con_foto = 0

    for item in alcance_items:
        numero, momento, actividad = item["numero"], item["momento"], item["actividad"]
        evidencia = evidencias_por_item.get(numero, {})
        if not hay_fotos_en_item(evidencia):
            continue
        total_con_foto += 1
        y = nueva_pagina(c, y, 170)
        y = linea_pdf(c, "Renglon", str(numero), y)
        y = linea_pdf(c, "Momento", momento, y)
        y = bloque_texto_pdf(c, "Actividad critica", actividad, y)

        if hay_fotos_antes(evidencia):
            y = fila_dos_fotos_pdf(c, f"{momento} - Antes 1", evidencia.get("antes_1"), f"{momento} - Antes 2", evidencia.get("antes_2"), y)
        if hay_fotos_despues(evidencia):
            y = fila_dos_fotos_pdf(c, f"{momento} - Despues 1", evidencia.get("despues_1"), f"{momento} - Despues 2", evidencia.get("despues_2"), y)

    if total_con_foto == 0:
        y = linea_pdf(c, "Evidencias", "No se adjuntaron fotografias.", y)

    if df_materiales is not None and not df_materiales.empty:
        y = titulo_seccion(c, "Materiales utilizados", y)
        for _, row in df_materiales.iterrows():
            cant, desc = str(row.get("Cantidad", "")).strip(), str(row.get("Descripcion", "")).strip()
            if desc:
                y = linea_pdf(c, "Material", f"{cant} - {desc}", y)

    y = bloque_texto_pdf(c, "Observaciones", observaciones, y)
    y = bloque_texto_pdf(c, "Destinatarios configurados", "\n".join(destinatarios) if destinatarios else "Sin destinatarios.", y)
    c.save()
    return pdf_path


# =========================================================
# CORREO
# =========================================================
def enviar_correo(pdf_path, contrato, folio, sucursal, oficina, nombre_archivo, correos_extra, fecha_ejecucion, destinatarios_base):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            return False, "Faltan credenciales de correo en Secrets."
        remitente, password = st.secrets["EMAIL_SENDER"], st.secrets["EMAIL_PASSWORD"]
        extras = [c.strip() for c in correos_extra.split(",") if c.strip()] if correos_extra else []
        destinatarios = list(set(destinatarios_base + extras))

        msg = EmailMessage()
        msg["Subject"] = normalizar_texto(f"Reporte Fotografico BESCO: {contrato} | TK: {folio} | Of: {oficina}")
        msg["From"] = remitente
        msg["To"] = ", ".join(destinatarios)
        msg.set_content(normalizar_texto(f"Se ha generado un nuevo reporte para:\nContrato: {contrato}\nFolio: {folio}\nSucursal: {sucursal}"))

        with open(pdf_path, "rb") as archivo:
            msg.add_attachment(archivo.read(), maintype="application", subtype="pdf", filename=nombre_archivo)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True, "Correo enviado correctamente."
    except Exception as error:
        return False, f"No se pudo enviar el correo: {error}"


def validar_reporte(contrato, folio, sucursal, tecnico):
    faltantes = []
    if not contrato: faltantes.append("Contrato")
    if not folio.strip(): faltantes.append("Folio / Ticket / OT")
    if not sucursal.strip(): faltantes.append("Sucursal / Inmueble")
    if not tecnico.strip(): faltantes.append("Tecnico asignado")
    return faltantes


# =========================================================
# APP PRINCIPAL
# =========================================================
def main():
    aplicar_estilos()

    st.markdown('<div class="titulo">📷 Reporte Fotografico por Contrato</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitulo">Configurable por contrato, alcance, evidencias desde Google Drive, PDF y correo.</div>', unsafe_allow_html=True)

    if existe_logo_besco():
        st.success(f"Logo BESCO detectado correctamente.")
    else:
        st.warning(f"No se detecto el logo BESCO en la ruta: {LOGO_PATH}")

    st.page_link("portal.py", label="⬅️ Volver al portal", use_container_width=True)

    st.subheader("1. Datos generales")
    contrato = st.selectbox("Contrato", list(CONTRATOS_CONFIG.keys()))
    config = CONTRATOS_CONFIG[contrato]
    alcance_items = ALCANCES_POR_CONTRATO.get(contrato, [])

    tipo_servicio = st.selectbox("Tipo de servicio", TIPOS_SERVICIO)
    folio = st.text_input("Folio / Ticket / OT", max_chars=40)
    fecha_ejecucion = st.date_input("Fecha de ejecucion", datetime.now())
    sucursal = st.text_input("Sucursal / Inmueble")
    direccion = st.text_input("Direccion")
    ciudad = st.text_input("Ciudad")
    oficina = st.text_input("Oficina responsable")
    tecnico = st.text_input("Tecnico asignado")
    supervisor = st.text_input("Supervisor")

    st.divider()
    st.subheader("2. Alcance del contrato y Evidencias Fotográficas")

    # Selector de origen de evidencias (Local o Google Drive)
    origen_evidencias = st.radio(
        "Selecciona el origen de las fotografías:",
        ["📁 Carga Local / Dispositivo", "☁️ Sincronizar desde Google Drive (Carpeta del Folio)"],
        horizontal=True
    )

    archivos_drive_cache = []
    if origen_evidencias == "☁️ Sincronizar desde Google Drive (Carpeta del Folio)":
        st.info(f"Buscando evidencias en Google Drive vinculadas al Folio: **{folio if folio else 'General'}**")
        if st.button("🔄 Actualizar lista de Drive"):
            st.rerun()
        archivos_drive_cache = listar_fotos_desde_drive(folio)
        if archivos_drive_cache:
            st.success(f"Se encontraron {len(archivos_drive_cache)} imágenes en la nube.")
        else:
            st.warning("No se encontraron imágenes en la nube con este Folio.")

    evidencias_por_item = {}

    for item in alcance_items:
        numero, momento, actividad = item["numero"], item["momento"], item["actividad"]
        with st.expander(f"{numero}. {momento} (Fotos opcionales)", expanded=False):
            st.markdown(f'<div class="info-box"><strong>Actividad critica:</strong><br>{actividad}</div>', unsafe_allow_html=True)

            antes_1, antes_2, despues_1, despues_2 = None, None, None, None

            if origen_evidencias == "📁 Carga Local / Dispositivo":
                antes_1 = st.file_uploader(f"{momento} - Antes 1", type=["jpg", "jpeg", "png"], key=f"{contrato}_{numero}_a1")
                antes_2 = st.file_uploader(f"{momento} - Antes 2", type=["jpg", "jpeg", "png"], key=f"{contrato}_{numero}_a2")
                despues_1 = st.file_uploader(f"{momento} - Despues 1", type=["jpg", "jpeg", "png"], key=f"{contrato}_{numero}_d1")
                despues_2 = st.file_uploader(f"{momento} - Despues 2", type=["jpg", "jpeg", "png"], key=f"{contrato}_{numero}_d2")
            else:
                nombres_disponibles = [f['name'] for f in archivos_drive_cache]
                
                sel_a1 = st.selectbox(f"{momento} - Antes 1 (Drive)", options=["-- Seleccionar --"] + nombres_disponibles, key=f"{contrato}_{numero}_drv_a1")
                if sel_a1 != "-- Seleccionar --":
                    match = next((f for f in archivos_drive_cache if f['name'] == sel_a1), None)
                    if match:
                        bytes_img = descargar_imagen_drive_a_bytes(match['id'])
                        if bytes_img: antes_1 = io.BytesIO(bytes_img)

                sel_a2 = st.selectbox(f"{momento} - Antes 2 (Drive)", options=["-- Seleccionar --"] + nombres_disponibles, key=f"{contrato}_{numero}_drv_a2")
                if sel_a2 != "-- Seleccionar --":
                    match = next((f for f in archivos_drive_cache if f['name'] == sel_a2), None)
                    if match:
                        bytes_img = descargar_imagen_drive_a_bytes(match['id'])
                        if bytes_img: antes_2 = io.BytesIO(bytes_img)

                sel_d1 = st.selectbox(f"{momento} - Despues 1 (Drive)", options=["-- Seleccionar --"] + nombres_disponibles, key=f"{contrato}_{numero}_drv_d1")
                if sel_d1 != "-- Seleccionar --":
                    match = next((f for f in archivos_drive_cache if f['name'] == sel_d1), None)
                    if match:
                        bytes_img = descargar_imagen_drive_a_bytes(match['id'])
                        if bytes_img: despues_1 = io.BytesIO(bytes_img)

                sel_d2 = st.selectbox(f"{momento} - Despues 2 (Drive)", options=["-- Seleccionar --"] + nombres_disponibles, key=f"{contrato}_{numero}_drv_d2")
                if sel_d2 != "-- Seleccionar --":
                    match = next((f for f in archivos_drive_cache if f['name'] == sel_d2), None)
                    if match:
                        bytes_img = descargar_imagen_drive_a_bytes(match['id'])
                        if bytes_img: despues_2 = io.BytesIO(bytes_img)

            evidencias_por_item[numero] = {"antes_1": antes_1, "antes_2": antes_2, "despues_1": despues_1, "despues_2": despues_2}
            cargadas = sum([1 for x in [antes_1, antes_2, despues_1, despues_2] if x is not None])
            st.info(f"Fotos seleccionadas en este renglon: {cargadas} de 4 opcionales.")

    st.divider()
    st.subheader("3. Observaciones y materiales")
    observaciones = st.text_area("Observaciones", height=120)
    
    usar_materiales = st.checkbox("Agregar materiales utilizados", value=False)
    if usar_materiales:
        df_materiales = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripcion"]), num_rows="dynamic", use_container_width=True)
    else:
        df_materiales = pd.DataFrame(columns=["Cantidad", "Descripcion"])

    st.divider()
    st.subheader("4. Estatus final")
    estatus_final = st.selectbox("Estatus final", config["estatus"])

    st.divider()
    st.subheader("5. Generar PDF y enviar correo")
    destinatarios_base = config["destinatarios"].copy()
    if "gerardo.mendez@besco.mx" not in destinatarios_base:
        destinatarios_base.append("gerardo.mendez@besco.mx")

    correos_extra = st.text_input("Correos adicionales separados por coma")
    faltantes = validar_reporte(contrato=contrato, folio=folio, sucursal=sucursal, tecnico=tecnico)

    if faltantes:
        st.markdown(f'<div class="warning-box">Faltan campos obligatorios: {", ".join(faltantes)}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ok-box">Datos minimos completos. Puedes generar el PDF.</div>', unsafe_allow_html=True)

    generar = st.button("📄 Generar PDF", type="primary", use_container_width=True, disabled=bool(faltantes))

    if generar:
        with st.spinner("Generando PDF y comprimiendo imagenes..."):
            try:
                pdf_path = crear_pdf(
                    contrato=contrato, folio=folio, fecha_ejecucion=fecha_ejecucion,
                    sucursal=sucursal, direccion=direccion, ciudad=ciudad, oficina=oficina,
                    tecnico=tecnico, supervisor=supervisor, tipo_servicio=tipo_servicio,
                    estatus_final=estatus_final, alcance_items=alcance_items,
                    evidencias_por_item=evidencias_por_item, observaciones=observaciones,
                    df_materiales=df_materiales, destinatarios=destinatarios_base
                )
                nombre_pdf = crear_nombre_archivo(f"Reporte_Fotografico_{contrato}_{folio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")

                st.session_state["rf_contrato_pdf_path"] = pdf_path
                st.session_state["rf_contrato_nombre_pdf"] = nombre_pdf
                st.session_state["rf_contrato_fecha"] = fecha_ejecucion.strftime("%d/%m/%Y")
                st.session_state["rf_contrato_datos_mail"] = {
                    "contrato": contrato, "folio": folio, "sucursal": sucursal,
                    "oficina": oficina, "correos_extra": correos_extra, "destinatarios": destinatarios_base
                }
                st.success("PDF generado correctamente.")
            except Exception as error:
                st.error(f"No se pudo generar el PDF: {error}")

    if "rf_contrato_pdf_path" in st.session_state:
        pdf_path = st.session_state["rf_contrato_pdf_path"]
        nombre_pdf = st.session_state["rf_contrato_nombre_pdf"]

        with open(pdf_path, "rb") as archivo_pdf:
            st.download_button("⬇️️ Descargar PDF", data=archivo_pdf, file_name=nombre_pdf, mime="application/pdf", use_container_width=True)

        if st.button("📨 Enviar reporte por correo", use_container_width=True):
            datos_mail = st.session_state["rf_contrato_datos_mail"]
            with st.spinner("Enviando correo..."):
                enviado, mensaje = enviar_correo(
                    pdf_path=pdf_path, contrato=datos_mail["contrato"], folio=datos_mail["folio"],
                    sucursal=datos_mail["sucursal"], oficina=datos_mail["oficina"], nombre_archivo=nombre_pdf,
                    correos_extra=datos_mail["correos_extra"], fecha_ejecucion=st.session_state["rf_contrato_fecha"],
                    destinatarios_base=datos_mail["destinatarios"]
                )
            if enviado: st.success(mensaje)
            else: st.warning(mensaje)

    st.markdown('<div class="footer">Sistema Operativo - Grupo Besco | Reporte Fotografico por Contrato</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
