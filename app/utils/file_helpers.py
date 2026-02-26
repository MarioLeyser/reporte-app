import os
import tempfile
from pathlib import Path
from datetime import datetime

def create_temp_file(extension=".jpg"):
    """Crea un archivo temporal con extensión dada"""
    fd, path = tempfile.mkstemp(suffix=extension)
    os.close(fd)
    return path

def generate_output_filename(codigo: str) -> str:
    """Genera nombre único para el PDF"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_code = "".join(c for c in codigo if c.isalnum() or c in "._-")
    return f"Reporte_{safe_code}_{timestamp}.pdf"
