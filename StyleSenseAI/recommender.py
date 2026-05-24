def generate_three_outfit_recommendations(analysis: dict, gender_focus: str, weather_condition: str) -> list:
    """
    Generate three structured rule-based recommendations.
    Fallback when LLM API fails.
    """
    style = analysis.get("style", "Casual")
    color_names = analysis.get("color_names", ["Neutral"])
    color_str = ", ".join(color_names[:3])
    
    casual_look = {
        "title": "Casual Look",
        "items": "Comfortable cotton t-shirt, relaxed fit denim jeans, white sneakers.",
        "colors": f"Using {color_str} as subtle accents.",
        "occasion": "Everyday wear, casual hangouts.",
        "description": f"A stylish yet comfortable casual look inspired by the {style} vibe and {color_str} palette.",
        "prompt": f"Edit the person's outfit into a stylish casual daily wear look featuring {color_str} tones. Preserve face, pose, body shape, and background. Only change clothing. Realistic fashion photo."
    }
    
    formal_look = {
        "title": "Formal Look",
        "items": "Tailored blazer, crisp button-down shirt, dress trousers, oxfords.",
        "colors": f"Structured look incorporating deep shades of {color_str}.",
        "occasion": "Office, formal meetings, evening events.",
        "description": f"A sophisticated modern formal outfit enhancing the {style} elements.",
        "prompt": f"Edit the person's outfit into a modern formal office outfit featuring {color_str} tones. Preserve face, pose, body shape, and background. Only change clothing. Realistic luxury fashion photo."
    }
    
    streetwear_look = {
        "title": "Streetwear Look",
        "items": "Oversized graphic hoodie, cargo pants, chunky sneakers, bucket hat.",
        "colors": f"Bold utilization of {color_str}.",
        "occasion": "Urban settings, fashion events, casual outings.",
        "description": f"An edgy streetwear ensemble combining the {style} aesthetic with trendy cuts.",
        "prompt": f"Edit the person's outfit into a trendy streetwear urban outfit featuring {color_str} tones. Preserve face, pose, body shape, and background. Only change clothing. Realistic urban fashion photo."
    }
    
    return [casual_look, formal_look, streetwear_look]
