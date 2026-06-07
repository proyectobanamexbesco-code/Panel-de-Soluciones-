import streamlit as st
import sys
import os

# Esto asegura que la app encuentre tu archivo utils.py en la raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import BESCO_PDF, enviar_correo

# Configuración individual de la página
st.set_page_config(page_title="Reporte General | Besco", page_icon="📸")

st.title("📸 Reporte Fotográfico General")

with st.form("reporte_general_form"):
    cliente = st.text_input("Nombre del Cliente / Proyecto")
    folio = st.text_input("Folio o Número de Ticket")
    tecnico = st.text_input("Técnico a cargo")
    
    st.markdown("### Evidencia Fotográfica")
    fotos_antes = st.file_uploader("Fotos Antes del servicio", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    fotos_despues = st.file_uploader("Fotos Después del servicio", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    
    st.markdown("### Envío de Resultados")
    corr_extra = st.text_input("Correos adicionales (separados por coma)")
    
    # Botón principal de ejecución
    submit = st.form_submit_button("Generar PDF y Enviar Correo")
    
    if submit:
        if cliente and folio and tecnico:
            st.info("Generando documento PDF...")
            
            # 1. Crear el PDF usando la clase centralizada BESCO_PDF
            pdf = BESCO_PDF()
            pdf.add_page()
            
            # Datos del reporte
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, f"Cliente: {cliente}", ln=True)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Folio: {folio}", ln=True)
            pdf.cell(0, 10, f"Tecnico: {tecnico}", ln=True)
            pdf.ln(5)
            
            # Inserción dinámica de las cuadrículas de fotos
            pdf.photo_grid("Evidencia: Antes", fotos_antes)
            pdf.photo_grid("Evidencia: Despues", fotos_despues)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            # 2. Configurar destinatarios base (puedes añadir o quitar de esta lista)
            destinatarios_base = ["gerardo.mendez@besco.mx"]
            
            # 3. Enviar el correo
            st.info("Enviando correo con evidencia adjunta...")
            if enviar_correo(pdf_bytes, cliente, folio, f"Reporte_{folio}.pdf", corr_extra, destinatarios_base):
                st.success("¡Reporte generado y enviado con éxito!")
        else:
            st.warning("Por favor, llena los campos de Cliente, Folio y Técnico obligatoriamente.")
