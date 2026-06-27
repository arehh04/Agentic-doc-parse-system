import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class EntityExtractionAgent:
    """
    Agent responsible for prompting the LLM to extract structured entities 
    from the OCR text. It returns raw JSON output, delegating validation to the ValidationAgent.
    """
    
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is not set in the environment.")
            
        self.llm = ChatOpenAI(
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
            
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Here is the receipt OCR text:\n\n{ocr_text}{feedback}")
        ])
        
        self.chain = self.prompt_template | self.llm
        
    def extract(self, raw_ocr_text: str, error_feedback: str = "") -> dict:
        """
        Executes the extraction prompt.
        Accepts optional `error_feedback` if re-prompting after a validation failure.
        """
        feedback_str = f"\n\nPREVIOUS ERROR TO FIX:\n{error_feedback}" if error_feedback else ""
        
        result = self.chain.invoke({
            "ocr_text": raw_ocr_text, 
            "feedback": feedback_str
        })
        
        content = result.content.strip()
        if not content:
            raise ValueError("Empty content returned by the API.")
            
        parsed_json = json.loads(content)
        return parsed_json
