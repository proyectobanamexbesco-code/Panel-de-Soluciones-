import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from PIL import Image
import os
import smtplib
from email.message import EmailMessage
import io
import uuid
import tempfile
import contextlib
from pypdf import PdfWriter

# --- CONFIGURACIÓN DE RUTAS Y LOGOTIPO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGOS_POSIBLES = ["logo besco 2026.jpeg", "logo.png", "logo.jpg"]
LOGO_PATH = None
for logo in LOGOS_POSIBLES:
    path = os.path.join(BASE_DIR, logo)
    if os.path.exists(path):
        LOGO_PATH = path
        break

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BESCO | Evidencia Técnica", layout="wide")

st.markdown("""
    <style>
    .stApp { color: #262730 !important; }
    .stButton > button { color: white !important; background-color: #E21836 !important; }
    h1, h2, h3 { color: #1E3A5F !important; }
    div[data-testid="stExpander"] div[role="button"] p { font-weight: bold !important; color: #1E3A5F !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE LIMPIEZA DE CARACTERES ESPECIALES ---
def limpiar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    reemplazos = {
        '•': '-', '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u2013': '-', '\u2014': '-', '\u200b': '', '\r': '', '°': ' grados'
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto.encode('latin-1', 'replace').decode('latin-1')

# --- GESTOR DE ARCHIVOS TEMPORALES ---
@contextlib.contextmanager
def archivo_temporal(suffix=".jpg"):
    """Crea un archivo temporal y garantiza su eliminación al salir del bloque."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    try:
        yield tmp.name
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(tmp.name)

def imagen_a_temp(file_obj):
    """Convierte un archivo de imagen a JPEG temporal. Retorna context manager."""
    return archivo_temporal(suffix=".jpg")

# --- CLASE PDF PROFESIONAL ---
class BESCO_PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.section_count = 1
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(left=12, top=12, right=12)

    def header(self):
        # Logo
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            try:
                with archivo_temporal(suffix=".jpg") as tmp_logo:
                    img_logo = Image.open(LOGO_PATH).convert("RGB")
                    orig_w, orig_h = img_logo.size
                    final_h = 22
                    final_w = orig_w * (final_h / orig_h)
                    img_logo.save(tmp_logo, format="JPEG", quality=95)
                    self.image(tmp_logo, x=12, y=8, w=final_w, h=final_h)
            except Exception:
                pass

        # Título derecho
        self.set_font('Arial', 'B', 11)
        self.set_text_color(30, 58, 95)
        self.set_xy(0, 10)
        self.cell(self.w - 12, 6, limpiar_texto('REPORTE DE SERVICIO TÉCNICO'), 0, 1, 'R')

        self.set_font('Arial', '', 8)
        self.set_text_color(120, 120, 120)
        self.set_x(0)
        self.cell(self.w - 12, 5, limpiar_texto(f"Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), 0, 1, 'R')

        # Línea separadora
        self.set_draw_color(226, 24, 54)
        self.set_line_width(0.8)
        self.line(12, 33, self.w - 12, 33)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.ln(28)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(200, 200, 200)
        self.line(12, self.get_y(), self.w - 12, self.get_y())
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, limpiar_texto(f'Página {self.page_no()} | Documento confidencial BESCO'), 0, 0, 'C')

    def add_custom_section(self, title):
        if self.get_y() > 245:
            self.add_page()
        # Barra de sección con acento rojo
        self.set_fill_color(30, 58, 95)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(255, 255, 255)
        self.cell(4, 8, '', 0, 0, 'L', fill=True)
        self.set_fill_color(226, 24, 54)
        self.cell(2, 8, '', 0, 0, 'L', fill=True)
        self.set_fill_color(30, 58, 95)
        self.cell(self.w - 30, 8, limpiar_texto(f"  {self.section_count}. {title.upper()}"), 0, 1, 'L', fill=True)
        self.section_count += 1
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def tabla_info(self, datos):
        """Renderiza una tabla de dos columnas (etiqueta | valor) con estilo limpio."""
        self.set_font('Arial', '', 9)
        col_label = 50
        col_valor = self.w - 12 - 12 - col_label

        for etiqueta, valor in datos:
            y_antes = self.get_y()
            # Medir altura necesaria para el valor (multi_cell)
            # Usamos get_string_width para determinar si necesitamos salto
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(240, 243, 248)
            self.cell(col_label, 7, limpiar_texto(etiqueta), 1, 0, 'L', fill=True)
            self.set_font('Arial', '', 9)
            self.set_fill_color(255, 255, 255)
            self.cell(col_valor, 7, limpiar_texto(str(valor)), 1, 1, 'L', fill=True)
        self.ln(3)

    def tabla_mediciones(self, meds):
        """Tabla horizontal para mediciones técnicas (A/C, etc.)."""
        if not meds:
            return
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        ancho = (self.w - 24) / len(meds)
        for k in meds:
            self.cell(ancho, 7, limpiar_texto(k), 1, 0, 'C', fill=True)
        self.ln()
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(255, 255, 255)
        for v in meds.values():
            self.cell(ancho, 7, limpiar_texto(str(v) if v else '-'), 1, 0, 'C')
        self.ln(5)

    def bloque_texto(self, etiqueta, contenido, color_fondo=(248, 248, 252)):
        """Bloque de texto largo con etiqueta y fondo sutil."""
        if not contenido:
            return
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, limpiar_texto(f"  {etiqueta}"), 0, 1, 'L', fill=True)
        self.set_font('Arial', '', 9)
        self.set_text_color(40, 40, 40)
        self.set_fill_color(*color_fondo)
        self.multi_cell(0, 5, limpiar_texto(contenido), border=1, fill=True)
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def photo_grid(self, title, photos, prefix="img"):
        """Grilla de fotos 2 columnas con pie de foto y relación de aspecto correcta."""
        if not photos:
            return
        if self.get_y() > 230:
            self.add_page()

        self.set_font('Arial', 'BI', 9)
        self.set_text_color(30, 58, 95)
        self.cell(0, 6, limpiar_texto(f"  Fotografías — {title}"), 0, 1, 'L')
        self.set_text_color(0, 0, 0)

        MAX_W = 89
        MAX_H = 66
        ESPACIO_H = 72   # alto de celda por fila (foto + pie)
        MARGEN_X = 12

        for i, foto in enumerate(photos):
            try:
                foto.seek(0)
                img = Image.open(foto).convert("RGB")

                # Calcular dimensiones respetando aspecto
                img_w, img_h = img.size
                escala = min(MAX_W / img_w, MAX_H / img_h)
                final_w = img_w * escala
                final_h = img_h * escala

                col = i % 2
                if col == 0 and i > 0 and (self.get_y() + ESPACIO_H > 270):
                    self.add_page()

                with archivo_temporal(suffix=".jpg") as tmp_img:
                    img.save(tmp_img, format="JPEG", quality=90)
                    y_act = self.get_y()
                    x_pos = MARGEN_X + col * 95 + (MAX_W - final_w) / 2
                    self.image(tmp_img, x=x_pos, y=y_act, w=final_w, h=final_h)

                # Pie de foto
                self.set_xy(MARGEN_X + col * 95, y_act + MAX_H + 1)
                self.set_font('Arial', 'I', 7)
                self.set_text_color(100, 100, 100)
                self.cell(MAX_W, 4, limpiar_texto(f"Foto {i+1} — {title}"), 0, 0, 'C')
                self.set_text_color(0, 0, 0)

                if col == 1 or i == len(photos) - 1:
                    self.set_y(y_act + ESPACIO_H)

            except Exception as e:
                self.set_font('Arial', 'I', 8)
                self.cell(0, 6, limpiar_texto(f"[Error al cargar imagen {i+1}]"), 0, 1)

        self.ln(4)

    def folio_grid(self, title, photo_files):
        """Una foto del folio por página, centrada y a máximo tamaño."""
        if not photo_files:
            return
        for i, foto in enumerate(photo_files[:4]):
            try:
                self.add_page()
                self.add_custom_section(f"{title} — Evidencia {i+1}")
                foto.seek(0)
                img = Image.open(foto).convert("RGB")
                avail_w, avail_h = 186, 220
                img_w, img_h = img.size
                escala = min(avail_w / img_w, avail_h / img_h)
                final_w, final_h = img_w * escala, img_h * escala

                with archivo_temporal(suffix=".jpg") as tmp_folio:
                    img.save(tmp_folio, format="JPEG", quality=95)
                    x_center = 12 + (avail_w - final_w) / 2
                    self.image(tmp_folio, x=x_center, y=self.get_y() + 5, w=final_w, h=final_h)
            except Exception:
                self.set_font('Arial', 'I', 9)
                self.cell(0, 8, limpiar_texto(f"[Error al cargar folio {i+1}]"), 0, 1)

    def separador_equipo(self):
        """Línea visual entre equipos."""
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(12, self.get_y(), self.w - 12, self.get_y())
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.ln(5)


# --- FUNCIÓN ENVÍO DE CORREO SMTP ---
def enviar_correo(pdf_bytes, cliente, folio, sucursal, oficina, nombre_archivo, correos_extra, fecha_ejec, lista_destinatarios):
    try:
        if "EMAIL_SENDER" not in st.secrets or "EMAIL_PASSWORD" not in st.secrets:
            st.error("❌ Error de configuración: No se encontraron las claves 'EMAIL_SENDER' o 'EMAIL_PASSWORD' en los Secrets.")
            return False

        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        extra = [c.strip() for c in correos_extra.split(",") if c.strip()] if correos_extra else []
        destinatarios = list(set(lista_destinatarios + extra))

        msg = EmailMessage()
        msg['Subject'] = limpiar_texto(f"Reporte Técnico BESCO: {cliente} | TK: {folio} | Of: {oficina}")
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios)
        msg.set_content(limpiar_texto(
            f"Se ha generado un nuevo reporte desde el Sistema de Evidencia Técnica BESCO.\n\n"
            f"Fecha Ejecución: {fecha_ejec}\n"
            f"Oficina: {oficina}\n"
            f"Cliente: {cliente}\n"
            f"Folio: {folio}\n"
            f"Sucursal: {sucursal}"
        ))
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"❌ Error de conexión SMTP: {e}")
        return False


