import os
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
