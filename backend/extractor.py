import re

import os

# --- CLOUD AI INTEGRATION ---
gemini_client = None
qwen_client = None
init_error = None

def init_reader():
    """
    Initializes Cloud Clients. Checks for API keys.
    """
    global gemini_client, qwen_client, init_error
    
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
            
    if init_error:
        print(f"❌ Critical Error: {init_error}")

def get_active_engine():
    """Returns the name of the currently active engine."""
    global qwen_client, gemini_client, init_error
    if qwen_client:
        return f"Qwen 2.5 VL (Cloud)"
    if gemini_client:
        return "Gemini Flash 2.0 (Cloud)"
    return f"NONE - {init_error or 'No Engine Loaded'}"

def process_file(file_path):
    # Ensure init
    global gemini_client, qwen_client
    if gemini_client is None and qwen_client is None:
        init_reader()

    # --- PRIORITY 1: QWEN 2.5 (Vision) ---
    if qwen_client:
        print("🧠 Processing with Qwen 2.5 VL...")
        try:
             # Handle PDFs by converting to image first
             target_path = file_path
             if str(file_path).lower().endswith('.pdf'):
                from pdf2image import convert_from_path
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
                print("Gemini returned empty results.")
        except Exception as e:
             print(f"Gemini Application Error: {e}")

    # --- NO ENGINE AVAILABLE ---
    print("❌ No active extraction engine available. Please check API Keys.")
    return []
