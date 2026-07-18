import os
import json
import time
import uuid
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import quote

import requests
import streamlit as st


# =========================================================
# RESULTADO ESTANDAR
# =========================================================
@dataclass
class RegistroPDFResult:
    ok: bool
    message: str
    pdf_url: Optional[str] = None
    drive_item_id: Optional[str] = None
    list_item_id: Optional[str] = None
    error: Optional[str] = None


# =========================================================
# CONFIGURACION GENERAL
# =========================================================
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
LOGIN_BASE_URL = "https://login.microsoftonline.com"

MAX_SMALL_UPLOAD_BYTES = 245 * 1024 * 1024
DEFAULT_TIMEOUT = 45
MAX_RETRIES = 3


# =========================================================
# MAPEO DE CAMPOS
# Ajusta estos nombres si tus columnas internas de SharePoint
# son distintas.
# =========================================================
FIELD_MAP = {
    "Title": "Title",
    "Modulo": "Modulo",
    "Contrato": "Contrato",
    "Cliente": "Cliente",
    "Folio": "Folio",
    "Oficina": "Oficina",
    "Sucursal": "Sucursal",
    "Tecnico": "Tecnico",
    "Supervisor": "Supervisor",
    "TipoServicio": "TipoServicio",
    "EstatusFinal": "EstatusFinal",
    "FechaEjecucion": "FechaEjecucion",
    "FechaGeneracion": "FechaGeneracion",
    "NombrePDF": "NombrePDF",
    "PDFUrl": "PDFUrl",
    "PDFDriveItemId": "PDFDriveItemId",
    "PDFSizeKB": "PDFSizeKB",
    "UsuarioApp": "UsuarioApp",
    "CorreosDestinatarios": "CorreosDestinatarios",
    "ResultadoCorreo": "ResultadoCorreo",
    "Observaciones": "Observaciones",
    "ExtraJson": "ExtraJson",
}


# =========================================================
# SECRETS
# =========================================================
def get_secret(name: str, default: Optional[str] = None) -> Optionaltry:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    if value is None:
        return default

    value = str(value).strip()

    if value == "":
        return default

    return value


def registro_activo() -> bool:
    value = get_secret("REGISTRO_PDF_ACTIVO", "true")
    return str(value).strip().lower() in ["true", "1", "yes", "si", "sí"]


def strict_mode() -> bool:
    value = get_secret("REGISTRO_PDF_STRICT_MODE", "false")
    return str(value).strip().lower() in ["true", "1", "yes", "si", "sí"]


# =========================================================
# NORMALIZACION
# =========================================================
def normalizar_texto(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)

    replacements = {
        "\r": " ",
        "\n": " ",
        "\t": " ",
        "•": "-",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u200b": "",
    }

    for original, new in replacements.items():
        text = text.replace(original, new)

    return " ".join(text.split())


def safe_filename(name: str) -> str:
    name = normalizar_texto(name)

    invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|", "&", "#", "%"]

    for char in invalid_chars:
        name = name.replace(char, "_")

    name = name.replace(" ", "_")

    if not name.lower().endswith(".pdf"):
        name += ".pdf"

    return name


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fecha_carpeta() -> str:
    return datetime.now().strftime("%Y/%m/%d")


def encode_graph_path(path: str) -> str:
    parts = [p for p in str(path).replace("\\", "/").split("/") if p]
    encoded = [quote(part, safe="") for part in parts]
    return "/".join(encoded)


def build_pdf_relative_path(modulo: str, nombre_pdf: str) -> str:
    base_folder = get_secret("SHAREPOINT_PDF_FOLDER", "PortalSolucionesPDF")
    modulo_folder = safe_filename(modulo).replace(".pdf", "")

    relative_path = f"{base_folder}/{modulo_folder}/{fecha_carpeta()}/{nombre_pdf}"

    return relative_path


# =========================================================
# TOKEN GRAPH
# =========================================================
def get_graph_token() -> str:
    tenant_id = get_secret("GRAPH_TENANT_ID")
    client_id = get_secret("GRAPH_CLIENT_ID")
    client_secret = get_secret("GRAPH_CLIENT_SECRET")

    if not tenant_id or not client_id or not client_secret:
        raise RuntimeError(
            "Faltan secrets de Microsoft Graph: GRAPH_TENANT_ID, GRAPH_CLIENT_ID o GRAPH_CLIENT_SECRET."
        )

    url = f"{LOGIN_BASE_URL}/{tenant_id}/oauth2/v2.0/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }

    response = requests.post(
        url,
        data=data,
        timeout=DEFAULT_TIMEOUT,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"No se pudo obtener token Graph. HTTP {response.status_code}: {response.text}"
        )

    payload = response.json()
    token = payload.get("access_token")

    if not token:
        raise RuntimeError("Microsoft Graph no devolvio access_token.")

    return token


