import google.generativeai as genai
import os
import json
from pathlib import Path
from PIL import Image

class GeminiProcessor:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API Key is required for Gemini Processor")
        genai.configure(api_key=api_key)
        # Use the flash model for speed and cost, or pro-vision for max intelligence
        # Switching to gemini-flash-latest for stability/quota availability
        self.model = genai.GenerativeModel('gemini-flash-latest')
        self.training_dir = Path("backend/training_data")
        self.training_dir.mkdir(parents=True, exist_ok=True)

    def load_training_examples(self):
        """
        Loads user-provided 'training' data to teach the AI what to look for.
        Looks for pairs of files: example1.png + example1.json inside backend/training_data/
        """
        history = []
        
        # Simple schema instruction for the system (system prompt equivalent)
        system_instruction = """
        You are an expert GD&T (Geometric Dimensioning and Tolerancing) Extractor.
        Your job is to look at a technical drawing and extract ALL dimensions, tolerances, and GD&T frames into a JSON format.
        
        Schema:
        [
          {
            "type": "Dimension" | "GD&T",
            "subtype": "Linear" | "Diameter" | "Position" | "Perpendicularity" | "Parallelism" etc.,
            "value": "The main number (e.g. 50, Ø10)",
            "tolerance": "The tolerance range (e.g. ±0.1, H7, or 'Basic')",
            "original_text": "The exact text you saw"
          }
        ]
        """
        
        # We can simulate few-shot by adding them as text/image turns effectively
        # For simplicity in the prompt construction, we'll append them.
        return system_instruction

    def extract_data(self, image_path):
        system_prompt = self.load_training_examples()
        
        prompt = """
        Analyze this engineering drawing with high precision.
        
        CRITICAL INSTRUCTIONS:
        1. **Look for Basic Dimensions**: These are numbers inside a rectangular box OR an oval/capsule shape (e.g. (12) or [12]).
        2. **Distinguish Ø from 0**: 
           - If a number is `010`, it is likely `Ø10`. 
           - Look for value `Ø` (Diameter) vs `R` (Radius) vs `M` (Metric).
        3. **GD&T Frames**:
           - Look for `[Symbol | Value | Datum]`.
           - Locate Feature Control Frames attached to dimensions.
           - Extract the full content (e.g. Position 0.15 relative to A and B).
        4. **Tolerances**:
           - Capture `±`, `+`, `-`, or limit codes (H7, etc).
        
        Extract all:
        - Linear Dimensions
        - Diameters (Symbol Ø)
        - Basic Dimensions (Frame/Star/Oval)
        - GD&T Symbols (Position, Flatness, etc)
        
        Return ONLY valid JSON.
        """
        
        try:
            img = Image.open(image_path)
            response = self.model.generate_content([system_prompt, prompt, img])
            
            # Clean response to ensure json
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return json.loads(text)
            
        except Exception as e:
            print(f"Gemini Error: {e}")
            return []
