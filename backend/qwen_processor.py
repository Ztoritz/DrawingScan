import os
import base64
import json
from openai import OpenAI
from pathlib import Path

class QwenProcessor:
    def __init__(self, api_key, base_url=None, model="qwen/qwen-2.5-vl-72b-instruct"):
        """
        Initialize Qwen Processor.
        :param api_key: API Key for the provider (OpenRouter, DeepInfra, vLLM, etc.)
        :param base_url: Base URL for the API (e.g., https://openrouter.ai/api/v1)
        :param model: The specific model string to use. Defaulting to a high-end 72B model.
        """
        if not api_key:
            raise ValueError("API Key is required for Qwen Processor")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else "https://openrouter.ai/api/v1" 
        )
        self.model = model
        print(f"🚀 Qwen Processor Initialized with Model: {self.model}")

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def get_system_prompt(self):
        return """
        You are an elite Metrology AI specialist in Geometric Dimensioning and Tolerancing (GD&T).
        Your task is to extract engineering data from technical drawings with 100% precision.
        
        You must identify:
        1. Linear Dimensions (with tolerances like H7, ±0.1, limits).
        2. GD&T Feature Control Frames (Symbol | Value | Datum).
           - Symbols: ⌖ (Position), ⏊ (Perpendicularity), ∥ (Parallelism), ◎ (Concentricity), ↗ (Runout).
        3. Basic Dimensions (Boxed values).
        4. Chamfers and Radii.

        OUTPUT FORMAT:
        Return ONLY a JSON Array. Do not include markdown formatting like ```json.
        [
          {
            "type": "Dimension" | "GD&T",
            "subtype": "Linear" | "Diameter" | "Position" | "Runout" | "Concentricity" | "Chamfer",
            "value": "The measured value (e.g. 20.0, Ø10, 1x45°)",
            "tolerance": "The tolerance string (e.g. ±0.1, H7, Basic)",
            "datum": "A (Only for GD&T)",
            "original_text": "The raw text found",
            "box_2d": [ymin, xmin, ymax, xmax]  // Normalised 0-1000 based on image size
          }
        ]
        """

    def extract_data(self, image_path):
        base64_image = self.encode_image(image_path)
        
        system_instruction = self.get_system_prompt()
        
        # User prompt with specific Qwen-optimized instructions
        user_prompt = """
        Extract all dimensions and GD&T from this drawing.
        
        Critical Rules:
        - EXTRACT BOUNDING BOXES for every single item using [ymin, xmin, ymax, xmax] format (0-1000 scale).
        - If you see a circle with crosshairs (⌖), it is Position.
        - If you see two concentric circles (◎), it is Concentricity.
        - If you see a simple arrow (↗), it is Runout.
        - Look for "H7", "g6", etc. as tolerances.
        - Treat "1x45°" as a Dimension (Subtype: Chamfer).
        
        Return pure JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_instruction
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high" # Force high resolution processing
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1, # Low temperature for factual extraction
                max_tokens=2000
            )

            # Extract content
            content = response.choices[0].message.content.strip()
            
            print(f"QWEN RAW RESPONSE: {content[:200]}...")
            
            # Clean Markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            # Attempt parsing
            return json.loads(content)

        except Exception as e:
            print(f"Qwen Processing Error: {e}")
            return []
