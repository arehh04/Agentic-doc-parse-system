import os

def parse_sroie_box_file(file_path: str) -> str:
    """
    Reads an SROIE box text file and extracts the OCR text.
    The format of each line is: x1,y1,x2,y2,x3,y3,x4,y4,Text.
    """
    text_lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Split into exactly 9 parts (8 coordinates + the rest as text)
            parts = line.strip().split(',', 8)
            if len(parts) == 9:
                text_lines.append(parts[8])
            elif len(parts) > 0 and parts[0]:
                text_lines.append(parts[-1])
                
    return "\n".join(text_lines)
