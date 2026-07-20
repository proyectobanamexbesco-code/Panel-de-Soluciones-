import streamlit as st
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
# Nota: Asegúrate de importar tus librerías de generación de PDF aquí (ej. FPDF o PyPDF)
# desde tu archivo de reportes existente.

def subir_pdf_a_google_drive(ruta_pdf_local, nombre_archivo_drive):
    """
    Sube el archivo PDF generado a la carpeta BASE_MAESTRA_PDF de Google Drive
    utilizando las credenciales unificadas de la cuenta de servicio corporativa.
    """
    try:
        # 1. Cargar las credenciales estructuradas desde [google_drive] en Secrets
        info_credenciales = st.secrets["google_drive"]
        credenciales = service_account.Credentials.from_service_account_info(info_credenciales)
        
        # 2. Inicializar el servicio de la API de Google Drive
        servicio = build('drive', 'v3', credentials=credenciales)
        
        # 3. Obtener el ID de la carpeta de destino configurada
        id_carpeta_destino = info_credenciales["folder_id"]
        
        # Metadatos del archivo en Drive vinculando la carpeta raíz
        metadatos_archivo = {
            'name': nombre_archivo_drive,
            'parents': [id_carpeta_destino]
        }
        
        # Preparar el archivo binario para la subida
        media = MediaFileUpload(ruta_pdf_local, mimetype='application/pdf', resumable=True)
        
        # 4. Ejecutar la subida del archivo
        archivo_subido = servicio.files().create(
            body=metadatos_archivo,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = archivo_subido.get("id")
        
        # 5. REFUERZO DE PERMISOS: Conceder permisos explícitos para evitar archivos fantasmas u ocultos
        if file_id:
            permiso_herencia = {
                'type': 'anyone',
                'role': 'reader'
            }
            servicio.permissions().create(
                fileId=file_id,
                body=permiso_herencia,
                fields='id'
            ).execute()
            
            st.success(f"✅ ¡Reporte respaldado en Google Drive con éxito! (ID: {file_id})")
            return file_id
            
    except Exception as e:
        st.error(f"❌ Error crítico al sincronizar con Google Drive: {e}")
        return None

# ==============================================================================
# ESTRUCTURA E INTERFAZ DEL REPORTE GENERAL (Streamlit)
# ==============================================================================
def main():
    st.title("📊 Generación de Reporte General")
    st.write("Complete el formulario para compilar las evidencias técnicas y generar el archivo PDF.")

    # --- CAMPOS DE ENTRADA DEL FORMULARIO ---
    with st.form("formulario_reporte_general"):
        # Puedes expandir estos campos con la estructura específica que ya manejas
        nombre_tecnico = st.text_input("Nombre del Técnico Responsable")
        detalles_trabajo = st.text_area("Descripción de las Actividades / Evidencias")
        
        # Simulación de carga de imágenes de evidencia si aplica en tu script original
        archivos_imagenes = st.file_uploader("Cargar imágenes de evidencia", accept_multiple_files=True, type=["png", "jpg", "jpeg"])
        
        # Botón de envío del formulario
        boton_procesar = st.form_submit_with_clicks = st.form_submit_button("Generar y Enviar Reporte")

    if boton_procesar:
        if not nombre_tecnico or not detalles_trabajo:
            st.warning("⚠️ Por favor complete los campos obligatorios antes de continuar.")
            return

        with st.spinner("Procesando datos y construyendo el documento PDF..."):
            # 1. Definir nombres y rutas temporales para el archivo local
            nombre_pdf_final = f"Reporte_{nombre_tecnico.replace(' ', '_')}.pdf"
            ruta_temporal_local = os.path.join("/tmp", nombre_pdf_final) if os.name != 'nt' else nombre_pdf_final
            
            # ----------------==================================================
            # ESPACIO PARA TU LÓGICA DE GENERACIÓN DE PDF EXISTENTE
            # ----------------==================================================
            # Aquí va el código que ya tenías para instanciar FPDF/PyPDF, estructurar
            # las hojas, acomodar las imágenes fijas y escribir las descripciones.
            # Como ejemplo base, creamos un archivo dummy si no existe:
            try:
                with open(ruta_temporal_local, "w", encoding="utf-8") as f:
                    f.write(f"Reporte Técnico General\nResponsable: {nombre_tecnico}\nDetalles: {detalles_trabajo}")
            except Exception as pdf_err:
                st.error(f"Error al estructurar el PDF local: {pdf_err}")
                return
            # ----------------==================================================

            # 2. Subida automatizada a la infraestructura de Google Drive
            if os.path.exists(ruta_temporal_local):
                id_drive_resultado = subir_pdf_a_google_drive(ruta_temporal_local, nombre_pdf_final)
                
                # 3. Limpieza del entorno local tras el envío exitoso
                if id_drive_resultado:
                    try:
                        os.remove(ruta_temporal_local)
                    except OSError:
                        pass
            else:
                st.error("No se encontró el archivo temporal local generado.")

if __name__ == "__main__":
    main()
