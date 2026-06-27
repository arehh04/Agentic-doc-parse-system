import os
import base64
from parser.document_parser import parse_sroie_box_file

class DocumentParsingAgent:
    """
    Agent responsible for converting raw input documents (images or box text files)
    into a structured text string for extraction.
    
    Now uses HuggingFace Serverless VLM (Zero RAM) for image OCR.
    """
    
    def __init__(self):
        self.hf_token = os.environ.get("HF_TOKEN")
        self.model = "meta-llama/Llama-3.2-11B-Vision-Instruct"
        
    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def parse_file(self, file_path: str) -> str:
        """
        Parses a file. Uses HF Serverless VLM for .jpg/.png images, and our custom parser for .txt box files.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = file_path.lower().split('.')[-1]
        
        if ext == 'txt':
            return parse_sroie_box_file(file_path)
        elif ext in ['jpg', 'jpeg', 'png']:
            print(f"[VLM OCR] Extracting text from image via HF Serverless API: {file_path}")
            if not self.hf_token:
                raise ValueError("500: HF_TOKEN environment variable is missing. Please set HF_TOKEN in your HuggingFace Space Secrets to use the Serverless VLM OCR.")
            
            base64_image = self._encode_image(file_path)
            
            # Using OpenAI compatible API for HuggingFace
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api-inference.huggingface.co/v1/",
                api_key=self.hf_token
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extract all the text from this receipt. Output only the transcribed text, maintaining the logical structure, layout, and order of the receipt items. Do not add conversational text."
                            },
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/{ext};base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=1500,
            )
            return response.choices[0].message.content
        else:
            raise NotImplementedError(f"Parsing for extension .{ext} not yet implemented.")
