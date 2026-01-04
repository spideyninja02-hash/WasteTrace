from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tickets import router as tickets_router

import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import imagehash
import re

# =========================
# Gemini setup
# =========================
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

TEMP_IMG_PATH = Path("temp.jpg")
known_hashes = set()

# =========================
# Image classification logic
# =========================
def classify_and_count(image_path: Path) -> dict[str, int]:
    """
    Always returns numeric classification dictionary.
    Never returns strings or error objects.
    """

    incoming_hash = imagehash.average_hash(Image.open(image_path))

    # 🚫 Duplicate image → treat as no waste
    if incoming_hash in known_hashes:
        return {
            "cardboard": 0,
            "glass": 0,
            "metal": 0,
            "paper": 0,
            "plastic": 0,
            "trash": 0,
        }

    known_hashes.add(incoming_hash)

    prompt = """
    You are a trash classifier and counter.
    Count only nearby waste items clearly visible.
    Return EXACTLY in this format:

    cardboard: <number>
    glass: <number>
    metal: <number>
    paper: <number>
    plastic: <number>
    trash: <number>
    """

    img_bytes = image_path.read_bytes()

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": img_bytes},
        {"text": prompt}
    ])

    text = response.text.strip()
    print("[Gemini Raw Output]", text)

    pattern = r"(cardboard|glass|metal|paper|plastic|trash):\s*(\d+)"
    classification = {
        "cardboard": 0,
        "glass": 0,
        "metal": 0,
        "paper": 0,
        "plastic": 0,
        "trash": 0,
    }

    for cat, count in re.findall(pattern, text, re.IGNORECASE):
        classification[cat.lower()] = int(count)

    return classification


# =========================
# FastAPI app
# =========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Keep tickets API
app.include_router(tickets_router)

# =========================
# 🔥 CLASSIFY IMAGE ENDPOINT
# =========================
@app.post("/classify-image")
async def classify_image(file: UploadFile = File(...)):
    contents = await file.read()
    TEMP_IMG_PATH.write_bytes(contents)

    classification = classify_and_count(TEMP_IMG_PATH)

    # ✅ Safe numeric sum
    total_items = sum(classification.values())

    if total_items == 0:
        return {
            "detected": False,
            "classification": classification,
            "message": "No waste detected"
        }

    dominant_category = max(classification, key=classification.get)

    return {
        "detected": True,
        "category": dominant_category,
        "counts": classification,
        "message": f"{dominant_category.capitalize()} waste detected"
    }
