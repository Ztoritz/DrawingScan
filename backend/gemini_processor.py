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
        3. **GD&T Feature Control Frames**:
           - **Structure**: A rectangular box divided into cells: `[ Symbol | Tolerance | Datum(s) ]`.
           - **Example in Drawing**: `[ ◎ | Ø0.1 | A ]` (Concentricity of 0.1 relative to Datum A).
           - **Action**: Extract these fully.
             - Type: "GD&T"
             - Subtype: "Concentricity" (or Position/Perpendicularity based on symbol)
             - Value: "Ø0.1" (Include the diameter symbol if inside the frame)
             - Datum: "A"
        4. **Tolerances**:
           - Capture `±`, `+`, `-`, or limit codes (H7, etc).
           
        *** EXTENSIVE TRAINING DATA ***
        
        Example 1 (Linear Dimension):
        Input: A line with text "50 ± 0.1"
        Output: { "type": "Dimension", "subtype": "Linear", "value": "50", "tolerance": "±0.1", "original_text": "50 ± 0.1" }

        Example 2 (Diameter with Concentricity):
        Input: Text "Ø20 H7" and a frame "[ ◎ | Ø0.05 | A ]"
        Output: [
          { "type": "Dimension", "subtype": "Diameter", "value": "20", "tolerance": "H7", "original_text": "Ø20 H7" },
          { "type": "GD&T", "subtype": "Concentricity", "value": "Ø0.05", "datum": "A", "original_text": "[◎|Ø0.05|A]" }
        ]

        Example 3 (Position with Modifiers):
        Input: A frame "[ ⌖ | Ø0.25 (M) | A | B | C ]"
        Output: { "type": "GD&T", "subtype": "Position", "value": "Ø0.25 (M)", "datum": "A, B, C", "original_text": "[⌖|Ø0.25(M)|A|B|C]" }

        Example 4 (Basic Dimension):
        Input: A number "50" inside a rectangle: "[50]"
        Output: { "type": "Dimension", "subtype": "Basic", "value": "50", "tolerance": "Basic", "original_text": "[50]" }

        *** END TRAINING ***
        
        Analyze the image and Return ONLY a JSON Array.
        """
        
        try:
            img = Image.open(image_path)
            # Use a slightly higher temperature to encourage creative extraction but strict JSON
            generation_config = genai.types.GenerationConfig(
                temperature=0.2, # Low temp for precision
                candidate_count=1
            )
            
            response = self.model.generate_content(
                [system_prompt, prompt, img],
                generation_config=generation_config
            )
            
            # Clean response to ensure json
            text = response.text.strip()
            
            # Debug: Print raw text to console (visible in Coolify logs)
            print(f"GEMINI RAW RESPONSE: {text[:200]}...")

            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # Handle case where AI returns plain text list without code blocks
            if not text.startswith('[') and '[' in text:
                text = text[text.find('['):text.rfind(']')+1]

            return json.loads(text)
            
        except Exception as e:
            print(f"Gemini Application Error: {e}")
            # print(f"Failed Text was: {response.text}") # Uncomment if needed
            return []
