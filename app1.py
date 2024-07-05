from flask import Flask, render_template, request, send_file
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
        output_filename = f"output_text_{file.filename}.txt"

        if file.filename.endswith('.pdf'):
            text, image_base64 = extract_text_from_pdf(file)
        else:
            # For image files (e.g., JPG), perform OCR using pytesseract with LSTM and page segmentation
            image = Image.open(BytesIO(file.read()))

            # Resize image to a higher resolution (e.g., 300 DPI)
            image = image.resize((2550, 3300), resample=Image.LANCZOS)

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

            # Resize image to a higher resolution (e.g., 300 DPI)
            img = img.resize((2550, 3300), resample=Image.LANCZOS)

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

# Route to serve the text file for download
@app1.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

# Run the Flask application
if __name__ == '__main__':
    app1.run(debug=True)