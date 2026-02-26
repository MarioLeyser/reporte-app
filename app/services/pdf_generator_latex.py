import subprocess
import os
import shutil
from pathlib import Path
from config import OUTPUTS_DIR, ASSETS_DIR

def find_pdflatex():
    """Busca pdflatex en el PATH o en ubicaciones comunes de MiKTeX."""
    
    # 1. Intentar encontrarlo en el PATH
    path = shutil.which("pdflatex")
    if path:
        return path
        
    # 2. Ubicaciones comunes en Windows
    common_paths = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\MiKTeX\miktex\bin\x64\pdflatex.exe"),
        r"C:\Program Files\MiKTeX\miktex\bin\x64\pdflatex.exe",
    ]
    
    for p in common_paths:
        if os.path.exists(p):
            return p
            
    return "pdflatex" # Fallback al nombre, que fallará si no está en PATH

def generate_pdf_latex(tex_content: str, output_filename_base: str) -> str:
    """
    Genera un PDF compilando el contenido LaTeX usando pdflatex.
    output_filename_base: nombre sin extensión
    """
    temp_dir = OUTPUTS_DIR / "temp_latex"
    temp_dir.mkdir(exist_ok=True)
    
    # Copiar logo
    logo_src = ASSETS_DIR / "logo.png"
    if logo_src.exists():
        shutil.copy2(logo_src, temp_dir / "logo.png")
    
    tex_file = temp_dir / f"{output_filename_base}.tex"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(tex_content)
    
    pdflatex_cmd = find_pdflatex()
    
    # Ejecutar pdflatex
    try:
        result = subprocess.run(
            [pdflatex_cmd, "-interaction=nonstopmode", f"{output_filename_base}.tex"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print("Compilación exitosa")
    except subprocess.CalledProcessError as e:
        print(f"Error en pdflatex: {e.output}")
        # A veces pdflatex falla pero genera el PDF si los errores no son críticos
        # En producción deberíamos ser más estrictos
    
    pdf_source = temp_dir / f"{output_filename_base}.pdf"
    pdf_target = OUTPUTS_DIR / f"{output_filename_base}.pdf"
    
    if pdf_source.exists():
        if pdf_target.exists():
            os.remove(pdf_target)
        os.rename(pdf_source, pdf_target)
        
        # Limpiar archivos auxiliares
        for ext in [".aux", ".log", ".tex", ".out"]:
            aux_file = temp_dir / f"{output_filename_base}{ext}"
            if aux_file.exists():
                os.remove(aux_file)
        
        return str(pdf_target)
    else:
        raise Exception("No se pudo generar el PDF. Verifica la instalación de LaTeX.")
