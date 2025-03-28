# Pulls Header 3 and 4 and extracts them to a text file.
# Useful for extracting report findings and isntances to Excel

import sys
import os
from docx import Document
 
def extract_headings(docx_path, output_txt=None):
    if not os.path.isfile(docx_path):
        print(f"[!] File not found: {docx_path}")
        return
 
    if not output_txt:
        base = os.path.splitext(os.path.basename(docx_path))[0]
        output_txt = f"{base}_headings.txt"
 
    document = Document(docx_path)
    headings = []
 
    for para in document.paragraphs:
        if para.style.name in ['Heading 3', 'Heading 4']:
            text = para.text.strip()
            if text:
                headings.append(text)
 
    with open(output_txt, 'w', encoding='utf-8') as f:
        for line in headings:
            f.write(line + '\n')
 
    print(f"[+] Extracted {len(headings)} headings to '{output_txt}'")
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_headings.py <input.docx> [output.txt]")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else None
        extract_headings(input_file, output_file)
 
