# StyleSense AI – Intelligent Fashion Assistant

StyleSense AI is a premium, cloud-powered Computer Vision and Generative AI application built for fashion analysis and virtual try-on. It combines traditional computer vision techniques with advanced LLMs and cloud-based image generation to provide users with a complete AI fashion stylist experience.

## Final Scope
This project represents the final architecture for a university-level computer vision and AI demonstration. It operates entirely via lightweight cloud APIs, eliminating the need for expensive local GPU hardware or massive multi-gigabyte library installations.

### Features
1. **OpenCV-based Image Analysis**: Extracts dominant color palettes using KMeans clustering and rule-based heuristics.
2. **Replicate API Virtual Try-On**: Generates three unique outfit variations (Casual, Formal, Streetwear) directly in the cloud.
3. **Gemini AI Fashion Chatbot**: Provides an interactive chat interface and generates professional stylist feedback based on the CV analysis.
4. **Resilient Fallback Mode**: If any API key is missing or an endpoint fails (e.g., Replicate free credits expire), the app gracefully degrades to beautiful structured fallback recommendations without crashing.
5. **Premium UI/UX**: Designed with a dark luxury glassmorphism theme, gold/purple accents, and equal-height layout cards.

## Computer Vision Techniques Used
- **KMeans Clustering (`scikit-learn`)**: Identifies dominant `k=5` color centroids from user images.
- **Color Mapping**: Uses mathematical euclidean distance to map extracted RGB values to human-readable color names.
- **Rule-Based Style Inference**: Analyzes color contrast and vibrancy to classify the user's outfit into categories like "Formal", "Streetwear", or "Casual", calculating a pseudo fashion score based on color coherence.

## Architecture Flow
```text
Upload Image -> OpenCV Analysis -> Replicate Try-On -> Gemini Stylist
```

## Installation Steps
1. **Clone the repository.**
2. **Install requirements:**
   ```powershell
   python -m pip install -r requirements.txt
   ```
   *Note: This project does **not** require a GPU or Conda. All massive ML frameworks (Torch, Diffusers, Transformers) have been intentionally removed.*

3. **Configure Environment Variables:**
   Rename `.env.example` to `.env` and fill in your API keys:
   ```env
   REPLICATE_API_TOKEN=your_replicate_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   * **Replicate Token**: Get it from [replicate.com](https://replicate.com). **Note:** Replicate may require a credit card after a few free runs. If your token expires or the free tier is exhausted, the app handles the failure cleanly.
   * **Gemini Key**: Get it from [Google AI Studio](https://aistudio.google.com).

4. **Run the Application:**
   ```powershell
   python -m streamlit run app.py
   ```

## Troubleshooting
- **API generation unavailable?** Verify your `.env` tokens. The sidebar clearly displays the current API Status.
- **UI layout looks misaligned?** Ensure you are running `streamlit>=1.32.0` as specified in `requirements.txt`.
