import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def check_gemini_status() -> dict:
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        return {
            "found": True,
            "model": GEMINI_MODEL,
            "error": None
        }

    return {
        "found": False,
        "model": GEMINI_MODEL,
        "error": "GEMINI_API_KEY missing or invalid in .env"
    }


def _get_model():
    return genai.GenerativeModel(GEMINI_MODEL)


def generate_llm_fashion_advice(
    analysis: dict,
    outfit_ideas: list,
    gender_focus: str,
    weather_condition: str
) -> str:
    if not check_gemini_status()["found"]:
        return _get_fallback_advice(analysis, gender_focus, weather_condition)

    try:
        model = _get_model()

        prompt = f"""
You are a premium AI fashion stylist.

Based on this computer vision outfit analysis, provide concise, stylish, practical fashion advice.

Detected style: {analysis.get("style", "Unknown")}
Dominant colors: {", ".join(analysis.get("color_names", []))}
Fashion score: {analysis.get("fashion_score", "N/A")}/100
Target gender focus: {gender_focus}
Weather condition: {weather_condition}
Outfit ideas: {outfit_ideas}

Write 3 to 4 professional sentences.
Mention color harmony, occasion suitability, and one improvement suggestion.
Do not use markdown headings.
"""

        response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text:
            return response.text.strip()

        return _get_fallback_advice(analysis, gender_focus, weather_condition)

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return _get_fallback_advice(analysis, gender_focus, weather_condition)


def answer_fashion_chat(user_question: str, analysis: dict, outfit_ideas: list) -> str:
    if not check_gemini_status()["found"]:
        return (
            "Gemini is currently running in fallback mode because the API key is missing. "
            "Based on your outfit, focus on clean color matching, comfortable fit, and accessories "
            "that support the detected style."
        )

    try:
        model = _get_model()

        prompt = f"""
You are a premium AI fashion stylist.

The user uploaded an outfit with this computer vision analysis:

Style: {analysis.get("style", "Unknown")}
Dominant colors: {", ".join(analysis.get("color_names", []))}
Fashion score: {analysis.get("fashion_score", "N/A")}/100

Available outfit ideas:
{outfit_ideas}

User question:
{user_question}

Answer in maximum 4 sentences.
Make the answer practical, stylish, and easy to understand.
"""

        response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text:
            return response.text.strip()

        return (
            "I could not generate a Gemini response right now, but your outfit can be improved "
            "by balancing colors, fit, and occasion."
        )

    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        return "Gemini could not respond right now. Please check your API key, model name, or internet connection."


def _get_fallback_advice(analysis: dict, gender_focus: str, weather_condition: str) -> str:
    colors = ", ".join(analysis.get("color_names", [])) or "neutral"
    style = analysis.get("style", "Casual")

    advice = f"Your outfit has a clear {style} aesthetic with {colors} tones. "

    if weather_condition in ["Cold", "Winter/Cold"]:
        advice += "For colder weather, add layering such as a structured jacket, coat, or knitwear. "
    elif weather_condition in ["Hot", "Summer/Warm"]:
        advice += "For warm weather, use breathable fabrics such as cotton or linen while keeping the outfit balanced. "
    elif weather_condition in ["Rainy"]:
        advice += "For rainy weather, add practical outerwear and darker footwear to keep the outfit functional. "

    advice += (
        "To improve the look, match footwear and accessories with the dominant color palette "
        "while keeping the overall style consistent."
    )

    return advice