# ==========================================
# INTERFAZ GRÁFICA DE STREAMLIT
# ==========================================
st.title("📑 Portal de Soluciones BESCO — Reporte General")

st.subheader("1. Identificación General del Servicio")
c_g1, c_g2, c_g3 = st.columns([2, 1, 1.5])
cliente = c_g1.text_input("Cliente")
folio = c_g2.text_input("Folio / OT / TK", max_chars=20)
fecha_ejecucion = c_g3.date_input("Fecha de Ejecución", datetime.now())

col_loc1, col_loc2 = st.columns(2)
sucursal = col_loc1.text_input("Sucursal / Inmueble")

lista_oficinas = [
    "Acapulco", "Toluca", "Pachuca", "Michoacán", "Zonas/ CDMX", "CDMX",
    "Ben & Company", "BX+", "Emerson", "Odoo", "Tampico"
]
oficina = col_loc2.selectbox("Oficina Responsable", lista_oficinas)

c_t1, c_t2, c_t3, c_t4 = st.columns(4)
tecnico = c_t1.text_input("Técnico Asignado")
supervisor = c_t2.text_input("Supervisor")
tipo_serv = c_t3.selectbox("Servicio", ["Preventivo", "Correctivo", "Emergencia"])
referencia = c_t4.selectbox("Referencia", ["Con Ticket", "Sin Ticket"])

