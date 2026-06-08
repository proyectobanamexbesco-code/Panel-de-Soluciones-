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
import base64
from pypdf import PdfWriter

# --- LOGO BESCO EMBEBIDO EN BASE64 ---
LOGO_B64 = """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A6I2aYVNt0lxGGUdw8WeAuH4EtJCz9FUVeqlhSePUjCMG1W02i1F05umC265zWN1VBwpqije6LwXt7tBDNt4yRs5vkWkj71yVznB8m05yeuxDLrZJRXGheWvY4btkbueMjHeTmO8wR/t3C7RbD2CjjWLQfT/AFts8duy+1kVNMD8JcabaOqpifRrtju33a7dp9t9itd1vSP0klODxNfidL9nnHz4QrSoXUea3qPLx96L6ZXdNbNfNbo5EMe+N7ZI3ua9hDmuadiCPIgrMI9aNYI6IW1mqmXNpWt4CEXqpDePt9vyU5579H3qtYKiWXCbra8mogSWB0nwdSB6bsf+j8vUP7+wUf8A8z7qP8bwf7mk+/v9Y0fH8/G2WlPTtSt24qEl6Jv+B6Jp8V8KaxTVadzRljpzuKa+U8NfQh+pqaisqJKusqJJ55XF8kkry573HzJJ7kr9bXa7je7jTWi0UM9ZXVkrYaengYXySvcdg1oHclbK4b9H3rHe52Py242fGqTcF5fN8XOB9zI/kP75AtvtFOmHTTRKL42y0b7ne5I+Et3rgHTbHzbGB8sTf+z3PqSruy4dvLqalWXJHxb6mB4h9qmg6LRcLGar1cbKH3V2zLpj/bl+R+XSxocNEdOI7XcmRvv92e2tu0jdiGybbMhafVrG9t/VxcfVTRsPYKgYwDYNA/cvS6HQoQtqcaVJYitkeV9S1G41a7qX13LNSo22/X8l0XkjzwZ58G/kqhrR5NA/cqoqpY4RTi32CcW+wVUQkpsPYL47vUz0Ntqq6koH1s9PBJLHTRuDXTva0kRgnsC4jYE+pX2qmwPmniCGLTrFqfN4cdz0Qu4L64w+JBM9rTA6d7WSgSRtP97DCefA77khgLd7ng+pGpGT1dZRXvSirsbhbpaykqamaQQvlD+LKdxMYdyPmXbeXk0juZU4t/ZH5KnBv7I/JVpVINPEEvmyMPuQ9juca4Xq7RUdZgtDboN6MyS1EM7WHxKWWWZofy3aWSMiZy4OG8/HY+G4mTMUrLrdMYtNxyC3ChudXQwT1tKAdoJ3RtMkffv8riR39lduLf2R+SbAeQXzUmp9IpBLA2HsnFv7I/JVRUyTy6NjgWuY0gjYgjzVgvmn2D5JRQ22+Ylaa6kp5nVEdPNSMdG2UjYvDdtuRBPf71kKID8aalp6OnipKWCOGCBjY4o42hrWMaNg0AeQA7bL9QAPIKqIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCIiAIiIAiIgCoAB5BVRAU4t9gqcGeXAfkvSIOpTi3y4j8k4tA24j8lVEAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREAREQBERAEREB/9k="""

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
        # Logo embebido en base64
        try:
            logo_bytes = base64.b64decode(LOGO_B64)
            img_logo = Image.open(io.BytesIO(logo_bytes)).convert("RGB")
            orig_w, orig_h = img_logo.size
            final_h = 22
            final_w = orig_w * (final_h / orig_h)
            with archivo_temporal(suffix=".jpg") as tmp_logo:
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
