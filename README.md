# Generador Automático de Reportes PDF (estilo COG)

Aplicación para generar reportes de actividades con estructura profesional, incluyendo tablas de datos, evidencia fotográfica y equipos de medición.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación

1. Clonar o descargar este repositorio.
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. **IMPORTANTE (Windows):** Para que WeasyPrint funcione, es necesario instalar las librerías GTK+.
   - Descarga el instalador de GTK3 para Windows desde: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Instálalo y asegúrate de reiniciar tu terminal o IDE después de la instalación.
   - Si persiste el error, intenta agregar la ruta `C:\Program Files\GTK3-Runtime Win64\bin` a tu variable de entorno PATH.

## Uso

Ejecutar la aplicación:

```bash
python run.py
```

Se abrirá una ventana del navegador con la interfaz de Streamlit. Complete todos los campos, suba las imágenes y haga clic en "Generar Reporte PDF". El archivo se guardará en la carpeta `outputs/` y se ofrecerá para descarga.

## Estructura del proyecto

- `app/`: Código fuente (modelos, controladores, servicios).
- `assets/`: Archivos estáticos (CSS, imágenes).
- `templates/`: Plantillas HTML para el PDF.
- `outputs/`: PDF generados.
- `config.py`: Configuración global.
- `run.py`: Script de lanzamiento.

## Personalización

- Modifique `assets/css/report_style.css` para cambiar la apariencia del PDF.
- Edite `config.py` para ajustar los valores por defecto (revisores, código de formato, etc.).
- Las plantillas HTML están en `templates/`; puede adaptarlas a nuevas necesidades.

## Licencia

Uso interno.
