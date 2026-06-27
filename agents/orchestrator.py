import logging
from dataclasses import dataclass
from pydantic import ValidationError

from agents.parsing_agent import DocumentParsingAgent
from agents.extraction_agent import EntityExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.quality_agent import DataQualityAgent
from agents.storage_agent import StorageAgent
from models.schema import ReceiptSchema

@dataclass
class OrchestratorState:
    file_path: str
    filename: str
    raw_text: str = ""
    raw_json: dict = None
    validated_data: ReceiptSchema = None
    quality_report: dict = None
    retry_count: int = 0
    max_retries: int = 3
    is_success: bool = False
    error_message: str = ""

class OrchestratorAgent:
    """
    Lightweight state machine that orchestrates the flow of data through the agent pipeline.
    """
    def __init__(self):
        self.parsing_agent = DocumentParsingAgent()
        self.extraction_agent = EntityExtractionAgent()
        self.validation_agent = ValidationAgent()
        self.quality_agent = DataQualityAgent()
        self.storage_agent = StorageAgent()
        
        self.logger = logging.getLogger("orchestrator")
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            self.logger.addHandler(logging.StreamHandler())
            
    def process_file(self, file_path: str, filename: str) -> OrchestratorState:
        state = OrchestratorState(file_path=file_path, filename=filename)
        
        try:
            # 1. Parsing
            state.raw_text = self.parsing_agent.parse_file(state.file_path)
            
            # 2 & 3. Extraction & Validation (with Retry Loop)
            last_error = ""
            while state.retry_count < state.max_retries:
                try:
                    # Extraction
                    state.raw_json = self.extraction_agent.extract(state.raw_text, error_feedback=last_error)
                    
                    # Validation
                    state.validated_data = self.validation_agent.validate(state.raw_json)
                    break # Success, exit retry loop
                    
                except (ValidationError, ValueError) as e:
                    state.retry_count += 1
                    last_error = str(e)
                    self.logger.warning(f"Validation failed for {filename} (Attempt {state.retry_count}/{state.max_retries}): {e}")
                    
            if not state.validated_data:
                raise Exception(f"Failed to extract valid data after {state.max_retries} retries. Last error: {last_error}")
                
            # 4. Data Quality
            state.quality_report = self.quality_agent.analyze(state.validated_data)
            
            # 5. Storage
            self.storage_agent.store(state.filename, state.raw_text, state.validated_data)
            
            state.is_success = True
            
        except Exception as e:
            state.is_success = False
            state.error_message = str(e)
            self.logger.error(f"Pipeline failed for {filename}: {e}")
            
        return state
