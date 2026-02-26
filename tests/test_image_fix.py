from PIL import Image
import io
import sys
import os

# Append project root to path
sys.path.append(os.getcwd())

from app.services.image_processor import resize_image

def test_various_modes_to_jpeg():
    modes_to_test = [
        ('RGBA', (255, 0, 0, 128)),
        ('P', 1), # Palettized
        ('LA', (128, 128)), # Grayscale + Alpha
        ('CMYK', (0, 255, 255, 0)),
        # ('HSV', (120, 255, 255)) # PIL often fails to save HSV directly to common formats
    ]
    
    print("Testing various image modes conversion to JPEG...")
    
    for mode, color in modes_to_test:
        print(f"Testing mode: {mode}")
        try:
            img = Image.new(mode, (100, 100), color=color)
            img_bytes = io.BytesIO()
            
            # Save in a format that supports the mode (PNG usually supports most, or TIFF)
            # For this test, we just need the bytes. Some modes might need specific formats to save.
            # simpler approach: just mock the bytes reading part or save as specific format.
            # Let's use PNG for alpha modes, TIFF for others if needed, or just force it.
            
            if mode in ['CMYK', 'HSV']:
                 img.save(img_bytes, format='TIFF')
            else:
                 img.save(img_bytes, format='PNG')
                 
            input_bytes = img_bytes.getvalue()
            
            result = resize_image(input_bytes)
            
            # Verify result
            result_img = Image.open(io.BytesIO(result))
            print(f"  -> Result mode: {result_img.mode}")
            
            # Allow L for grayscale, otherwise RGB
            if result_img.mode not in ("RGB", "L"):
                 print(f"  FAILED: Expected RGB or L, got {result_img.mode}")
                 sys.exit(1)
                 
        except Exception as e:
            print(f"  FAILED with error: {e}")
            sys.exit(1)

    print("Success! All modes processed correctly.")

if __name__ == "__main__":
    test_various_modes_to_jpeg()
