import streamlit as st
import gspread
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
import uuid
import os
from PIL import Image
import google.generativeai as genai

# --- CONEXIÓN GOOGLE SHEETS ---
def obtener_gspread_client():
    # Utilizamos el método nativo y más directo de gspread para conectarnos
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

# --- ENVÍO DE CORREOS AUTOMATIZADO ---
def enviar_correo(pdf_bytes, cliente, folio, nombre_archivo, corr_extra, destinatarios):
    try:
        remitente = st.secrets["EMAIL_SENDER"]
        password = st.secrets["EMAIL_PASSWORD"]
        
        lista_correos = destinatarios.copy()
        if corr_extra:
            lista_correos.extend([c.strip() for c in corr_extra.split(",")])
        destinatarios_totales = list(set(lista_correos))
        
        msg = EmailMessage()
        msg['Subject'] = f"Reporte: {cliente} | Folio: {folio}"
        msg['From'] = remitente
        msg['To'] = ", ".join(destinatarios_totales)
        msg.set_content("Adjunto encontrarás el documento generado automáticamente por el sistema de Grupo Besco.")
        
        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=nombre_archivo)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        return False

# --- ANÁLISIS DE REPORTES CON GEMINI (IA) ---
def analizar_reporte_con_gemini(datos):
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        respuesta = model.generate_content(f"Actúa como ingeniero senior de Besco. Resume este reporte técnico detalladamente: {datos}")
        return respuesta.text
    except Exception as e:
        return f"Error al conectar con la IA: {e}"

# --- GENERADOR DE PDF BESCO ---
class BESCO_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'REPORTE TECNICO BESCO', 0, 1, 'R')
        
    def add_custom_section(self, title):
        self.set_fill_color(30, 58, 95)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, title, 0, 1, 'L', fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)
        
    def photo_grid(self, title, photos):
        if not photos:
            return
        self.add_custom_section(title)
        
        x_start = self.get_x()
        y_start = self.get_y()
        img_width = 80
        max_height = 0
        
        for i, foto in enumerate(photos):
            if self.get_y() > 250: 
                self.add_page()
                y_start = self.get_y()
                
            temp_p = f"temp_{uuid.uuid4().hex}.jpg"
            try:
                Image.open(foto).convert("RGB").save(temp_p, format="JPEG")
                
                if i % 2 == 0 and i > 0:
                    y_start += max_height + 5
                    self.set_xy(x_start, y_start)
                    max_height = 0
                    
                x_pos = x_start if i % 2 == 0 else x_start + img_width + 10
                self.image(temp_p, x=x_pos, y=y_start, w=img_width)
                
                max_height = max(max_height, img_width * 0.75) 
            except Exception as e:
                st.error(f"Error procesando imagen: {e}")
            finally:
                if os.path.exists(temp_p):
                    os.remove(temp_p)
        
        self.set_y(y_start + max_height + 10)
