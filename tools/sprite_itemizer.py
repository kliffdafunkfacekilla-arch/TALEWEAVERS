
import os
import json
from PIL import Image

def itemize_spritesheet(sheet_path, output_dir, grid_size=(32, 32), mode="grid"):
    """
    Slices a spritesheet into individual icons and generates a manifest.
    """
    if not os.path.exists(sheet_path):
        print(f"Error: {sheet_path} not found.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    img = Image.open(sheet_path).convert("RGBA")
    width, height = img.size
    
    manifest = []
    
    if mode == "grid":
        sprite_w, sprite_h = grid_size
        cols = width // sprite_w
        rows = height // sprite_h
        
        count = 0
        for r in range(rows):
            for c in range(cols):
                box = (c * sprite_w, r * sprite_h, (c + 1) * sprite_w, (r + 1) * sprite_h)
                sprite = img.crop(box)
                
                # Check if sprite is empty (fully transparent)
                extrema = sprite.getextrema()
                if extrema[3][1] > 0: # Alpha channel max > 0
                    count += 1
                    filename = f"sprite_{count:03d}.png"
                    sprite.save(os.path.join(output_dir, filename))
                    manifest.append({
                        "id": count,
                        "file": filename,
                        "grid_pos": [c, r]
                    })
                    
        print(f"Slicing complete. Extracted {count} sprites into {output_dir}.")
    
    # Save Manifest
    with open(os.path.join(output_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
        
    # Generate HTML Preview
    generate_preview(manifest, output_dir)

def generate_preview(manifest, output_dir):
    html = """
    <html>
    <head>
        <style>
            body { background: #0f172a; color: white; font-family: sans-serif; padding: 20px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; }
            .item { background: #1e293b; border: 1px solid #334155; padding: 10px; text-align: center; border-radius: 8px; }
            img { width: 64px; height: 64px; object-fit: contain; image-rendering: pixelated; }
            .id { font-size: 12px; color: #94a3b8; margin-top: 5px; }
        </style>
    </head>
    <body>
        <h1>Sprite Sheet Catalog</h1>
        <p>Use the IDs below to reference sprites in the SAGA Brain.</p>
        <div class="grid">
    """
    
    for item in manifest:
        html += f'''
        <div class="item">
            <img src="sprites/{item['file']}">
            <div class="id">ID: {item['id']}</div>
        </div>
        '''
        
    html += "</div></body></html>"
    
    # Since relative paths in HTML usually work better from the public root
    preview_path = os.path.join(os.path.dirname(output_dir), "catalog.html")
    with open(preview_path, "w") as f:
        f.write(html)
    print(f"Preview generated at {preview_path}")

if __name__ == "__main__":
    # Default behavior: look for spritesheet.png in root
    itemize_spritesheet("spritesheet.png", "vtt/public/assets/sprites", grid_size=(32, 32))
