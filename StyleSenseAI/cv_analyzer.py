import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Convert PIL image to OpenCV format (RGB) and resize for faster processing."""
    # Convert PIL Image to numpy array
    img_np = np.array(image)
    if len(img_np.shape) == 2:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_GRAY2RGB)
    elif img_np.shape[2] == 4:
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
    
    # Resize for faster KMeans processing
    img_resized = cv2.resize(img_np, (200, 200), interpolation=cv2.INTER_AREA)
    return img_resized

def rgb_to_color_name(rgb: list) -> str:
    """Map an RGB value to a human-readable color name using distance."""
    r, g, b = rgb
    colors = {
        "Black": (0, 0, 0), "White": (255, 255, 255), "Red": (255, 0, 0),
        "Green": (0, 255, 0), "Blue": (0, 0, 255), "Yellow": (255, 255, 0),
        "Cyan": (0, 255, 255), "Magenta": (255, 0, 255), "Gray": (128, 128, 128),
        "Maroon": (128, 0, 0), "Olive": (128, 128, 0), "Green": (0, 128, 0),
        "Purple": (128, 0, 128), "Teal": (0, 128, 128), "Navy": (0, 0, 128),
        "Pink": (255, 192, 203), "Brown": (165, 42, 42), "Orange": (255, 165, 0),
        "Gold": (255, 215, 0), "Beige": (245, 245, 220), "Khaki": (240, 230, 140)
    }
    
    min_dist = float('inf')
    closest_name = "Unknown"
    
    for name, (cr, cg, cb) in colors.items():
        dist = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
        if dist < min_dist:
            min_dist = dist
            closest_name = name
            
    return closest_name

def extract_dominant_colors(image_np: np.ndarray, k: int = 5) -> list:
    """Extract dominant colors using KMeans clustering."""
    # Flatten the image array to a 2D array of pixels
    pixels = image_np.reshape(-1, 3)
    
    # Use KMeans to find dominant colors
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Get the colors and their proportions
    colors = kmeans.cluster_centers_
    labels = kmeans.labels_
    
    counts = np.bincount(labels)
    total = len(pixels)
    
    dominant_colors = []
    for i in range(k):
        proportion = counts[i] / total
        rgb = [int(x) for x in colors[i]]
        hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        name = rgb_to_color_name(rgb)
        
        dominant_colors.append({
            "rgb": rgb,
            "hex": hex_color,
            "name": name,
            "proportion": float(proportion)
        })
    
    # Sort by proportion descending
    dominant_colors.sort(key=lambda x: x["proportion"], reverse=True)
    return dominant_colors

def classify_outfit_style(colors: list, image_np: np.ndarray = None) -> tuple:
    """Classify the outfit style based on color heuristics and brightness."""
    # Heuristics based on color palette
    color_names = [c["name"] for c in colors]
    
    has_black = "Black" in color_names
    has_white = "White" in color_names
    has_navy = "Navy" in color_names
    has_gray = "Gray" in color_names
    has_bright = any(c in color_names for c in ["Red", "Yellow", "Orange", "Pink", "Cyan", "Magenta"])
    has_earth = any(c in color_names for c in ["Brown", "Olive", "Khaki", "Beige", "Green"])
    
    style = "Casual"
    confidence = 65
    
    if has_black and (has_white or has_gray or has_navy) and not has_bright:
        style = "Formal"
        confidence = 85
    elif has_earth and not has_bright:
        style = "Smart Casual"
        confidence = 75
    elif has_bright and has_black:
        style = "Streetwear"
        confidence = 80
    elif has_bright and not has_black:
        style = "Summer/Vibrant"
        confidence = 70
        
    return style, confidence

def calculate_fashion_score(colors: list, style: str) -> int:
    """Calculate a dummy fashion score based on color coherence."""
    unique_colors = len(set([c["name"] for c in colors]))
    
    # Basic fashion heuristic: 2-3 dominant colors is usually cohesive
    base_score = 70
    if 2 <= unique_colors <= 3:
        base_score += 20
    elif unique_colors == 1:
        base_score += 15
    else:
        base_score += 5
        
    # Cap at 98 for realism
    return min(98, base_score)

def suggest_occasion(style: str, colors: list) -> str:
    """Suggest an occasion based on style and colors."""
    if style == "Formal":
        return "Office / Business Meeting / Wedding"
    elif style == "Streetwear":
        return "City Walk / Casual Hangout / Concert"
    elif style == "Smart Casual":
        return "Date Night / Office Casual / Dinner"
    elif style == "Summer/Vibrant":
        return "Beach / Vacation / Outdoor Party"
    else:
        return "Daily Wear / Weekend Outing / Coffee Run"

def analyze_outfit(image: Image.Image) -> dict:
    """Main orchestrator for computer vision analysis."""
    img_np = preprocess_image(image)
    colors = extract_dominant_colors(img_np, k=5)
    style, confidence = classify_outfit_style(colors, img_np)
    fashion_score = calculate_fashion_score(colors, style)
    occasion = suggest_occasion(style, colors)
    
    summary = f"A {style.lower()} outfit featuring {', '.join([c['name'] for c in colors[:3]])} tones."
    
    return {
        "style": style,
        "dominant_colors": colors,
        "color_names": [c["name"] for c in colors],
        "fashion_score": fashion_score,
        "occasion": occasion,
        "confidence": confidence,
        "summary": summary
    }
