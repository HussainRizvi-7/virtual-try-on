import os
import requests
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
import replicate

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

if REPLICATE_API_TOKEN:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

REPLICATE_MODEL = os.getenv("REPLICATE_MODEL", "black-forest-labs/flux-schnell")


def check_replicate_status() -> dict:
    return {
        "found": bool(REPLICATE_API_TOKEN),
        "model": REPLICATE_MODEL,
        "error": None if REPLICATE_API_TOKEN else "REPLICATE_API_TOKEN missing in .env"
    }


def run_virtual_tryon(input_image_path: str, outfit_prompt: str) -> Image.Image | None:
    if not check_replicate_status()["found"]:
        return None

    try:
        output = replicate.run(
            REPLICATE_MODEL,
            input={
                "prompt": outfit_prompt
            }
        )

        image_url = None

        if isinstance(output, list) and len(output) > 0:
            image_url = str(output[0])
        elif isinstance(output, str):
            image_url = output
        elif isinstance(output, dict):
            image_url = output.get("image") or output.get("output")

        if not image_url:
            print("Failed to parse image URL from Replicate output:", output)
            return None

        if isinstance(image_url, list) and len(image_url) > 0:
            image_url = str(image_url[0])

        response = requests.get(str(image_url), timeout=30)

        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGB")

        print(f"Failed to download image from Replicate: {response.status_code}")
        return None

    except Exception as e:
        print(f"Replicate API Error: {e}")
        return None


def generate_three_virtual_tryons(input_image_path: str, outfit_ideas: list) -> list:
    results = []

    for idea in outfit_ideas:
        prompt = idea.get("prompt", "Generate a realistic fashion outfit")
        img = run_virtual_tryon(input_image_path, prompt)
        results.append(img)

    return results