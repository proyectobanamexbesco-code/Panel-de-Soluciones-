import streamlit as st
import os
from datetime import datetime
from fpdf import FPDF
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==============================================================================
# CLASE PERSONALIZADA PARA GENERACIÓN DEL PDF (ESTILO CORPORATIVO BESCO)
# ==============================================================================
class PDFReporteBesco(FPDF):
    def header(self):
        # Encabezado corporativo elegante
        self.set_fill_color(22, 54, 87)  # Azul Oscuro Institucional
        self.rect(0, 0, 216, 30, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'SISTEMA DE EVIDENCIA TÉCNICA BESCO', ln=True, align='C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, f'Emisión Automatizada: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='C')
        self.ln(10)

    def footer(self):
        # Pie de página con numeración
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()} de {{nb}} | Grupo Besco S.A. de C.V.', align='C')

    def agregar_seccion_titulo(self, titulo):
        self.set_fill_color(240, 240, 240)
        self.set_text_color(22, 54, 87)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f"  {titulo.upper()}", ln=True, fill=True)
        self.ln(3)

# ==============================================================================
# FUNCIÓN COMPLETA DE SUBIDA A INFRAESTRUCTURA GOOGLE DRIVE
# ==============================================================================
def subir_pdf_a_google_drive(ruta_pdf_local, nombre_archivo_drive):
    try:
        # 1. Autenticación robusta usando la sección unificada [google_drive]
        info_credenciales = st.secrets["google_drive"]
        credenciales = service_account.Credentials.from_service_account_info(info_credenciales)
        
        # 2. Construcción del cliente API de Google Drive
        servicio = build('drive', 'v3', credentials=credenciales)
        id_carpeta_destino = info_credenciales["folder_id"]
        
        metadatos_archivo = {
            'name': nombre_archivo_drive,
            'parents': [id_carpeta_destino]
        }
        
        media = MediaFileUpload(ruta_pdf_local, mimetype='application/pdf', resumable=True)
        
        # 3. Transmisión del archivo
        archivo_subido = servicio.files().create(
            body=metadatos_archivo,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = archivo_subido.get("id")
        
        # 4. REFUERZO DE PERMISOS: Forzar visibilidad inmediata en la interfaz web de Drive
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
            return file_id
            
    except Exception as e:
        st.error(f"❌ Error crítico en el canal de sincronización con Google Drive: {e}")
        return None

# ==============================================================================
# APLICACIÓN PRINCIPAL - INTERFAZ DE STREAMLIT
# ==============================================================================
def main():
    st.set_page_config(page_title="Reporte General - BESCO", layout="wide")
    
    st.title("📋 Generador del Reporte General Técnico")
    st.write("Sincronizado directamente con la Base Maestra Corporativa.")
    
    # --- FORMULARIO ESTRUCTURADO ---
    with st.form("formulario_maestro_reporte"):
        st.subheader("1. Datos de Identificación General")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Cliente / Empresa", placeholder="Ej. GAP Toluca")
            folio = st.text_input("Folio del Reporte", placeholder="Ej. MP-AA-4821")
            sucursal = st.text_input("Sucursal / Sitio", placeholder="Ej. LERMA")
        with col2:
            fecha_ejecucion = st.date_input("Fecha de Ejecución", datetime.now())
            tecnico = st.text_input("Técnico(s) Asignado(s)", placeholder="Nombre del personal técnico")
            supervisor = st.text_input("Supervisor a Cargo", placeholder="Nombre del supervisor")
            
        servicio_tipo = st.selectbox("Tipo de Servicio", ["Preventivo (Sin Ticket)", "Preventivo (Con Ticket)", "Correctivo", "Urgencia"])
        
        st.write("---")
        st.subheader("2. Registro de Hallazgos y Equipos")
        
        num_equipos = st.number_input("Número de sistemas o áreas a reportar", min_value=1, max_value=6, value=1)
        
        datos_equipos = []
        for i in range(int(num_equipos)):
            st.markdown(f"#### **Sistema / Área #{i+1}**")
            c1, c2, c3 = st.columns([2, 2, 3])
            with c1:
                nombre_eq = st.text_input(f"Nombre / Categoría (Eq. {i+1})", key=f"eq_nom_{i}")
                tag_eq = st.text_input(f"TAG / Identificador (Eq. {i+1})", key=f"eq_tag_{i}")
            with c2:
                estatus_eq = st.selectbox(f"Estatus Final (Eq. {i+1})", ["Operando correctamente", "Requiere Presupuesto", "Fuera de Servicio"], key=f"eq_est_{i}")
            with c3:
                actividades = st.text_area(f"Actividades Realizadas (Eq. {i+1})", key=f"eq_act_{i}", placeholder="Describa el trabajo técnico detallado...")
            
            col_img1, col_img2 = st.columns(2)
            with col_img1:
                img_antes = st.file_uploader(f"Evidencia ANTES (Eq. {i+1})", type=["jpg", "png", "jpeg"], key=f"img_ant_{i}", accept_multiple_files=True)
            with col_img2:
                img_despues = st.file_uploader(f"Evidencia DESPUÉS (Eq. {i+1})", type=["jpg", "png", "jpeg"], key=f"img_des_{i}", accept_multiple_files=True)
                
            datos_equipos.append({
                "nombre": nombre_eq, "tag": tag_eq, "estatus": estatus_eq, "actividades": actividades,
                "imagenes_antes": img_antes, "imagenes_despues": img_despues
            })
            st.markdown("---")
            
        boton_guardar = st.form_submit_button("🚀 Compilar Reporte y Subir Historial")

    if boton_guardar:
        if not cliente or not folio or not tecnico:
            st.error("❌ Los campos 'Cliente', 'Folio' y 'Técnico(s)' son obligatorios para validar el registro corporativo.")
            return

        with st.spinner("Construyendo documento e indexando evidencias binarias..."):
            # Nombres estandarizados de archivos locales
            nombre_limpio_cliente = cliente.replace(" ", "_").upper()
            nombre_pdf_final = f"Reporte_BESCO_{nombre_limpio_cliente}_{folio.replace(' ', '_')}.pdf"
            ruta_local = os.path.join("/tmp", nombre_pdf_final) if os.name != 'nt' else nombre_pdf_final
            
            try:
                # --- PROCESAMIENTO DINÁMICO FPDF ---
                pdf = PDFReporteBesco(orientation='P', unit='mm', format='Letter')
                pdf.alias_nb_pages()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=20)
                
                # Bloque 1: Información General
                pdf.agregar_seccion_titulo("1. Información General del Servicio")
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                
                # Estructura de Tabla Base para Datos Generales
                pdf.cell(40, 7, 'Cliente:', 1, 0, 'L')
                pdf.cell(55, 7, str(cliente), 1, 0, 'L')
                pdf.cell(40, 7, 'Folio Interno:', 1, 0, 'L')
                pdf.cell(55, 7, str(folio), 1, 1, 'L')
                
                pdf.cell(40, 7, 'Fecha Ejecución:', 1, 0, 'L')
                pdf.cell(55, 7, str(fecha_ejecucion), 1, 0, 'L')
                pdf.cell(40, 7, 'Sucursal:', 1, 0, 'L')
                pdf.cell(55, 7, str(sucursal), 1, 1, 'L')
                
                pdf.cell(40, 7, 'Técnico:', 1, 0, 'L')
                pdf.cell(55, 7, str(tecnico), 1, 0, 'L')
                pdf.cell(40, 7, 'Supervisor:', 1, 0, 'L')
                pdf.cell(55, 7, str(supervisor), 1, 1, 'L')
                
                pdf.cell(40, 7, 'Tipo de Servicio:', 1, 0, 'L')
                pdf.cell(150, 7, str(servicio_tipo), 1, 1, 'L')
                pdf.ln(6)
                
                # Bloque 2: Recorrido de los Equipos registrados
                idx = 1
                for eq in datos_equipos:
                    pdf.agregar_seccion_titulo(f"Equipo / Área {idx}: {eq['nombre']}")
                    pdf.set_font('Arial', '', 10)
                    
                    pdf.cell(40, 7, 'Identificador / TAG:', 1, 0, 'L')
                    pdf.cell(55, 7, str(eq['tag']), 1, 0, 'L')
                    pdf.cell(40, 7, 'Estatus Final:', 1, 0, 'L')
                    pdf.cell(55, 7, str(eq['estatus']), 1, 1, 'L')
                    
                    pdf.cell(40, 7, 'Actividades:', 1, 0, 'L')
                    pdf.multi_cell(150, 7, str(eq['actividades']), 1, 'L')
                    pdf.ln(4)
                    
                    # Manejo Dinámico de Imágenes Guardadas en Memoria
                    if eq['imagenes_antes']:
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(0, 5, "📸 Evidencias del Antes:", ln=True)
                        pdf.ln(1)
                        for img_f in eq['imagenes_antes']:
                            try:
                                # Guardado temporal en disco del buffer en memoria para FPDF
                                tmp_img_path = f"tmp_ant_{idx}_{img_f.name}"
                                with open(tmp_img_path, "wb") as f_img:
                                    f_img.write(img_f.getbuffer())
                                pdf.image(tmp_img_path, x=pdf.get_x(), w=45, h=35)
                                pdf.ln(2)
                                os.remove(tmp_img_path)
                            except Exception:
                                pass
                                
                    if eq['imagenes_despues']:
                        pdf.set_font('Arial', 'B', 9)
                        pdf.cell(0, 5, "📸 Evidencias del Después:", ln=True)
                        pdf.ln(1)
                        for img_f in eq['imagenes_despues']:
                            try:
                                tmp_img_path = f"tmp_des_{idx}_{img_f.name}"
                                with open(tmp_img_path, "wb") as f_img:
                                    f_img.write(img_f.getbuffer())
                                pdf.image(tmp_img_path, x=pdf.get_x(), w=45, h=35)
                                pdf.ln(2)
                                os.remove(tmp_img_path)
                            except Exception:
                                pass
                    
                    pdf.ln(5)
                    idx += 1
                
                # Compilar salida física
                pdf.output(ruta_local)
                
            except Exception as pdf_error:
                st.error(f"❌ Error en el motor de ensamblaje PDF: {pdf_error}")
                return

            # --- SUBIDA AUTOMÁTICA AL CLOUD MAESTRO ---
            if os.path.exists(ruta_local):
                id_documento_drive = subir_pdf_a_google_drive(ruta_local, nombre_pdf_final)
                
                if id_documento_drive:
                    st.balloons()
                    st.success(f"🎉 ¡Proceso Completado con Éxito!")
                    st.info(f"📁 Archivo indexado correctamente en la carpeta compartida BASE_MAESTRA_PDF con el identificador único: {id_documento_drive}")
                    
                    # Limpieza segura final
                    try:
                        os.remove(ruta_local)
                    except OSError:
                        pass
            else:
                st.error("No se pudo validar la existencia del compilado binario local.")

if __name__ == "__main__":
    main()
