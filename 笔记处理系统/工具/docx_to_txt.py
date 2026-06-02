import os
import glob
import sys
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

def convert_docx_to_txt(docx_path, txt_path):
    try:
        doc = Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.write('\n'.join(full_text))
        return True
    except Exception as e:
        print(f"Error converting {docx_path}: {e}")
        return False

def batch_convert(input_dir, output_extension='_raw.txt'):
    docx_files = glob.glob(os.path.join(input_dir, '*.docx'))
    success_count = 0
    for docx_path in docx_files:
        base_name = os.path.basename(docx_path)
        txt_name = base_name.replace('.docx', '') + output_extension
        txt_path = os.path.join(input_dir, txt_name)
        if convert_docx_to_txt(docx_path, txt_path):
            print(f"[OK] {base_name} -> {txt_name}")
            success_count += 1
        else:
            print(f"[FAIL] {base_name}")
    return success_count, len(docx_files)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
        ext = sys.argv[2] if len(sys.argv) > 2 else '_raw.txt'
        success, total = batch_convert(input_dir, ext)
        print(f"\nTotal: {success}/{total} files converted successfully")
    else:
        print("Usage: python docx_to_txt.py <input_directory> [output_extension]")