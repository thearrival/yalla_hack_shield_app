import PyPDF2

def extract_text_from_pdf(pdf_path, txt_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    with open(txt_path, 'w', encoding='utf-8') as file:
        file.write(text)

pdf_file = '/home/ubuntu/Yalla-Hack_Automated_Profit_Generation_System_Combined.pdf'
txt_file = '/home/ubuntu/yalla_hack_combined_text.txt'
extract_text_from_pdf(pdf_file, txt_file)


