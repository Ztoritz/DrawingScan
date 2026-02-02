import re
from pdf2image import convert_from_path
import cv2
import numpy as np
import os

# --- CLOUD AI INTEGRATION ---
gemini_client = None
qwen_client = None
reader = None
init_error = None

def init_reader():
    """
    Initializes OCR engines. Checks for API keys to determine mode.
    """
    global reader, gemini_client, qwen_client, init_error
    
    init_error = "No Cloud Keys Found"

    # Check Qwen First (User Preference)
    qwen_key = os.environ.get("QWEN_API_KEY")
    if qwen_key:
        try:
            print(f"DEBUG: Found QWEN_API_KEY: {qwen_key[:5]}...")
            from qwen_processor import QwenProcessor
            base_url = os.environ.get("QWEN_BASE_URL")
            model = os.environ.get("QWEN_MODEL", "qwen/qwen-2.5-vl-72b-instruct") 
            print(f"🚀 Initializing Qwen 2.5... (Model: {model})")
            qwen_client = QwenProcessor(api_key=qwen_key, base_url=base_url, model=model)
            print("✅ Qwen 2.5 Connected.")
            init_error = None
            return # Success
        except Exception as e:
            init_error = f"Qwen Init Failed: {str(e)}"
            print(f"⚠️ Failed to connect to Qwen: {e}")

    # Check Gemini Second
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and not qwen_client:
        print("🚀 Gemini AI Detected. Initializing Cloud Engine...")
        try:
             from gemini_processor import GeminiProcessor
             gemini_client = GeminiProcessor(gemini_key)
             print("✅ Gemini Pro Connected.")
             init_error = None
             return
        except Exception as e:
            init_error = f"Gemini Init Failed: {str(e)}"
            print(f"⚠️ Failed to connect to Gemini: {e}")
    
    # Always load EasyOCR as fallback
    if reader is None:
        try:
            import easyocr
            print("Initializing EasyOCR (Fallback/Local)...")
            reader = easyocr.Reader(['en'], gpu=False)
            print("EasyOCR Initialized.")
        except ImportError:
            print("⚠️ EasyOCR not installed. Local fallback disabled to save build size.")
            if not init_error:
                init_error = "No Cloud Keys & No Local OCR"

def get_active_engine():
    """Returns the name of the currently active engine."""
    global qwen_client, gemini_client
    if qwen_client:
        # parsed_model = qwen_client.model.split('/')[-1] # Simplification
        return f"Qwen 2.5 VL (Cloud)"
    if gemini_client:
        return "Gemini Flash 2.0 (Cloud)"
    return "EasyOCR (Local)"

