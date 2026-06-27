from pydantic import ValidationError
from models.schema import ReceiptSchema
import logging
import os

class ValidationAgent:
    """
    Agent responsible for enforcing Pydantic schemas. 
    It intercepts validation errors and passes them back for the Orchestrator to handle retries.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("validation_agent")
        self.logger.setLevel(logging.ERROR)
        log_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'validation_errors.log')
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        if not self.logger.hasHandlers():
            self.logger.addHandler(file_handler)
            
    def validate(self, raw_dict: dict) -> ReceiptSchema:
        """
        Validates a raw dictionary against the ReceiptSchema.
        Raises a ValidationError if the structure is incorrect.
        """
        try:
            validated_data = ReceiptSchema(**raw_dict)
            return validated_data
        except ValidationError as e:
            self.logger.error(f"Validation Error: {str(e)} | Input Dict: {raw_dict}")
            raise e
