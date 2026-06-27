import os
import base64
import requests
import io
from PIL import Image
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
        with Image.open(image_path) as img:
            # Resize image to prevent massive JSON payloads dropping the HF connection
            max_size = 1024
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Ensure it's in a compatible mode
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
                
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
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
            
            # Using direct requests for better error handling and visibility
            api_url = f"https://api-inference.huggingface.co/models/{self.model}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            # Ensure correct mime type
            mime_ext = "jpeg" if ext in ["jpg", "jpeg"] else ext
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extract all the text from this receipt. Output only the transcribed text, maintaining the logical structure, layout, and order of the receipt items. Do not add conversational text."
                            },
                            {
                                "type": "image_url", 
                                "image_url": {"url": f"data:image/{mime_ext};base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                "max_tokens": 1500,
            }
            
            try:
                # Add verify=False if there are SSL issues, but standard is True
                response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                if response.status_code != 200:
                    error_msg = response.text
                    raise Exception(f"HF API Error {response.status_code}: {error_msg}")
                
                response_json = response.json()
                if "choices" in response_json and len(response_json["choices"]) > 0:
                    return response_json["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Unexpected API response format: {response_json}")
            except requests.exceptions.ConnectionError as e:
                raise Exception(f"Connection error to HuggingFace API. Payload might be too large or the API is down. Details: {str(e)}")
            except requests.exceptions.Timeout:
                raise Exception("HuggingFace API timeout. The VLM took too long to process the image.")
            except Exception as e:
                raise Exception(str(e))
            
        else:
            raise NotImplementedError(f"Parsing for extension .{ext} not yet implemented.")