st.markdown("---")

st.subheader("2. Evidencia Documental (Reporte Físico)")
st.info("📌 Puede subir hasta 4 fotos (JPG/PNG) y/o archivos PDF del reporte firmado.")
archivos_folio = st.file_uploader("Subir Folio BESCO", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

st.markdown("---")

st.subheader("3. Equipos a Reportar")
num_equipos = st.number_input("¿Cuántos equipos se atendieron?", min_value=1, max_value=20, value=1)

leyendas_default = {
    "Conservación": "SE REALIZA REAPRIETE DE TORNILLERIA Y LUBRICACIÓN DE CHAPAS, BISAGRAS, SE HACE REVISIÓN DE ESTADO DE PINTURA, PISOS EXTINTORES Y MOBILIARIO.",
    "Hidrosanitario": "SE REALIZA REVISIÓN DE CESPOL, MEZCLADORA, MANGUERAS, LLAVES, WC, DESPACHADORES, EXTRACTORES Y CONEXIONES, SE DEJA FUNCIONANDO CORRECTAMENTE.",
    "Tableros Eléctricos": "SE REALIZA LIMPIEZA, REAPRIETE DE TORNILLERIA, TOMA DE AMPERAJES Y VOLTAJES, SE DEJA FUNCIONANDO CORRECTAMENTE.",
    "Iluminación": "SE REALIZA REVISIÓN GENERAL DE LÁMPARAS, SE CAMBIAN LAMPARAS FUNDIDAS, SE DEJA FUNCIONANDO CORRECTAMENTE.",
    "Aire Acondicionado": "SE REALIZA LIMPIEZA GENERAL DE SERPENTINES, TOMADO PRESIÓN DE REFRIGERANTE, VOLTAJES, AMPERAJES, REAPRIETE DE CONEXIONES, LIMPIEZA DE FILTROS, SE DEJA FUNCIONANDO CORRECTAMENTE."
}

equipos_data = []
for i in range(num_equipos):
    with st.expander(f"CONFIGURACIÓN EQUIPO {i+1}", expanded=True):
        cols_cat = st.columns(2)
        categorias_opciones = ["Ninguna", "Aire Acondicionado", "Tableros Eléctricos", "Hidroneumático", "Conservación", "Hidrosanitario", "Iluminación", "Otros"]
        esp = cols_cat[0].selectbox("Categoría", categorias_opciones, key=f"esp_{i}")
        estatus = cols_cat[1].selectbox("Estatus Final", ["Operando correctamente", "Operando con observaciones", "No queda operando"], key=f"est_{i}")

        meds, otros = {}, ""
        if esp == "Aire Acondicionado":
            cols = st.columns(4)
            meds['Succión'] = cols[0].text_input("Succión", key=f"s_{i}")
            meds['Descarga'] = cols[1].text_input("Descarga", key=f"d_{i}")
            meds['Salida'] = cols[2].text_input("Salida", key=f"t_{i}")
            meds['Amperaje'] = cols[3].text_input("Amp", key=f"a_{i}")
        elif esp == "Otros":
            otros = st.text_area("Detalles/Mediciones:", key=f"o_{i}")

        ca1, ca2, ca3 = st.columns(3)
        tag = ca1.text_input("TAG", key=f"tg_{i}")
        marca = ca2.text_input("Marca", key=f"mr_{i}")
        cap = ca3.text_input("Capacidad", key=f"cp_{i}")

        texto_defecto = leyendas_default.get(esp, "")
        actividades = st.text_area("Actividades Realizadas", value=texto_defecto, height=80, key=f"act_{i}_{esp}")
        com = st.text_area("Comentarios Extras", key=f"com_{i}")

        fa = st.file_uploader("Fotos ANTES", accept_multiple_files=True, key=f"fa_{i}")
        fd = st.file_uploader("Fotos DESPUÉS", accept_multiple_files=True, key=f"fd_{i}")

        equipos_data.append({
            "numero": i+1, "esp": esp, "estatus": estatus, "actividades": actividades,
            "meds": meds, "otros": otros, "tag": tag, "marca": marca, "cap": cap,
            "com": com, "fa": fa, "fd": fd
        })

st.subheader("4. Materiales Utilizados")
df_mat = st.data_editor(pd.DataFrame(columns=["Cantidad", "Descripción"]), num_rows="dynamic")

st.markdown("---")
st.subheader("5. Envío de Reporte")

mapeo_correos = {
    "Acapulco": ["itzallana.vazquez@besco.mx", "gerardo.fuentes@besco.mx"],
    "Toluca": ["policarpo.rosaliano@besco.mx", "monica.iniestra@besco.mx"],
    "Pachuca": ["german.constantino@besco.mx"],
    "Michoacán": ["cristobal.rodriguez@besco.mx", "ximena.acosta@besco.mx", "javier.zamano@besco.mx"],
    "Zonas/ CDMX": ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "brenda.cervantes@besco.mx"],
    "CDMX": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx"],
    "Ben & Company": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx"],
    "BX+": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "patricia.cortes@besco.mx"],
    "Emerson": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "patricia.cortes@besco.mx"],
    "Odoo": ["gerardo.mendez@besco.mx", "alejandro.ramirez@besco.mx", "dorian.rodriguez@besco.mx"],
    "Tampico": ["ingrid.lucio@besco.mx", "joel.perez@besco.mx", "gerardo.mendez@besco.mx"]
}

