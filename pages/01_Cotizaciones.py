import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource(ttl=600)
def init_gspread_client():
    """Autentica y regresa el cliente de gspread usando la cuenta de servicio."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_dict = dict(st.secrets["google_credentials"])
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return None

def obtener_worksheet_reportes():
    """Conecta a la hoja de cálculo y abre/crea la pestaña 'Historial_Reportes'."""
    gc = init_gspread_client()
    if not gc: return None
    
    # Asegúrate de agregar HISTORIAL_REPORTES_KEY en tus st.secrets
    spreadsheet_id = st.secrets.get("HISTORIAL_REPORTES_KEY", "")
    if not spreadsheet_id:
        st.error("Falta configurar 'HISTORIAL_REPORTES_KEY' en secrets.")
        return None
        
    sh = gc.open_by_key(spreadsheet_id)
    worksheet_name = "Historial_Reportes"
    
    try:
        ws = sh.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        # Crea la pestaña con encabezados si no existe
        ws = sh.add_worksheet(title=worksheet_name, rows="100", cols="10")
        ws.append_row(["FOLIO_INTERNO", "FOLIO_CLIENTE", "FECHA", "CLIENTE", "SUCURSAL", "TECNICO", "TIPO_SERVICIO", "ESTATUS"])
    return ws

def generar_siguiente_folio(ws):
    """Lee la columna A para calcular el siguiente número consecutivo."""
    try:
        folios = ws.col_values(1) # Obtiene todos los valores de la columna A
        if len(folios) <= 1:
            return "REP-0001" # Si solo están los encabezados
            
        ultimo_folio = folios[-1]
        # Separa el prefijo del número (ej. REP-0045 -> 45)
        numero = int(ultimo_folio.split("-")[1])
        nuevo_numero = numero + 1
        return f"REP-{nuevo_numero:04d}"
    except Exception as e:
        return f"REP-{(len(folios) if 'folios' in locals() else 1):04d}"
