# Extract Headers from report and count instances

import sys
import os
from docx import Document
 
def extract_heading_counts(docx_path, output_txt=None):
    if not os.path.isfile(docx_path):
        print(f"[!] File not found: {docx_path}")
        return
 
    if not output_txt:
        base = os.path.splitext(os.path.basename(docx_path))[0]
        output_txt = f"{base}_heading3_counts.txt"
 
    document = Document(docx_path)
    lines = []
 
    paragraphs = document.paragraphs
    i = 0
    total = len(paragraphs)
 
    while i < total:
        para = paragraphs[i]
        style = para.style.name
        text = para.text.strip()
 
        if style == 'Heading 3' and text:
            h3_text = text
            h4_count = 0
            i += 1
 
            # Count Heading 4s that follow this Heading 3
            while i < total:
                next_para = paragraphs[i]
                next_style = next_para.style.name
                next_text = next_para.text.strip()
 
                if next_style == 'Heading 4' and next_text:
                    h4_count += 1
                    i += 1
                elif next_style == 'Heading 3':
                    break
                else:
                    i += 1
 
            lines.append(f"{h3_text} ({h4_count} subheadings)")
        else:
            i += 1
 
    with open(output_txt, 'w', encoding='utf-8') as f:
        for line in lines:  # ← fixed colon here
            f.write(line + '\n')
 
    print(f"[+] Extracted {len(lines)} Heading 3 entries to '{output_txt}'")
 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_headings.py <input.docx> [output.txt]")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else None
        extract_heading_counts(input_file, output_file)
