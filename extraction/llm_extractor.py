import os
import json
import logging
from pydantic import ValidationError
from langchain_openai import ChatOpenAI
from validation.schemas import ReceiptSchema
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException

# Set up logging for validation failures
logger = logging.getLogger("validation_logger")
logger.setLevel(logging.ERROR)
log_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'validation_errors.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
file_handler = logging.FileHandler(log_file_path)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(file_handler)

def extract_receipt_data(ocr_text: str, max_retries: int = 3) -> ReceiptSchema:
    """
    Extracts structured data from receipt OCR text using DeepSeek with retry logic.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set in the environment.")

    # Using the new deepseek-v4-flash model
    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        streaming=True,
        temperature=0.0,
        max_tokens=2048,
        model_kwargs={"response_format": {"type": "json_object"}}
    )
    
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'extraction_prompt.txt')
    with open(prompt_path, 'r') as f:
        system_prompt = f.read()
        
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the receipt OCR text:\n\n{ocr_text}")
    ])
    
    chain = prompt_template | llm
    
    last_error = None
    for attempt in range(max_retries):
        try:
            result = chain.invoke({"ocr_text": ocr_text})
            
            # The API may occasionally return empty content, we check for it here
            content = result.content.strip()
            if not content:
                raise ValueError("Empty content returned by the API.")
                
            # Parse the JSON string
            parsed_json = json.loads(content)
            
            # Validate via Pydantic schema
            validated_data = ReceiptSchema(**parsed_json)
            return validated_data
            
        except json.JSONDecodeError as e:
            last_error = e
            logger.error(f"Attempt {attempt + 1} JSON Decode Error: {str(e)} | Content: {result.content}")
            print(f"JSON Decode Error on attempt {attempt + 1}. Retrying...")
            
        except ValidationError as e:
            last_error = e
            logger.error(f"Attempt {attempt + 1} Validation Error: {str(e)} | Content: {result.content}")
            print(f"Validation failed on attempt {attempt + 1}. Retrying...")
            
        except Exception as e:
            # Handle empty content or generic API errors
            last_error = e
            logger.error(f"Attempt {attempt + 1} Error: {str(e)}")
            print(f"Error on attempt {attempt + 1}: {e}. Retrying...")
            
    # If all retries fail
    raise ValueError(f"Failed to extract valid JSON after {max_retries} attempts. Last Error: {last_error}")