dest_oficina = mapeo_correos.get(oficina, ["gerardo.mendez@besco.mx"])
if "gerardo.mendez@besco.mx" not in dest_oficina:
    dest_oficina.append("gerardo.mendez@besco.mx")

st.info(f"📧 Destinatarios automáticos: {', '.join(dest_oficina)}")
correos_extra = st.text_input("Correos adicionales (separados por coma)")

# --- GENERACIÓN DEL PDF ---
def generar_pdf(cliente, folio, fecha_ejecucion, oficina, sucursal, tecnico, supervisor,
                tipo_serv, referencia, equipos_data, df_mat, archivos_folio):

    pdf = BESCO_PDF()
    pdf.add_page()

    # --- Sección 1: Información General ---
    pdf.add_custom_section("Información General del Servicio")
    f_ejec_str = fecha_ejecucion.strftime('%d/%m/%Y')

    color_op = {
        "Operando correctamente": (0, 150, 80),
        "Operando con observaciones": (200, 130, 0),
        "No queda operando": (200, 30, 30),
    }

    datos_generales = [
        ("Cliente", cliente),
        ("Folio / OT / TK", folio),
        ("Fecha de Ejecución", f_ejec_str),
        ("Oficina Responsable", oficina),
        ("Sucursal / Inmueble", sucursal if sucursal else "—"),
        ("Técnico Asignado", tecnico if tecnico else "—"),
        ("Supervisor", supervisor if supervisor else "—"),
        ("Tipo de Servicio", f"{tipo_serv} ({referencia})"),
    ]
    pdf.tabla_info(datos_generales)

    # --- Resumen de equipos ---
    if len(equipos_data) > 1:
        pdf.add_custom_section("Resumen de Equipos")
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(30, 58, 95)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(10, 7, "#", 1, 0, 'C', fill=True)
        pdf.cell(50, 7, "Categoría", 1, 0, 'C', fill=True)
        pdf.cell(30, 7, "TAG", 1, 0, 'C', fill=True)
        pdf.cell(96, 7, "Estatus Final", 1, 1, 'C', fill=True)
        pdf.set_text_color(0, 0, 0)

        for eq in equipos_data:
            pdf.set_font('Arial', '', 9)
            pdf.set_fill_color(245, 245, 245)
            r, g, b = color_op.get(eq['estatus'], (0, 0, 0))
            pdf.cell(10, 6, str(eq['numero']), 1, 0, 'C')
            pdf.cell(50, 6, limpiar_texto(eq['esp']), 1, 0, 'L')
            pdf.cell(30, 6, limpiar_texto(eq['tag'] or '—'), 1, 0, 'C')
            pdf.set_text_color(r, g, b)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(96, 6, limpiar_texto(eq['estatus']), 1, 1, 'L')
            pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

    # --- Sección por equipo ---
    for eq in equipos_data:
        if pdf.get_y() > 230:
            pdf.add_page()

        pdf.add_custom_section(f"EQUIPO {eq['numero']}: {eq['esp']}")

        # Ficha técnica del equipo
        datos_eq = []
        if eq['tag']:    datos_eq.append(("TAG", eq['tag']))
        if eq['marca']:  datos_eq.append(("Marca", eq['marca']))
        if eq['cap']:    datos_eq.append(("Capacidad", eq['cap']))

        r, g, b = color_op.get(eq['estatus'], (0, 0, 0))
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(r, g, b)
        pdf.cell(0, 7, limpiar_texto(f"  Estatus Final: {eq['estatus']}"), 0, 1, 'L')
        pdf.set_text_color(0, 0, 0)

        if datos_eq:
            pdf.tabla_info(datos_eq)

        # Mediciones técnicas (A/C)
        valid_meds = {k: v for k, v in eq['meds'].items() if v}
        if valid_meds:
            pdf.tabla_mediciones(valid_meds)

        # Detalles libres (Otros)
        if eq['otros']:
            pdf.bloque_texto("Detalles / Mediciones", eq['otros'])

        # Actividades
        if eq['actividades']:
            pdf.bloque_texto("Actividades Realizadas", eq['actividades'])

        # Comentarios
        if eq['com']:
            pdf.bloque_texto("Comentarios Extras", eq['com'], color_fondo=(255, 252, 240))

        # Fotos
        pdf.photo_grid(f"ANTES — Equipo {eq['numero']}", eq['fa'], f"antes_{eq['numero']}")
        pdf.photo_grid(f"DESPUÉS — Equipo {eq['numero']}", eq['fd'], f"despues_{eq['numero']}")

        pdf.separador_equipo()

    # --- Materiales ---
    df_c = df_mat.dropna(subset=["Descripción"])
    if not df_c.empty:
        if pdf.get_y() > 220:
            pdf.add_page()
        pdf.add_custom_section("Materiales Utilizados")
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(30, 58, 95)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(30, 7, "CANTIDAD", 1, 0, 'C', fill=True)
        pdf.cell(pdf.w - 54, 7, limpiar_texto("DESCRIPCIÓN"), 1, 1, 'C', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 9)
        for idx, (_, row) in enumerate(df_c.iterrows()):
            fill = idx % 2 == 0
            pdf.set_fill_color(245, 247, 252) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(30, 7, limpiar_texto(str(row["Cantidad"])), 1, 0, 'C', fill=fill)
            pdf.cell(pdf.w - 54, 7, limpiar_texto(str(row["Descripción"])), 1, 1, 'L', fill=fill)

    # --- Folio BESCO (imágenes) ---
    fotos_folio = [f for f in archivos_folio if f and "image" in f.type]
    if fotos_folio:
        pdf.folio_grid("FOLIO BESCO", fotos_folio)

    # Serializar PDF
    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')

    # Fusionar PDFs adjuntos
    pdfs_folio = [f for f in archivos_folio if f and f.type == "application/pdf"]
    if pdfs_folio:
        merger = PdfWriter()
        merger.append(io.BytesIO(pdf_bytes))
        for p in pdfs_folio:
            p.seek(0)
            merger.append(p)
        out = io.BytesIO()
        merger.write(out)
        pdf_bytes = out.getvalue()

    return pdf_bytes, f_ejec_str


