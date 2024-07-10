from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF

def resize_and_save_as_pdf(file, pr_pix=0, pr_dpi=300):
    # Open the PDF file using PyMuPDF (fitz)
    input_pdf = fitz.open(BytesIO(file.read()))

    # Initialize a PdfWriter object for output
    output_pdf = PdfWriter()

    for page_num in range(len(input_pdf)):
        # Get each page from the input PDF
        page = input_pdf.load_page(page_num)

        # Convert page to image
        pix = page.get_pixmap()

        # Convert image to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Resize image while maintaining aspect ratio
        aspect_ratio = pix.height / pix.width
        new_pix = (pr_pix / 100) * pix.width
        new_width = int(pix.width - new_pix)
        new_height = int(aspect_ratio * new_width)
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Convert resized image to PNG bytes
        img_bytes = BytesIO()
        img_resized.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        # Create a new PDF writer object for each page
        output_page = PdfWriter()
        output_page.add_page(page)

        # Add the resized image as a new page in the output PDF
        output_page.add_page(img_bytes)

        # Append the output page to the output PDF
        output_pdf.append_pages_from_writer(output_page)

    # Save the output PDF to a BytesIO stream
    output_pdf_stream = BytesIO()
    output_pdf.write(output_pdf_stream)

    return output_pdf_stream

# Example usage
input_pdf_bytes = open(r"C:\Users\bmbar\Downloads\Free_Test_Data_10.5MB_PDF.pdf", 'rb').read()  # Read PDF file bytes
file_stream = BytesIO(input_pdf_bytes)  # Create BytesIO stream

# Resize and convert to PDF
pdf_output = resize_and_save_as_pdf(file_stream, pr_pix=50, pr_dpi=150)

# Save the PDF output to a file
with open("out.pdf", "wb") as f:
    f.write(pdf_output.getbuffer())

print('PDF saved successfully')
