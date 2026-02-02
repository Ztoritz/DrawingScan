import os
from gemini_processor import GeminiProcessor
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
print(f"Key loaded: {api_key[:10]}...")

try:
    processor = GeminiProcessor(api_key)
    # Using the path to the 'simple' drawing uploaded earlier
    image_path = r"C:/Users/Ztoritz Z/.gemini/antigravity/brain/84dfdbf0-ccb2-4100-93b6-9a797007245d/uploaded_media_1770062547031.png"
    
    print(f"Analyzing image: {image_path}")
    data = processor.extract_data(image_path)
    print("\n--- GEMINI EXTRACTION RESULTS ---")
    import json
    print(json.dumps(data, indent=2))
    print("---------------------------------")
except Exception as e:
    print(f"Error: {e}")