# --- BOTÓN UNIFICADO ---
if st.button("🚀 Generar y Enviar Reporte Final", type="primary", use_container_width=True):
    if not cliente or not folio:
        st.error("⚠️ Los campos Cliente y Folio son obligatorios para generar el reporte.")
    else:
        with st.spinner("Construyendo documento PDF y procesando imágenes..."):
            try:
                pdf_bytes, f_ejec_str = generar_pdf(
                    cliente, folio, fecha_ejecucion, oficina, sucursal,
                    tecnico, supervisor, tipo_serv, referencia,
                    equipos_data, df_mat, archivos_folio
                )

                nom_archivo = f"Reporte_BESCO_{cliente}_{folio}.pdf".replace(" ", "_")

                correo_enviado = enviar_correo(
                    pdf_bytes, cliente, folio, sucursal, oficina,
                    nom_archivo, correos_extra, f_ejec_str, dest_oficina
                )

                if correo_enviado:
                    st.success("✅ Reporte enviado exitosamente por correo y listo para descarga.")
                else:
                    st.warning("⚠️ El PDF se generó correctamente, pero hubo un problema con el envío SMTP. Descárgalo manualmente:")

                st.download_button(
                    "📥 Descargar PDF del Reporte",
                    data=pdf_bytes,
                    file_name=nom_archivo,
                    mime="application/pdf",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"❌ Error al generar el PDF: {e}")
                st.exception(e)
