import subprocess
import sys
import os

def main():
    # Initialize assets if logo is missing
    logo_path = os.path.join("assets", "logo.png")
    if not os.path.exists(logo_path):
        print("Logo not found. Generating logo...")
        subprocess.run([sys.executable, "create_logo.py"])

    # Run the streamlit application
    print("Starting Generador de Reportes COG...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.join("app", "main.py")])
    except KeyboardInterrupt:
        print("\nApplication stopped.")

if __name__ == "__main__":
    main()
