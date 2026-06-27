import os
from parser.document_parser import parse_sroie_box_file
from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions

class DocumentParsingAgent:
    """
    Agent responsible for converting raw input documents (images or box text files)
    into a structured text string for extraction.
    """
    
    def __init__(self):
        # Configure EasyOCR to avoid the torch.PP-OCRv6.det.small error in HuggingFace Spaces
        ocr_options = EasyOcrOptions(do_ocr=True)
        pipeline_options = PdfPipelineOptions(ocr_options=ocr_options)
        
        # Initialize Docling converter with EasyOCR
        self.converter = DocumentConverter(
            format_options={
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    
    def parse_file(self, file_path: str) -> str:
        """
        Parses a file. Uses Docling for .jpg/.png images, and our custom parser for .txt box files.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = file_path.lower().split('.')[-1]
        
        if ext == 'txt':
            return parse_sroie_box_file(file_path)
        elif ext in ['jpg', 'jpeg', 'png', 'pdf']:
            print(f"[Docling] Converting image: {file_path}")
            result = self.converter.convert(file_path)
            return result.document.export_to_markdown()
        else:
            raise NotImplementedError(f"Parsing for extension .{ext} not yet implemented.")
