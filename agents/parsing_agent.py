import os
from parser.document_parser import parse_sroie_box_file
from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions

class DocumentParsingAgent:
    """
    Agent responsible for converting raw input documents (images or box text files)
    into a structured text string for extraction.
    
    Uses local Docling parser with EasyOCR for zero-API, fully local, robust processing.
    """
    
    def __init__(self):
        # Configure EasyOCR to avoid PyTorch GPU requirements in HF spaces
        ocr_options = EasyOcrOptions(force_full_page_ocr=True, use_gpu=False)
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = ocr_options
        
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.IMAGE, InputFormat.PDF],
            format_options={
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    
    def parse_file(self, file_path: str) -> str:
        """
        Parses a file. Uses Docling EasyOCR for images, and custom parser for .txt box files.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = file_path.lower().split('.')[-1]
        
        if ext == 'txt':
            return parse_sroie_box_file(file_path)
        elif ext in ['jpg', 'jpeg', 'png', 'pdf']:
            print(f"[Docling] Extracting text locally: {file_path}")
            result = self.converter.convert(file_path)
            
            # Export the document to markdown
            return result.document.export_to_markdown()
        else:
            raise NotImplementedError(f"Parsing for extension .{ext} not yet implemented.")