def process_file(file_path):
    # Ensure init
    global reader, gemini_client, qwen_client
    if reader is None and gemini_client is None and qwen_client is None:
        init_reader()

    # --- PRIORITY 1: QWEN 2.5 (Vision) ---
    if qwen_client:
        print("🧠 Processing with Qwen 2.5 VL...")
        try:
             # Handle PDFs by converting to image first
             target_path = file_path
             if str(file_path).lower().endswith('.pdf'):
                images = convert_from_path(file_path)
                if images:
                    target_path = file_path + "_temp.png"
                    images[0].save(target_path)
            
             results = qwen_client.extract_data(target_path)
             
             # Cleanup
             if target_path != file_path and os.path.exists(target_path):
                 os.remove(target_path)
             
             if results:
                 # --- ENRICHMENT STEP: ISO TOLERANCES ---
                 try:
                     # Lazy import to avoid circular dep issues during startup if any
                     from iso_fits import calculate_iso_limits
                     
                     for item in results:
                         # Only enrich Dimensions (Linear/Diameter)
                         if item.get("type") == "Dimension" and item.get("subtype") in ["Diameter", "Linear", "Basic"]:
                             tol = item.get("tolerance", "")
                             val = str(item.get("value", "0")).replace("Ø", "").strip()
                             
                             # Check for ISO code patterns (e.g. H7, g6, f7)
                             # Heuristic: Starts with letter, length <= 4
                             if tol and len(tol) <= 5 and tol[0].isalpha():
                                 limits = calculate_iso_limits(val, tol)
                                 if limits:
                                     item["calculated_limits"] = limits  # Add new field
                 except ImportError:
                     print("⚠️ ISO Fits library not found. Skipping enrichment.")
                 except Exception as e:
                     print(f"⚠️ ISO Enrichment Failed: {e}")
                                 
                 return results
        except Exception as e:
            print(f"Qwen Error: {e}")

    # --- PRIORITY 2: CLOUD AI (GEMINI) ---
    if gemini_client:
        print("🧠 Processing with Gemini Pro...")
        try:
            # Gemini handles PDFs/Images natively or via PIL.
            # Convert PDF to image if needed first
            target_path = file_path
            
            # If PDF, convert first page to image for Gemini (simplification for now)
            # Full PDF support exists but image is safer for "Vision" endpoint usually
            if str(file_path).lower().endswith('.pdf'):
                images = convert_from_path(file_path)
                if images:
                    # Save temporary image for Gemini
                    target_path = file_path + "_temp.png"
                    images[0].save(target_path)
            
            results = gemini_client.extract_data(target_path)
            
            # Cleanup temp
            if target_path != file_path and os.path.exists(target_path):
                os.remove(target_path)
                
            if results:
                return results
            else:
                print("Gemini returned empty results. Falling back to local OCR.")
        except Exception as e:
             print(f"Gemini Application Error: {e}. Falling back to local OCR.")

    # --- FALLBACK: LOCAL EASYOCR ---
    print("👀 Processing with Local EasyOCR...")

def get_active_engine():
    """Returns the name of the currently active engine."""
    global gemini_client, qwen_client, init_error
    if qwen_client:
        return f"Qwen 2.5 VL (Cloud)"
    if gemini_client:
        return "Gemini Flash 2.0 (Cloud)"
    
    # Fallback case
    return f"EASYOCR (LOCAL) - {init_error or 'Unknown Error'}"

def process_file(file_path):
    # Ensure init
    global reader, gemini_client
    # Ensure reader is loaded if process_file is called without init (e.g. testing)
    global reader
    if reader is None:
        init_reader()

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

    all_extracted_data = []

    for i, image in enumerate(images):
        open_cv_image = np.array(image)
        
        # Ensure BGR format for OpenCV
        if len(open_cv_image.shape) == 3:
            open_cv_image = open_cv_image[:, :, ::-1].copy() 
            # Use Grayscale for OCR to save memory (1 channel vs 3)
            gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        elif len(open_cv_image.shape) == 2:
             gray = open_cv_image
        else:
             open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
             gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

        # --- SMART IMAGE NORMALIZATION ---
        # Handle "different sizes" (scaling up small ones, capping large ones)
        height, width = gray.shape[:2]
        long_side = max(height, width)
        
        target_min = 1500
        target_max = 3072 # Increased from 2000 to allow more detail
        
        if long_side < target_min:
            # Upscale small images to at least 1500px
            scale = target_min / long_side
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        elif long_side > target_max:
            # Downscale massive images to avoid OOM
            scale = target_max / long_side
            gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        # --- CONTRAST ENHANCEMENT (CLAHE) ---
        # "Adjust" for difficult drawings. This brings out faint text.
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

        # --- EasyOCR Execution ---
        # Tuned parameters for Engineering Drawings:
        # text_threshold=0.6 (default 0.7) -> Find fainter text
        # link_threshold=0.4 (default 0.4)
        # low_text=0.35 (default 0.4) -> Keep lower confidence text
        # width_ths=0.7 (Merge separate characters closer together)
        try:
            results = reader.readtext(
                gray, 
                detail=1,
                text_threshold=0.6,
                low_text=0.35,
                width_ths=0.7 
            )
        except Exception as e:
            print(f"OCR Error on page {i+1}: {e}")
            continue
        
        combined_text = ""
        for (bbox, text, prob) in results:
            if prob > 0.3: # Filter really bad guesses
                combined_text += "\n" + text

        extracted_items = extract_items_from_text(combined_text, i + 1)
        
    # --- Deduplication ---
    # Deduplicate based on distinct content signature
    seen_values = set()
    unique_items = []
    
    # Debug: Print raw text to help diagnose what EasyOCR actually saw
    print(f"--- Raw Text Page {i+1} ---")
    print(combined_text)
    print("-------------------------")

    for item in extracted_items:
        sig = f"{item['type']}-{item.get('value', '')}-{item.get('tolerance', '')}-{item.get('subtype', '')}"
        if sig not in seen_values:
            seen_values.add(sig)
            unique_items.append(item)
            
    all_extracted_data.extend(unique_items)

    return all_extracted_data

