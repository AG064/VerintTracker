import os
import sys
from PIL import Image

def process_logo(input_path, output_dir):
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Please save your logo image there first.")
        return

    print(f"Processing {input_path}...")
    
    img = Image.open(input_path)
    # img = img.convert("RGBA")
    
    # Background removal removed logic

    # Save PNG
    png_path = os.path.join(output_dir, "icon.png")
    img.save(png_path, "PNG")
    print(f"Saved {png_path}")
    
    # Save ICO (Win specific sizes)
    ico_path = os.path.join(output_dir, "icon.ico")
    img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Saved {ico_path}")

if __name__ == "__main__":
    # Look for logo in root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Try common extensions
    found = False
    for ext in ["png", "jpg", "jpeg"]:
        path = os.path.join(root_dir, f"logo.{ext}")
        if os.path.exists(path):
            process_logo(path, os.path.join(root_dir, "src", "gui", "assets"))
            found = True
            break
            
    if not found:
        print("No logo found! Please save your image as 'logo.png' or 'logo.jpg' in the project root folder.")