# =========================================================
# REQUEST GRAPH CON REINTENTOS
# =========================================================
def graph_request(
    method: str,
    url: str,
    token: str,
    headers: Optional[Dict[str, str]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[bytes] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> requests.Response:
    final_headers = {
        "Authorization": f"Bearer {token}",
    }

    if headers:
        final_headers.update(headers)

    last_response = None

    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.request(
            method=method,
            url=url,
            headers=final_headers,
            json=json_body,
            data=data,
            timeout=timeout,
        )

        last_response = response

        if response.status_code < 400:
            return response

        if response.status_code in [429, 500, 502, 503, 504]:
            sleep_seconds = min(2 * attempt, 10)
            time.sleep(sleep_seconds)
            continue

        return response

    return last_response


# =========================================================
# SITE / DRIVE / LIST
# =========================================================
def get_site_id(token: str) -> str:
    explicit_site_id = get_secret("SHAREPOINT_SITE_ID")

    if explicit_site_id:
        return explicit_site_id

    hostname = get_secret("SHAREPOINT_HOSTNAME")
    site_path = get_secret("SHAREPOINT_SITE_PATH")

    if not hostname or not site_path:
        raise RuntimeError(
            "Faltan SHAREPOINT_HOSTNAME y SHAREPOINT_SITE_PATH, o define SHAREPOINT_SITE_ID."
        )

    if not site_path.startswith("/"):
        site_path = "/" + site_path

    url = f"{GRAPH_BASE_URL}/sites/{hostname}:{site_path}"

    response = graph_request(
        method="GET",
        url=url,
        token=token,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"No se pudo obtener siteId. HTTP {response.status_code}: {response.text}"
        )

    site_id = response.json().get("id")

    if not site_id:
        raise RuntimeError("No se encontro id del sitio SharePoint.")

    return site_id


def get_drive_id(token: str, site_id: str) -> str:
    explicit_drive_id = get_secret("SHAREPOINT_DRIVE_ID")

    if explicit_drive_id:
        return explicit_drive_id

    library_name = get_secret("SHAREPOINT_DOCUMENT_LIBRARY", "Documentos")

    drives_url = f"{GRAPH_BASE_URL}/sites/{site_id}/drives"

    response = graph_request(
        method="GET",
        url=drives_url,
        token=token,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"No se pudieron listar bibliotecas. HTTP {response.status_code}: {response.text}"
        )

    drives = response.json().get("value", [])

    for drive in drives:
        if str(drive.get("name", "")).strip().lower() == library_name.strip().lower():
            drive_id = drive.get("id")

            if drive_id:
                return drive_id

    default_drive_url = f"{GRAPH_BASE_URL}/sites/{site_id}/drive"

    response_default = graph_request(
        method="GET",
        url=default_drive_url,
        token=token,
    )

    if response_default.status_code >= 400:
        raise RuntimeError(
            f"No se encontro biblioteca '{library_name}' ni drive default. HTTP {response_default.status_code}: {response_default.text}"
        )

    drive_id = response_default.json().get("id")

    if not drive_id:
        raise RuntimeError("No se pudo obtener driveId.")

    return drive_id


def get_list_id(token: str, site_id: str) -> str:
    explicit_list_id = get_secret("SHAREPOINT_LIST_ID")

    if explicit_list_id:
        return explicit_list_id

    list_name = get_secret("SHAREPOINT_REGISTRY_LIST", "RegistroPDFPortal")

    lists_url = f"{GRAPH_BASE_URL}/sites/{site_id}/lists"

    response = graph_request(
        method="GET",
        url=lists_url,
        token=token,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"No se pudieron listar listas SharePoint. HTTP {response.status_code}: {response.text}"
        )

    lists = response.json().get("value", [])

    for sp_list in lists:
        display_name = str(sp_list.get("displayName", "")).strip()
        name = str(sp_list.get("name", "")).strip()

        if display_name.lower() == list_name.lower() or name.lower() == list_name.lower():
            list_id = sp_list.get("id")

            if list_id:
                return list_id

    raise RuntimeError(f"No se encontro la lista SharePoint: {list_name}")


# =========================================================
# UPLOAD PDF
# =========================================================
def upload_pdf_to_sharepoint(
    token: str,
    drive_id: str,
    pdf_bytes: bytes,
    relative_path: str,
) -> Dict[str, Any]:
    if len(pdf_bytes) > MAX_SMALL_UPLOAD_BYTES:
        raise RuntimeError(
            "El PDF supera el limite para carga simple. Se requiere upload session."
        )

    encoded_path = encode_graph_path(relative_path)

    upload_url = f"{GRAPH_BASE_URL}/drives/{drive_id}/root:/{encoded_path}:/content"

    response = graph_request(
        method="PUT",
        url=upload_url,
        token=token,
        headers={
            "Content-Type": "application/pdf",
        },
        data=pdf_bytes,
        timeout=120,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"No se pudo subir PDF a SharePoint. HTTP {response.status_code}: {response.text}"
        )

    return response.json()


# =========================================================
# CREAR REGISTRO LISTA SHAREPOINT
# =========================================================
def limpiar_valor_sharepoint(value: Any) -> Any:
    if value is None:
        return ""

    if isinstance(value, (int, float, bool)):
        return value

    return normalizar_texto(value)


def build_fields_payload(
    modulo: str,
    nombre_pdf: str,
    pdf_url: str,
    drive_item_id: str,
    size_kb: float,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    title = metadata.get("Title") or f"{modulo} - {nombre_pdf}"

    base_fields = {
        "Title": title,
        "Modulo": modulo,
        "Contrato": metadata.get("Contrato", ""),
        "Cliente": metadata.get("Cliente", ""),
        "Folio": metadata.get("Folio", ""),
        "Oficina": metadata.get("Oficina", ""),
        "Sucursal": metadata.get("Sucursal", ""),
        "Tecnico": metadata.get("Tecnico", ""),
        "Supervisor": metadata.get("Supervisor", ""),
        "TipoServicio": metadata.get("TipoServicio", ""),
        "EstatusFinal": metadata.get("EstatusFinal", ""),
        "FechaEjecucion": metadata.get("FechaEjecucion", ""),
        "FechaGeneracion": now_iso(),
        "NombrePDF": nombre_pdf,
        "PDFUrl": pdf_url,
        "PDFDriveItemId": drive_item_id,
        "PDFSizeKB": round(size_kb, 2),
        "UsuarioApp": metadata.get("UsuarioApp", ""),
        "CorreosDestinatarios": metadata.get("CorreosDestinatarios", ""),
        "ResultadoCorreo": metadata.get("ResultadoCorreo", ""),
        "Observaciones": metadata.get("Observaciones", ""),
        "ExtraJson": json.dumps(metadata, ensure_ascii=False, default=str),
    }

    sharepoint_fields = {}

    for logical_name, internal_name in FIELD_MAP.items():
        value = base_fields.get(logical_name, "")
        sharepoint_fields[internal_name] = limpiar_valor_sharepoint(value)

    return sharepoint_fields


def create_sharepoint_list_item(
    token: str,
    site_id: str,
    list_id: str,
    fields_payload: Dict[str, Any],
) -> Dict[str, Any]:
    create_url = f"{GRAPH_BASE_URL}/sites/{site_id}/lists/{list_id}/items"

    response = graph_request(
        method="POST",
        url=create_url,
        token=token,
        headers={
            "Content-Type": "application/json",
        },
        json_body={
            "fields": fields_payload,
        },
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"No se pudo crear registro en lista SharePoint. HTTP {response.status_code}: {response.text}"
        )

    return response.json()


# =========================================================
# FUNCION PRINCIPAL
# =========================================================
def registrar_pdf_sharepoint(
    modulo: str,
    nombre_pdf: str,
    metadata: Optional[Dict[str, Any]] = None,
    pdf_path: Optional[str] = None,
    pdf_bytes: Optional[bytes] = None,
) -> RegistroPDFResult:
    if not registro_activo():
        return RegistroPDFResult(
            ok=False,
            message="Registro SharePoint desactivado por REGISTRO_PDF_ACTIVO=false.",
        )

    try:
        metadata = metadata or {}

        nombre_pdf_seguro = safe_filename(nombre_pdf)

        if pdf_bytes is None:
            if not pdf_path:
                raise RuntimeError("Debes enviar pdf_path o pdf_bytes.")

            with open(pdf_path, "rb") as file:
                pdf_bytes = file.read()

        size_kb = len(pdf_bytes) / 1024

        token = get_graph_token()
        site_id = get_site_id(token)
        drive_id = get_drive_id(token, site_id)
        list_id = get_list_id(token, site_id)

        relative_path = build_pdf_relative_path(
            modulo=modulo,
            nombre_pdf=nombre_pdf_seguro,
        )

        drive_item = upload_pdf_to_sharepoint(
            token=token,
            drive_id=drive_id,
            pdf_bytes=pdf_bytes,
            relative_path=relative_path,
        )

        pdf_url = drive_item.get("webUrl", "")
        drive_item_id = drive_item.get("id", "")

        fields_payload = build_fields_payload(
            modulo=modulo,
            nombre_pdf=nombre_pdf_seguro,
            pdf_url=pdf_url,
            drive_item_id=drive_item_id,
            size_kb=size_kb,
            metadata=metadata,
        )

        list_item = create_sharepoint_list_item(
            token=token,
            site_id=site_id,
            list_id=list_id,
            fields_payload=fields_payload,
        )

        list_item_id = list_item.get("id")

        return RegistroPDFResult(
            ok=True,
            message="PDF subido y registro creado en SharePoint.",
            pdf_url=pdf_url,
            drive_item_id=drive_item_id,
            list_item_id=list_item_id,
        )

    except Exception as error:
        error_text = str(error)

        if strict_mode():
            raise

        return RegistroPDFResult(
            ok=False,
            message="El PDF se genero, pero no se pudo registrar en SharePoint.",
            error=error_text,
        )


# =========================================================
# HELPER PARA STREAMLIT
# =========================================================
def mostrar_resultado_registro(resultado: RegistroPDFResult) -> None:
    if resultado.ok:
        st.success(resultado.message)

        if resultado.pdf_url:
            st.markdown(f"{resultado.pdf_url}")
    else:
        st.warning(resultado.message)

        if resultado.error:
            with st.expander("Detalle del error SharePoint", expanded=False):
                st.code(resultado.error)
