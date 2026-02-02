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
        # Convert PIL image to OpenCV format
        open_cv_image = np.array(image) 
        
        # Check if image has 3 channels (RGB) before converting
        if len(open_cv_image.shape) == 3:
             # Convert RGB to BGR 
            open_cv_image = open_cv_image[:, :, ::-1].copy() 
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        elif len(open_cv_image.shape) == 2:
            # Already grayscale
            gray = open_cv_image
        else:
            # Handle RGBA
             open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
             gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        
        # Simple thresholding
        # _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        # Run OCR
        # custom_config = r'--oem 3 --psm 6'
        text_data = pytesseract.image_to_string(gray)
        
        extracted_items = extract_items_from_text(text_data, i + 1)
        all_extracted_data.extend(extracted_items)

    return all_extracted_data

def extract_items_from_text(text, page_number):
    items = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # --- 1. Dimensions with Tolerances ---
        # Pattern ideas: 
        # 50.0 +/- 0.1
        # 50.0 +0.1/-0.2
        # 50 +/-0.1
        # H7, g6 (Fit tolerances)
        
        # Regex for Basic Linear Dimension + Tolerance
        # Matches: 12.5 +/-0.1, 15 ± 0.05
        dim_tol_pattern = r"(\d+\.?\d*)\s*(?:±|\+\/-)\s*(\d+\.?\d*)"
        matches = re.findall(dim_tol_pattern, line)
        for m in matches:
            items.append({
                "type": "Dimension",
                "value": m[0],
                "tolerance": f"±{m[1]}",
                "original_text": line,
                "page": page_number
            })
            
        # Regex for Upper/Lower limits
        # Matches: 12.5 +0.1 -0.2 (simplified)
        # hard to capture nicely in single line regex without getting messy, 
        # but let's try a simple one for space separated formatted text
        # Assumes text comes out linear like "50 +0.1 -0.1" which isn't always true in OCR
        
        # --- 2. Geometric Tolerance (GD&T) ---
        # Searching for keywords often found in control frames or notes
        # Parallelism, Perpendicularity, Flatness, Position
        gdt_keywords = {
            "⏊": "Perpendicularity",
            "//": "Parallelism",
            "⌖": "Position",
            "O": "Cylindricity", # OCR might read circle symbol as O
            "◎": "Concentricity"
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
