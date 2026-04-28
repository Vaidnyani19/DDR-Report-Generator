import fitz
import os
from PIL import Image
import io

def extract_from_pdf(pdf_path, output_img_dir, source_name):
    """
    Extract text AND images from any PDF.
    Returns: (full_text: str, image_list: list of dicts)
    """
    os.makedirs(output_img_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    full_text = ""
    image_list = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text
        text = page.get_text()
        if text.strip():
            full_text += f"\n=== Page {page_num + 1} ===\n{text}"
        
        # CORRECT way to extract images using get_images(full=True)
        image_index = 0
        for img_info in page.get_images(full=True):
            try:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                
                if base_image is None:
                    continue
                    
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                
                # Skip tiny images (logos, icons) under 5KB
                if len(image_bytes) < 5000:
                    continue
                
                # Validate image using Pillow
                try:
                    img = Image.open(io.BytesIO(image_bytes))
                    width, height = img.size
                    # Skip very small images
                    if width < 100 or height < 100:
                        continue
                    
                    # Optimization: Write raw bytes if it's already a standard format to avoid slow re-encoding
                    if ext.lower() in ['jpeg', 'jpg', 'png']:
                        img_filename = f"{output_img_dir}/{source_name}_p{page_num+1}_i{image_index}.{ext}"
                        with open(img_filename, "wb") as f:
                            f.write(image_bytes)
                    else:
                        img_filename = f"{output_img_dir}/{source_name}_p{page_num+1}_i{image_index}.jpg"
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        img.save(img_filename, "JPEG", quality=85)
                        
                    print(f"Saved {img_filename} (Size: {os.path.getsize(img_filename)} bytes)")
                except Exception as e:
                    print(f"Failed to process/save image on page {page_num+1}: {e}")
                    continue
                
                image_list.append({
                    "path": img_filename,
                    "page": page_num + 1,
                    "source": source_name,
                    "index": image_index,
                    "width": width,
                    "height": height
                })
                image_index += 1
                
            except Exception as e:
                print(f"Image extraction error page {page_num+1}: {e}")
                continue
    
    doc.close()
    print(f"[{source_name}] Extracted {len(image_list)} images, {len(full_text)} chars text")
    return full_text, image_list


def get_thermal_images_only(image_list):
    """
    From thermal PDF images, separate thermal scans from real photos.
    In Thermal_Images.pdf each page has 2 images:
    - First image = thermal heat map (usually wider/landscape)  
    - Second image = real photo of location
    Returns two lists: thermal_maps, real_photos
    """
    thermal_images = [img for img in image_list if img["source"] == "thermal"]
    
    thermal_maps = []
    real_photos = []
    
    # Group by page - first image per page = thermal map, second = real photo
    pages = {}
    for img in thermal_images:
        p = img["page"]
        if p not in pages:
            pages[p] = []
        pages[p].append(img)
    
    for page_num in sorted(pages.keys()):
        imgs = pages[page_num]
        if len(imgs) >= 1:
            thermal_maps.append(imgs[0])
        if len(imgs) >= 2:
            real_photos.append(imgs[1])
    
    return thermal_maps, real_photos
