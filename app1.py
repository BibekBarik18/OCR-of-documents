from flask import Flask, render_template, request, send_file, after_this_request
import tempfile
import pytesseract
from PIL import Image
import fitz
from io import BytesIO
import base64

# Configure Tesseract OCR executable path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\User\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
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

@app1.route('/resize_pdf', methods=['GET','POST'])
def main():
    if request.method == 'POST':
        return resize_pdf()
    return render_template('resize_pdf.html')

def resize_pdf():
    file = request.files['file']
    pr_dpi = int(request.form['dpi'])  # Get selected DPI as percentage
    pr_pix=int(request.form['pix'])

    if file:


        if file.filename.endswith('.pdf'):

            try:
                # Create a temporary file for the output PDF
                temp_output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                print(f"Temporary output PDF created: {temp_output_pdf.name}")

                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                    temp_pdf.write(file.read())
                    temp_pdf.seek(0)
                    print(f"Temporary input PDF created: {temp_pdf.name}")

                    # Open the input PDF file
                    try:
                        pdf_document = fitz.open(temp_pdf.name)
                        print(f"PDF document opened: {temp_pdf.name}")
                    except Exception as e:
                        print(f"Error opening PDF: {e}")
                        raise ValueError("The provided file is not a valid PDF.")

                    # Create a new PDF for the output
                    output_pdf = fitz.open()
                    print("Output PDF created")

                    for page_num in range(len(pdf_document)):
                        try:
                            page = pdf_document.load_page(page_num)
                            print(f"Page {page_num} loaded")

                            # Convert the page to an image (adjust resolution if needed)
                            pix = page.get_pixmap()
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            print(f"Page {page_num} converted to image")

                            # Retrieve current DPI
                            current_dpi = (300, 300)  # Assuming a default DPI of 300, as Pixmap doesn't carry DPI info

                            # Convert DPI tuple to a list
                            dpi_list = list(current_dpi)

                            # Adjust the DPI value
                            new_val = (pr_dpi / 100) * dpi_list[0]
                            new_dpi = dpi_list[0] - new_val

                            # Resize the image while maintaining aspect ratio
                            aspect_ratio = img.height / img.width
                            new_pix = (pr_pix / 100) * img.width
                            new_width = int(img.width - new_pix)
                            new_height = int(aspect_ratio * new_width)

                            img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                            print(f"Image resized for page {page_num}")

                            # Check and convert image mode if necessary
                            if img_resized.mode in ('RGBA', 'P'):
                                img_resized = img_resized.convert('RGB')
                            print(f"Image mode checked for page {page_num}")

                            # Convert image to bytes and create a PDF page from it
                            img_bytes = BytesIO()
                            img_resized.save(img_bytes, format='JPEG', dpi=(new_dpi, new_dpi))
                            img_bytes.seek(0)
                            print(f"Image saved to bytes for page {page_num}")

                            img_pdf = fitz.open(stream=img_bytes.read(), filetype='jpeg')
                            page_rect = fitz.Rect(0, 0, new_width, new_height)
                            output_pdf.new_page(width=page_rect.width, height=page_rect.height)
                            output_pdf[-1].show_pdf_page(page_rect, img_pdf, 0)
                            img_pdf.close()
                            print(f"Image added to output PDF for page {page_num}")

                        except Exception as e:
                            print(f"Error processing page {page_num}: {e}")
                            raise ValueError(f"An error occurred while processing page {page_num} of the PDF file.")

                    # Save the output PDF to the temporary file
                    output_pdf.save(temp_output_pdf.name)
                    output_pdf.close()
                    pdf_document.close()
                    print("Output PDF saved and documents closed")

                return send_file(temp_output_pdf.name, as_attachment=True, download_name=f"resized_{file.filename}")
            except Exception as e:
                print(f"An error occurred: {e}")
                raise ValueError("An error occurred while processing the PDF file.")

        else:
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


# Route to serve the text file for download
@app1.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)


# Run the Flask application
if __name__ == '__main__':
    app1.run(debug=True, host='0.0.0.0')