import pytesseract
from pytesseract import Output
from PIL import Image
from transformers import LayoutLMv2Processor, LayoutLMv2ForTokenClassification

# Step 1: Perform OCR using Tesseract
def perform_ocr(image_path):
    image = Image.open(image_path)
    ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
    return ocr_data

# Step 2: Prepare data for LayoutLMv2
processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased")

def prepare_layoutlmv2_data(ocr_data, image_path):
    words = ocr_data['text']
    boxes = []
    for i in range(len(words)):
        if words[i].strip():
            (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i])
            boxes.append([x, y, x + w, y + h])
    
    # Normalize bounding boxes
    image = Image.open(image_path)
    width, height = image.size
    boxes = [[int(1000 * (box[0] / width)), int(1000 * (box[1] / height)), int(1000 * (box[2] / width)), int(1000 * (box[3] / height))] for box in boxes]

    # Create features for LayoutLMv2
    encoded_inputs = processor(image, words, boxes=boxes, return_tensors="pt", truncation=True, padding="max_length", max_length=512)
    return encoded_inputs

# Step 3: Perform inference using LayoutLMv2
model = LayoutLMv2ForTokenClassification.from_pretrained("microsoft/layoutlmv2-base-uncased")

def infer_layoutlmv2(encoded_inputs):
    outputs = model(**encoded_inputs)
    predictions = outputs.logits.argmax(-1).squeeze().tolist()
    return predictions

# Step 4: Map predictions to words
label_map = {i: label for i, label in enumerate(processor.tokenizer.get_vocab().keys())}

def map_predictions_to_words(predictions, words):
    token_predictions = [label_map[pred] for pred in predictions]
    return list(zip(words, token_predictions))

# Example usage
image_path = 'D:\GIT\OCR-of-documents\test images\1.png'
ocr_data = perform_ocr(image_path)
encoded_inputs = prepare_layoutlmv2_data(ocr_data, image_path)
predictions = infer_layoutlmv2(encoded_inputs)
word_predictions = map_predictions_to_words(predictions, ocr_data['text'])

for word, prediction in word_predictions:
    print(f"{word}: {prediction}")
hi this is bibek