from PIL import Image, ImageDraw, ImageFont
import os

def create_logo():
    # Create an image with white background
    width = 400
    height = 100
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, otherwise use default
    try:
        font = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw Text
    # ICRT (Black) SAC (Red)
    draw.text((10, 10), "ICRT", fill="black", font=font)
    draw.text((120, 10), "SAC", fill="red", font=font)
    
    # Subtitle
    draw.text((10, 60), "Soluciones Tecnológicas Industriales", fill="black", font=font_small)
    
    # Ensure assets dir exists
    if not os.path.exists("assets"):
        os.makedirs("assets")
        
    image.save("assets/logo.png")
    print("Logo created at assets/logo.png")

if __name__ == "__main__":
    create_logo()
