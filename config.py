import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Rutas de carpetas
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
CSS_DIR = ASSETS_DIR / "css"
IMAGES_DIR = ASSETS_DIR / "images"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Crear carpeta de salida si no existe
OUTPUTS_DIR.mkdir(exist_ok=True)

# Configuración de PDF
PDF_TITLE = "Reporte de Actividades y Eventos"
PDF_AUTHOR = "ICRT"
PDF_SUBJECT = "Reporte técnico"
PDF_KEYWORDS = "gas, mantenimiento, reporte"

# Versión del formato
FORMAT_VERSION = "2"
FORMAT_CODE = "ICRT 001 TI CO FO 0011"

# Información de revisión
REVIEWED_BY = "MIGUEL AUCAPOMA"
REVIEW_DATE = "06/10/2023"
APPROVED_BY = "JUAN LLANOS"
APPROVE_DATE = "10/10/2023"

# Configuración de Nube (Nextcloud)
CLOUD_URL = "https://webserver.taild7f3a5.ts.net"
CLOUD_USER = "bot"
CLOUD_PASS = "@marioleiser64"
CLOUD_BASE_PATH = "/LasBambas"
# Subcarpetas dentro del proyecto
CLOUD_PHOTOS_PATH = f"{CLOUD_BASE_PATH}/Fotos"
CLOUD_REPORTS_PATH = f"{CLOUD_BASE_PATH}/Reportes"
CLOUD_DRAFTS_PATH = f"{CLOUD_BASE_PATH}/Borradores"
