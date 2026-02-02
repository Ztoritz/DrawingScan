import re
try:
    from pdf2image import convert_from_path
    import pytesseract
    import cv2
    import numpy as np
except ImportError:
    # Fallback/Mock for environment where dependnecies aren't fully installed yet
    # This helps prevents crashes during initial file creation if the user inspects code
    pass

# NOTE: You might need to install poppler for pdf2image and tesseract-ocr executable for pytesseract
# Windows users typically need to add them to PATH

def process_file(file_path):
    """
    Main function to process a file (PDF or Image) using EasyOCR (Deep Learning).
    """
    import easyocr
    file_path = str(file_path).lower()
    
    if file_path.endswith('.pdf'):
        images = convert_from_path(file_path)
    else:
        try:
            from PIL import Image
            pil_image = Image.open(file_path)
            images = [pil_image]
        except Exception as e:
            print(f"Error opening image: {e}")
            return []

    # Initialize EasyOCR Reader
    # We load it here. In a prod app, you might load this once globally.
    # gpu=False for compatibility with basic VPS (will use CPU)
    reader = easyocr.Reader(['en'], gpu=False)

    all_extracted_data = []

    for i, image in enumerate(images):
        open_cv_image = np.array(image)
        
        # Ensure BGR format for OpenCV/EasyOCR
        if len(open_cv_image.shape) == 3:
             # PIL is RGB, EasyOCR/OpenCV prefers BGR usually, 
             # but EasyOCR actually handles RGB/BGR fine. Let's stick to standard OpenCV BGR.
            open_cv_image = open_cv_image[:, :, ::-1].copy() 
        elif len(open_cv_image.shape) == 2:
             # Convert gray to BGR for consistency
             open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_GRAY2BGR)
        else:
             open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
        
        # --- EasyOCR Execution ---
        # detail=0 returns just the listing of text. 
        # detail=1 returns [ [ [x,y]...], 'text', confidence ]
        # We use detail=0 for simpler parsing first, or detail=1 if we want to filter by confidence
        
        # We pass the raw image. EasyOCR is robust enough to handle scaling internally.
        # But we can still do a modest 2x upscale if results are tiny.
        # Let's trust EasyOCR raw first as it's quite smart.
        
        # results = reader.readtext(open_cv_image, detail=0) 
        # combined_text = "\n".join(results)
        
        # Let's get detailed results to filter low confidence garbage
        results = reader.readtext(open_cv_image, detail=1)
        
        combined_text = ""
        for (bbox, text, prob) in results:
            if prob > 0.3: # Filter really bad guesses
                combined_text += "\n" + text

        extracted_items = extract_items_from_text(combined_text, i + 1)
        
        # Deduplication
        seen_values = set()
        unique_items = []
        for item in extracted_items:
            sig = f"{item['type']}-{item.get('value', '')}-{item.get('tolerance', '')}-{item.get('subtype', '')}"
            if sig not in seen_values:
                seen_values.add(sig)
                unique_items.append(item)
                
        all_extracted_data.extend(unique_items)

    return all_extracted_data

def extract_items_from_text(text, page_number):
    items = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # --- 1. Dimensions with Tolerances (Strict) ---
        # Matches: 50.0 +/- 0.1, 12,5 ±0,1
        # Supports both dot and comma decimals
        dim_tol_pattern = r"([Øø]?\s*\d+[.,]?\d*)\s*(?:±|\+\/-)\s*(\d+[.,]?\d*)"
        matches = re.findall(dim_tol_pattern, line)
        for m in matches:
            items.append({
                "type": "Dimension",
                "value": m[0].replace(' ', ''), # Clean up spaces in "Ø 50"
                "tolerance": f"±{m[1]}",
                "original_text": line,
                "page": page_number
            })

        # --- 2. Limits / Fit Tolerances ---
        # Matches: 50 H7, 40 g6
        fit_pattern = r"(\d+[.,]?\d*)\s*([HhGgJsEef]\d+)"
        matches_fit = re.findall(fit_pattern, line)
        for m in matches_fit:
            items.append({
                "type": "Dimension (Fit)",
                "value": m[0],
                "tolerance": m[1],
                "original_text": line,
                "page": page_number
            })

        # --- 3. Standalone Precision Dimensions (Loose) ---
        # Matches numbers that look like precise dimensions (e.g. 50.00, 12.5) 
        # but don't have explicit tolerances next to them.

        # 3a. High Precision / Imperial (e.g., 4.0000, 1.5000) - CALIBRATED FROM SAMPLE
        # We look for 3 or 4 decimal places explicitly, which is a strong signal of a dimension.
        # Also handles fuzzy Diameter symbol (O, Q, 0) if followed by high precision number.
        high_prec_pattern = r"(?<!\d)([ØøOQ0o]?\s*\d+[.,]\d{3,4})(?!\d)"
        matches_high_prec = re.findall(high_prec_pattern, line)
        for m in matches_high_prec:
             val_clean = m.replace(' ', '').replace(',', '.')
             
             # Check if it looks like a diameter
             subtype = "Linear"
             if val_clean[0] in 'ØøOQ0o':
                 subtype = "Diameter"
                 # Strip the symbol for the value field
                 val_clean = re.sub(r'[ØøOQ0o]', '', val_clean)

             items.append({
                "type": "Dimension",
                "subtype": subtype,
                "value": val_clean,
                "tolerance": "Basic", # No explicit tolerance listed
                "original_text": line,
                "page": page_number
            })

        # 3b. Standard Precision (e.g. 12.5) - Lower confidence
        # Only if we didn't just match it as high precision (simple logic: avoid duplicates later)
        if not matches_high_prec:
            loose_dim_pattern = r"(?<!\d)([Øø]?\s*\d+[.,]\d{1,2})(?!\d)(?!\s*(?:±|\+\/-))"
            matches_loose = re.findall(loose_dim_pattern, line)
            for m in matches_loose:
                 # heuristic: Ignore small integers like 1.0 or 2.0 unless they have a diameter symbol, 
                 # as they might be typical text/numbering.
                 # But valid for 12.5
                 val = m.replace(' ', '')
                 items.append({
                    "type": "Dimension (Basic)",
                    "value": val,
                    "tolerance": "General",
                    "original_text": line,
                    "page": page_number
                })

        # --- 4. Geometric Tolerance (GD&T) ---
        # Searching for keywords often found in control frames or notes
        gdt_keywords = {
            "⏊": "Perpendicularity",
            "//": "Parallelism",
            "⌖": "Position",
            "O": "Cylindricity", 
            "◎": "Concentricity",
            "Ø": "Diameter Symbol" 
        }
        
        # Also check for standard text representations folks use if symbols fail
        gdt_text_map = {
            "PERPENDICULAR": "Perpendicularity",
            "PARALLEL": "Parallelism",
            "FLATNESS": "Flatness",
            "POSITION": "Position"
        }

        for symbol, name in gdt_keywords.items():
            if symbol in line:
                 items.append({
                    "type": "GD&T",
                    "subtype": name,
                    "value": "Symbol found", # extracting exact value is hard without spatial analysis
                    "original_text": line,
                    "page": page_number
                })

        for key, name in gdt_text_map.items():
            if key in line.upper():
                 items.append({
                    "type": "GD&T",
                    "subtype": name,
                    "value": "Text Annotation", 
                    "original_text": line,
                    "page": page_number
                })

    # Deduplicate based on original_text to avoid noise
    # (Optional refinement step)
    
    return items
