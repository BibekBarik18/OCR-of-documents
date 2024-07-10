from PyPDF2 import PdfReader,PdfWriter

reader=PdfReader(r"C:\Users\bmbar\Downloads\Free_Test_Data_10.5MB_PDF.pdf")
writer=PdfWriter()
for page in reader.pages:
    page.compress_content_streams()
    writer.add_page(page)

with open("out.pdf","wb") as f:
    writer.write(f)
print('Compressed successfully')