from flask import Flask, render_template, request, send_file, after_this_request
import tempfile
import pytesseract
from PIL import Image
import fitz
import os
import io
from io import BytesIO
import base64
from PyPDF2 import PdfReader, PdfWriter

# Configure Tesseract OCR executable path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
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

            aspect_ratio = image.height / image.width
            new_width = 2550
            new_height = aspect_ratio * new_width

            # Resize image to a higher resolution (e.g., 300 DPI)
            image = image.resize((int(new_width), int(new_height)), resample=Image.LANCZOS)

            # Preprocess image (example: convert to grayscale)
            image = image.convert('L')

            # Perform OCR using pytesseract with LSTM and page segmentation
            text = pytesseract.image_to_string(image, config='--oem 1 --psm 1')

        # Return rendered template with text content
        return render_template('result.html', text=text, image_base64=image_base64)


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
            text += f"Page {page_num + 1}:\n"

            # Convert the page to an image (adjust resolution if needed)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            aspect_ratio = pix.height / pix.width
            new_width = 2550
            new_height = aspect_ratio * new_width

            # Resize image to a higher resolution (e.g., 300 DPI)
            img = img.resize((int(new_width), int(new_height)), resample=Image.LANCZOS)

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

@app1.route('/resize_image', methods=['GET','POST'])
def man():
    if request.method == 'POST':
        return resize_image()
    return render_template('resize_image.html')

def resize_image():
    file = request.files['file']
    pr_dpi = int(request.form['dpi'])  # Get selected DPI as percentage
    pr_pix=int(request.form['pix'])

    if file:
            image = Image.open(BytesIO(file.read()))

            # Retrieve current DPI
            current_dpi = image.info.get('dpi', (300, 300))  # Default to 300 DPI if no DPI info is available

            # Convert DPI tuple to a list
            dpi_list = list(current_dpi)

            # Halve the DPI value
            new_val = (pr_dpi / 100) * dpi_list[0]
            new_dpi = dpi_list[0] - new_val

            # Set new DPI (dots per inch) metadata
            image.info['dpi'] = (new_dpi, new_dpi)

            # Resize the image while maintaining aspect ratio
            aspect_ratio = image.height / image.width
            new_pix = (pr_pix / 100) * image.width
            new_width = int(image.width - new_pix)
            new_height = int(aspect_ratio * new_width)

            img_resized = image.resize((new_width, new_height), Image.LANCZOS)

            # Check and convert image mode if necessary
            print(f"Image mode before conversion: {img_resized.mode}")
            if img_resized.mode in ('RGBA', 'P'):
                img_resized = img_resized.convert('RGB')
            print(f"Image mode after conversion: {img_resized.mode}")

            img_io = BytesIO()
            img_resized.save(img_io, format='JPEG', dpi=(new_dpi, new_dpi))
            img_io.seek(0)

            return send_file(img_io, as_attachment=True, download_name=f"resized_{file.filename}")

@app1.route('/resize_pdf', methods=['GET','POST'])
def lan():
    if request.method == 'POST':
            # Check if 'action' parameter is set to 'compress' or 'resize'
            action = request.form.get('action')
            if action == 'compress':
                return compress_pdf()
            elif action == 'resize':
                return resize_pdf()
    return render_template('resize_pdf.html')
        

def resize_pdf():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_input, \
                 tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_output:
                temp_input.write(file.read())
                temp_input.seek(0)
                
                # Compress the PDF
                pdf_document = fitz.open(temp_input.name)
                pdf_writer = fitz.open()

                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img = img.convert("RGB")
                    img_byte_array = io.BytesIO()
                    img.save(img_byte_array, format='JPEG', quality=100)
                    img_byte_array.seek(0)
                    pdf_writer.new_page(width=img.width, height=img.height)
                    pdf_writer[-1].insert_image((0, 0, img.width, img.height), stream=img_byte_array.read())
                    img_byte_array.close()

                 # Save the compressed PDF to the output file
                output_filename = f"resized_{file.filename}"
                output_path = os.path.join(tempfile.gettempdir(), output_filename)
                pdf_writer.save(output_path)
                pdf_writer.close()

                # Clean up resources
                pdf_document.close()
                return send_file(output_path, as_attachment=True, download_name=output_filename)
            
# Function to compress uploaded PDF
def compress_pdf():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_input, \
                tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_output:
                temp_input.write(file.read())
                temp_input.seek(0)

                # Open the input PDF file
                pdf_reader = PdfReader(temp_input.name)
                pdf_writer = PdfWriter()

                # Compress each page's content streams
                for page in pdf_reader.pages:
                    page.compress_content_streams()
                    pdf_writer.add_page(page)

                # Save the compressed PDF to the output file
                output_filename = f"compressed_{file.filename}"
                temp_output_path = os.path.join(tempfile.gettempdir(), output_filename)
                with open(temp_output_path, 'wb') as f:
                    pdf_writer.write(f)

                # Return the compressed PDF for download
                return send_file(temp_output_path, as_attachment=True, download_name=output_filename)


# Run the Flask application
if __name__ == '__main__':
    app1.run(debug=True, host='0.0.0.0')