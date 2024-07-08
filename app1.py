from flask import Flask, render_template, request, send_file, after_this_request
import tempfile
import pytesseract
from PIL import Image
import fitz
from io import BytesIO
import base64


# Configure Tesseract OCR executable path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update with your Tesseract path

# Initialize Flask application
app1 = Flask(__name__)

# Route to serve the HTML form for uploading images or PDFs
@app1.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return handle_file_upload()
    return render_template('index.html')

# Route to handle file upload and perform OCR
def handle_file_upload():
    file = request.files['file']

    if file:
        # Generate unique output filename
        output_filename = f"output_{file.filename}.txt"

        if file.filename.endswith('.pdf'):
            text, image_base64 = extract_text_from_pdf(file)
        else:
            # For image files (e.g., JPG), perform OCR using pytesseract with LSTM and page segmentation
            image = Image.open(BytesIO(file.read()))

            abs=image.height/image.width
            new_width=2550
            new_height=abs*new_width

            # Resize image to a higher resolution (e.g., 300 DPI)
            image = image.resize((int(new_width), int(new_height)), resample=Image.LANCZOS)

            # Preprocess image (example: convert to grayscale)
            image = image.convert('L')

            # Perform OCR using pytesseract with LSTM and page segmentation
            text = pytesseract.image_to_string(image, config='--oem 1 --psm 1')

            # Encode image as base64 string
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Save extracted text to a text file
        with open(output_filename, 'w', encoding='utf-8') as txt_file:
            txt_file.write(text)

        # Return rendered template with text content
        return render_template('result.html', text=text, image_base64=image_base64, download_link=output_filename)

# Function to extract text from a PDF using PyMuPDF (fitz) and perform OCR
def extract_text_from_pdf(pdf_file):
    text = ""
    image_base64 = None  # Initialize image_base64

    with tempfile.NamedTemporaryFile(delete=False) as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_pdf.seek(0)
        pdf_document = fitz.open(temp_pdf.name, filetype="pdf")

        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text+=f"Page {page_num + 1}:\n"

            # Convert the page to an image (adjust resolution if needed)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            abs=pix.height/pix.width
            new_width=2550
            new_height=abs*new_width

            # Resize image to a higher resolution (e.g., 300 DPI)
            img = img.resize((int(new_width),int(new_height)), resample=Image.LANCZOS)

            # Preprocess image (example: convert to grayscale)
            img = img.convert('L')

            # Perform OCR using pytesseract with LSTM and page segmentation
            page_text = pytesseract.image_to_string(img, config='--oem 1 --psm 6')
            text += page_text + "\n"

            # If you want to display the first page's image (for example), encode it as base64
            if page_num == 0:
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return text, image_base64

@app1.route('/resize_pdf',methods=['Get','Post'])
def main():
    if request.method == 'POST':
        return resize_pdf()
    return render_template('resize_pdf.html')
def resize_pdf():
    file = request.files['file']
    if file.filename.endswith('.pdf'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_pdf:
                temp_pdf.write(file.read())
                temp_pdf.seek(0)
                pdf_document = fitz.open(temp_pdf.name, filetype="pdf")

                resized_pages=[]

                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)

                    # Convert the page to an image (adjust resolution if needed)
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    abs=pix.height/pix.width
                    new_width=595
                    new_height=abs*new_width

                    img = img.resize((int(new_width),int(new_height)), resample=Image.LANCZOS)

                    resized_pages.append(img)

                    # Create a temporary file to save the output PDF
                with tempfile.NamedTemporaryFile(delete=False) as temp_pdf:
                    # Save resized images as pages in the output PDF
                    with fitz.open() as output_pdf_document:
                        for img_resized in resized_pages:
                            img_bytes = img_resized.tobytes()
                            img_memory = fitz.open(stream=img_bytes, filetype="jpg")
                            output_pdf_document.new_page(width=img_memory[0].rect.width, height=img_memory[0].rect.height)
                            output_pdf_document[-1].show_pdf_page(output_pdf_document[-1].rect, img_memory, 0)
                            img_memory.close()
                        
                        # Save the output PDF to the temporary file
                        output_pdf_document.save(temp_pdf.name)

                # Return the resized PDF file to the client
                return send_file(temp_pdf.name, as_attachment=True, download_name=f"resized_{file.filename}")



# Route to serve the text file for download
@app1.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

# Run the Flask application
if __name__ == '__main__':
    app1.run(debug=True, host='0.0.0.0')