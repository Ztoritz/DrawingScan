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
    Main function to process a file (PDF or Image) and extract Drawing data.
    """
    file_path = str(file_path).lower()
    
    if file_path.endswith('.pdf'):
        images = convert_from_path(file_path)
    else:
        # Assume it's an image file supported by PIL/OpenCV
        # We wrap it in a list to reuse the loop below
        try:
            # Open with PIL first to verify/convert
            from PIL import Image
            pil_image = Image.open(file_path)
            images = [pil_image]
        except Exception as e:
            print(f"Error opening image: {e}")
            return []

    all_extracted_data = []

    for i, image in enumerate(images):
        open_cv_image = np.array(image) 
        
        # Ensure BGR format for OpenCV
        if len(open_cv_image.shape) == 3:
             # Convert RGB to BGR if coming from PIL
             # Note: pdf2image returns RGB, cv2 reads/writes BGR
            open_cv_image = open_cv_image[:, :, ::-1].copy() 
            gray_original = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        elif len(open_cv_image.shape) == 2:
            gray_original = open_cv_image
        else:
             open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
             gray_original = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        
        # --- STRATEGY 1: High Scaling + Adaptive (Good for small decimals) ---
        gray_scaled = cv2.resize(gray_original, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        # Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        gray_scaled = cv2.filter2D(gray_scaled, -1, kernel)
        
        gray_adaptive = cv2.adaptiveThreshold(
            gray_scaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )

        # --- STRATEGY 2: Moderate Scale + Simple Threshold (Good for clean, high contrast drawings) ---
        # 2x scale often preserves geometry better than 3x for larger lines
        gray_mod = cv2.resize(gray_original, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
        _, gray_binary = cv2.threshold(gray_mod, 180, 255, cv2.THRESH_BINARY)
        
        # --- STRATEGY 3: Raw (Good if thresholds destroy faint dim lines) ---
        # Sometimes raw grayscale is best for Tesseract's internal binarization
        
        # Collect text from all strategies
        combined_text = ""
        
        # Configs to run
        configs = [
            r'--oem 3 --psm 6',   # Block
            r'--oem 3 --psm 11',  # Sparse
        ]

        # 1. Run on High Res Adaptive
        for config in configs:
            combined_text += "\n" + pytesseract.image_to_string(gray_adaptive, config=config)
            
        # 2. Run on Moderate Simple Binary
        combined_text += "\n" + pytesseract.image_to_string(gray_binary, config=r'--oem 3 --psm 6')
        
        # 3. Run on Original (Raw)
        combined_text += "\n" + pytesseract.image_to_string(gray_original, config=r'--oem 3 --psm 3')

        extracted_items = extract_items_from_text(combined_text, i + 1)
        
        # Deduplication (Crucial when running multiple strategies)
        seen_values = set()
        unique_items = []
        for item in extracted_items:
            # Create a unique signature
            # We treat close values as identical? For now exact match.
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