def clean_ocr_text(line):
    """
    Normalizes common OCR errors for engineering symbols.
    """
    # Fix Diameter symbols
    line = re.sub(r'(?<![A-Za-z])(?:Q|O|o)(?=\d)', 'Ø', line) # Q10 -> Ø10
    
    # Fix "010" -> "Ø10" (Leading zero followed by integer digits is usually a misread Diameter)
    # Match 0 followed by digit, BUT NOT followed by a dot (0.15 is valid)
    line = re.sub(r'\b0(?=\d+(?!\.))', 'Ø', line)

    # Fix Plus/Minus errors
    line = line.replace('t/', '+/-').replace('I-', '+/-')
    
    return line

def extract_items_from_text(text, page_number):
    items = []
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Pre-clean the line
        line = clean_ocr_text(line)
        
        # --- 1. Dimensions with Tolerances ---
        # Matches: 50.0 +/- 0.1, 12,5 ±0,1, 10+0,2 (loose)
        # We need to be very aggressive here.
        
        # 1a. Explicit Symbols (±, +/-)
        dim_tol_pattern = r"([Øø]?\s*\d+[.,]?\d*)\s*(?:±|\+\/-)\s*(\d+[.,]?\d*)"
        matches = re.findall(dim_tol_pattern, line)
        for m in matches:
            items.append({
                "type": "Dimension",
                "value": m[0].replace(' ', ''),
                "tolerance": f"±{m[1]}",
                "original_text": line,
                "page": page_number
            })
            
        # 1b. Loose Tolerance (e.g. 10+0.1 or 10-0.1 which might be asymmetric or just a misread ±)
        # This is risky but needed if OCR sees "10 + 0,2" instead of "10 ± 0,2"
        # We only match if the second number is small (< half the first) to avoid math sums
        loose_tol_pattern = r"([Øø]?\s*\d+[.,]?\d*)\s*[\+]\s*(\d+[.,]?\d*)"
        matches_loose_tol = re.findall(loose_tol_pattern, line)
        for m in matches_loose_tol:
             items.append({
                "type": "Dimension",
                "subtype": "Loose Match",
                "value": m[0].replace(' ', ''),
                "tolerance": f"±{m[1]} (Assumed)",
                "original_text": line,
                "page": page_number
            })

        # --- 2. Basic Dimensions (Boxed or Parentheses) ---
        # Matches: (12), [50.5]
        basic_dim_pattern = r"[\(\[\{]\s*(\d+[.,]?\d*)\s*[\)\]\}]"
        matches_basic = re.findall(basic_dim_pattern, line)
        for m in matches_basic:
             items.append({
                "type": "Dimension (Basic)",
                "value": m,
                "tolerance": "Basic",
                "original_text": line,
                "page": page_number
            })

        # --- 3. Limits / Fit Tolerances ---
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

        # --- 4. Standalone Dimensions ---
        # Only if NOT already matched as tolerance or basic
        if not matches and not matches_loose_tol and not matches_basic:
            
            # High Precision (3+ decimals) or Diameter
            high_prec_pattern = r"(?<!\d)([Øø]?\s*\d+[.,]\d{1,4})(?!\d)"
            matches_high = re.findall(high_prec_pattern, line)
            
            for m in matches_high:
                 val_clean = m.replace(' ', '').replace(',', '.')
                 
                 subtype = "Linear"
                 if 'Ø' in val_clean or 'ø' in val_clean:
                     subtype = "Diameter"
                     val_clean = val_clean.replace('Ø', '').replace('ø', '')

                 items.append({
                    "type": "Dimension",
                    "subtype": subtype,
                    "value": val_clean,
                    "tolerance": "General",
                    "original_text": line,
                    "page": page_number
                })

        # --- 5. GD&T (Geometric Dimensioning & Tolerancing) ---
        # Feature Control Frames often look like: [ Symbol | 0.15 | A | B ]
        # OCR often sees them as: "| 0.15 | A | B" or "1 0.15 1 A 1 B"
        
        # 5a. Fuzzy Symbol Mapping (Common OCR misreads)
        gdt_fuzzy_map = {
            "⏊": "Perpendicularity", "_|_": "Perpendicularity", "L": "Perpendicularity",
            "//": "Parallelism", "||": "Parallelism", "11": "Parallelism",
            "⌖": "Position", "(+)": "Position", "Q": "Position",  # 'Q' often misread for Position circle+cross
            "O": "Cylindricity", 
            "◎": "Concentricity", "(O)": "Concentricity",
            "∠": "Angularity",
            "⏥": "Profile of Surface",
            "⌭": "Profile of Line",
             "↗": "Runout"
        }

        # Check for explicit symbols first
        found_gdt_type = None
        for symbol, name in gdt_fuzzy_map.items():
            if symbol in line:
                found_gdt_type = name
                break
        
        # 5b. Feature Control Frame Structure Detection
        # Relaxed Pattern: Look for "Value" followed by "Datum" 
        # Value can start with Ø, Q, O, or just be a float like 0.15 or O.15
        # Datum is a Capital Letter
        # They might be separated by |, /, 1, I, spaces, or nothing
        
        # Regex breakdown:
        # 1. (?:[ØøQC]|O)? -> Optional Start Symbol (Diameter, Position, or letter O misread)
        # 2. \s* -> Spaces
        # 3. (?:[O0-9]+[.,][0-9]+) -> The Value (e.g. 0.15 or O.15)
        # 4. \s*(?:[|/!lI1]|\s)*\s* -> Optional Separators (Pipes or spaces)
        # 5. ([A-Z]) -> The Datum (Capture Group 2)
        
        fcf_pattern = r"((?:[ØøQCO]|\(?)\s*[O0-9]+[.,][0-9]+)\s*(?:[|/!lI1]|\s)*\s*([A-Z])"
        match_fcf = re.search(fcf_pattern, line)
        
        if match_fcf or found_gdt_type:
            # If we found a structure OR a symbol, try to extract the useful parts
            
            # Default to Position if we see a frame/datum structure but no symbol
            if not found_gdt_type:
                if match_fcf and ("Ø" in line or "Q" in line or "(" in line or "O" in line):
                     found_gdt_type = "Position (Inferred)"
                else: 
                     found_gdt_type = "GD&T Frame"

            # Extract the main value (tolerance)
            value = "Unknown"
            if match_fcf:
                # Group 1 is the value part
                raw_val = match_fcf.group(1).replace(' ', '')
                # normalize O to 0 if it's the leading digit (O.15 -> 0.15)
                # But careful not to replace Ø (if represented as O)
                if 'O.' in raw_val or 'O,' in raw_val:
                    raw_val = raw_val.replace('O.', '0.').replace('O,', '0,')
                    
                value = raw_val
                
                # Ensure diameter symbol is pretty
                if 'Ø' in line or 'Q' in line or 'O' in line:
                    if 'Ø' not in value and '0.' in value: # Only add if it looks like a diameter value
                         # Check if the O was actually the diameter symbol
                         if value.startswith('0'):
                             value = 'Ø' + value
            
            # Strict Filter: Must have a Datum (A, B, C...) or a strong GDT Symbol to be valid
            # This prevents random text "Version 1.0 A" from becoming GD&T
            has_datum = match_fcf and match_fcf.group(2) in "ABCDEFGHJKLMNPRSTuvwxyz"
            
            if found_gdt_type and (has_datum or found_gdt_type != "GD&T Frame"):
                items.append({
                    "type": "GD&T",
                    "subtype": found_gdt_type,
                    "value": value,
                    "original_text": line,
                    "page": page_number
                })

    return items
