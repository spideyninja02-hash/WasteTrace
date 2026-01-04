# test.py
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import imagehash
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import re
import json

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

TEMP_IMG_PATH = Path("temp.jpg")
known_hashes = set()

def classify_and_count(image_path):
    incoming_hash = imagehash.average_hash(Image.open(image_path))
    if incoming_hash in known_hashes:
        return {"error": "REJECT: duplicate or already exists"}
    known_hashes.add(incoming_hash)

    prompt = """
     You are a trash classifier and counter.
     Analyze the image and only count the items that appear to be within a close range, approximately 5 feet from the camera. Ignore any objects that seem to be far away in the background.
     For each object category (cardboard, glass, metal, paper, plastic, trash) in the image, count how many of these nearby items are present.
     Return only a structured response in the format:
     cardboard: <number>
     glass: <number>
     metal: <number>
     paper: <number>
     plastic: <number>
     trash: <number>
     If there is no object of a category, return 0 for that category.
     """


    with open(image_path, "rb") as f:
        img_bytes = f.read()

    vision_model = genai.GenerativeModel("gemini-2.5-flash")
    response = vision_model.generate_content([
        {"mime_type": "image/jpeg", "data": img_bytes},
        {"text": prompt}
    ])

    text = response.text.strip()
    print(f"[Terminal Log] Raw classification: {text}")

    pattern = r"(cardboard|glass|metal|paper|plastic|trash):\s*(\d+)"
    classification = {cat: 0 for cat in ["cardboard","glass","metal","paper","plastic","trash"]}
    for match in re.findall(pattern, text, re.IGNORECASE):
        classification[match[0].lower()] = int(match[1])

    return classification

# FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/classify-image")
async def classify_image(file: UploadFile):
    temp_path = Path("temp.jpg")
    contents = await file.read()
    temp_path.write_bytes(contents)
    classification = classify_and_count(temp_path)
    return {"classification": classification}

# Terminal test
if __name__ == "__main__":
    sample_image = "sample_waste.jpg"
    if os.path.exists(sample_image):
        print("Classifying image:", sample_image)
        classification = classify_and_count(sample_image)
        print("Classification result:", json.dumps(classification, indent=2))
    else:
        print(f"Image not found: {sample_image}")
