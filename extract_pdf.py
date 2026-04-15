import pypdf

base_path = r"c:\Users\Lenovo\Downloads\tailadmin-vuejs-1.0.0"
pdf_path = rf"{base_path}\BG Quản lý và ứng dụng cơ sở dữ liệu trong tài chính 2022 .pdf"
output_path = rf"{base_path}\pdf_text.txt"

text = ""
with open(pdf_path, 'rb') as file:
    reader = pypdf.PdfReader(file)
    for i, page in enumerate(reader.pages):
        text += f"\n--- Page {i+1} ---\n"
        text += page.extract_text()

with open(output_path, 'w', encoding='utf-8') as file:
    file.write(text)
print(f"Extracted {len(reader.pages)} pages to pdf_text.txt")
