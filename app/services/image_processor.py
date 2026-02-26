from PIL import Image
import io
import base64
from pathlib import Path
from app.utils.file_helpers import create_temp_file

def resize_image(image_bytes, max_width=600, max_height=450):
    """Redimensiona la imagen manteniendo proporción y devuelve bytes"""
    img = Image.open(io.BytesIO(image_bytes))
    # Convertir a RGB cualquier formato que no sea compatible con JPEG directamente
    # JPEG soporta L (escala de grises), RGB y CMYK (aunque CMYK puede dar problemas de color en algunos visores, mejor RGB)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
        
    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85)
    return output.getvalue()

def image_to_base64(image_bytes):
    """Convierte bytes de imagen a string base64 para incrustar en HTML"""
    return base64.b64encode(image_bytes).decode('utf-8')

def save_temp_image(image_bytes):
    """Guarda imagen en archivo temporal y devuelve la ruta"""
    temp_path = create_temp_file(".jpg")
    with open(temp_path, "wb") as f:
        f.write(image_bytes)
    return temp_path
