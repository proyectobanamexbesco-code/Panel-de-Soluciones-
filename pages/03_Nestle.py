import streamlit as st
import pandas as pd
import sys
import os

# Esto asegura que la app encuentre tu archivo utils.py en la raíz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import obtener_gspread_client, enviar_correo, BESCO_PDF, analizar_reporte_con_gemini

# Configuración individual de la página
st.set_page_config(page_title="Módulo Nestlé | Besco", page_icon="📑")

st.title("📑 Sistema de Evidencia Técnica: Nestlé")

# 1. Carga de estructura Nestlé
# Usamos st.cache_data para que no descargue el Excel completo cada vez que haces un clic, haciendo la app rapidísima
@st.cache_data(ttl=600)
def cargar_datos_nestle():
    try:
        client = obtener_gspread_client()
        data = client.open("NESTLE").worksheet("NESTLE").get_all_records()
        df = pd.DataFrame(data)
        df.columns = [str(c).upper().strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al cargar base de Nestlé. Verifica la conexión o el nombre de la hoja: {e}")
        return pd.DataFrame()

df = cargar_datos_nestle()

if not df.empty:
    # 2. Filtros
    area = st.selectbox("Área", sorted(df["AREA"].dropna().unique()))
    df_area = df[df["AREA"] == area]
    
    st.markdown("### Levantamiento de equipos Nestlé")
    equipo = st.selectbox("Selecciona el Equipo", df_area["ITEM"].astype(str) + " - " + df_area["DESCRIPCION DE EQUIPOS"])
    
    # 3. Formulario de Levantamiento
    with st.form("reporte_nestle"):
        # Lista desplegable para técnicos habituales
        tecnico = st.selectbox("Técnico a cargo", ["Oscar Salto", "Germán Constantino", "Andrés Mayagoitia", "Otro"])
        if tecnico == "Otro":
            tecnico = st.text_input("Especificar nombre del técnico")
            
        obs = st.text_area("Observaciones técnicas")
        fotos_antes = st.file_uploader("Fotos Antes", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        fotos_despues = st.file_uploader("Fotos Después", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        
        # Botón principal de ejecución
        submit = st.form_submit_button("Generar y Enviar Reporte")
        
        if submit:
            if obs:
                st.info("Generando documento PDF...")
                
                # Generación de PDF (Clase BESCO_PDF)
                pdf = BESCO_PDF()
                pdf.add_page()
                
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, f"Levantamiento Nestle: {equipo}", ln=True)
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"Area: {area}", ln=True)
                pdf.cell(0, 10, f"Tecnico: {tecnico}", ln=True)
                pdf.ln(5)
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Observaciones:", ln=True)
                pdf.set_font("Arial", '', 12)
                pdf.multi_cell(0, 10, obs)
                pdf.ln(5)
                
                # Inserción de fotos
                pdf.photo_grid("Evidencia: Antes", fotos_antes)
                pdf.photo_grid("Evidencia: Despues", fotos_despues)
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                # Destinatarios y Envío
                destinatarios = ["german.constantino@besco.mx", "andres.mayagoitia@besco.mx", "gerardo.mendez@besco.mx"]
                item_puro = equipo.split(" - ")[0]
                
                st.info("Enviando correo...")
                if enviar_correo(pdf_bytes, "Nestle", item_puro, f"Reporte_Nestle_{item_puro}.pdf", "", destinatarios):
                    st.success("¡Reporte enviado correctamente!")
                    
                    # Llamada a Gemini
                    st.write("### 🤖 Análisis IA del Reporte")
                    with st.spinner("Gemini está analizando el levantamiento..."):
                        resumen = analizar_reporte_con_gemini(f"Equipo: {equipo}, Área: {area}, Técnico: {tecnico}, Obs: {obs}")
                        st.info(resumen)
            else:
                st.warning("Por favor, ingresa al menos las observaciones técnicas antes de generar el reporte.")
else:
    st.warning("No se encontraron datos en la hoja de Nestlé.")
