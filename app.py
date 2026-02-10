from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
import requests
import os
import re
import trafilatura

app = Flask(__name__, static_folder="static", template_folder="templates")

# HuggingFace token
HF_TOKEN = os.environ.get("HF_API_TOKEN")

HF_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"

HEADERS = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}


@app.route("/")
def index():
    return render_template("index.html")


# ---------- SUMMARIZE ----------
def summarize_text(text, max_len):
    payload = {
        "inputs": text,
        "parameters": {
            "max_new_tokens": max_len,
            "min_new_tokens": 40
        }
    }

    response = requests.post(HF_API_URL, headers=HEADERS, json=payload, timeout=60)
    result = response.json()

    if isinstance(result, dict) and result.get("error"):
        raise Exception(result["error"])

    return result[0]["summary_text"]


# ---------- ARTICLE EXTRACTOR ----------
def extract_article(url):
    try:
        # follow redirects (Google News / MSN etc)
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
        final_url = r.url

        downloaded = trafilatura.fetch_url(final_url)
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)

        return text if text else "", final_url
    except:
        return "", url


# ---------- IMAGE EXTRACTOR ----------
def extract_image(url):
    try:
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text

        patterns = [
            r'<meta property="og:image" content="(.*?)"',
            r'<meta name="twitter:image" content="(.*?)"',
            r'"thumbnailUrl":"(.*?)"'
        ]

        for p in patterns:
            m = re.search(p, html)
            if m:
                return m.group(1)

    except:
        pass

    return "/static/news.jpg"


# ---------- MAIN ROUTE ----------
@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        data = request.get_json(silent=True)

        if data:
            url = data.get("url")
            text = data.get("text")
            target_lang = data.get("language")
            summary_length = data.get("length")
        else:
            url = request.form.get("url")
            text = request.form.get("text")
            target_lang = request.form.get("language")
            summary_length = request.form.get("length")

        full_text = ""
        title = "News Article"
        image = "/static/news.jpg"

        # ---- REAL ARTICLE EXTRACTION ----
        if url and url.strip():
            article_text, real_url = extract_article(url)

            if article_text:
                full_text = article_text
                title = article_text.split(".")[0][:120]
                image = extract_image(real_url)

        # manual text fallback
        if not full_text and text:
            full_text = text

        if not full_text or len(full_text.split()) < 50:
            return jsonify({"error": "Could not extract article text."})

        full_text = " ".join(full_text.split()[:900])

        # summary size
        if summary_length == "short":
            max_len = 80
        elif summary_length == "long":
            max_len = 200
        else:
            max_len = 130

        summary = summarize_text(full_text, max_len)

        if target_lang and target_lang != "en":
            summary = GoogleTranslator(source="auto", target=target_lang).translate(summary)

        bullets = [f"• {s.strip()}" for s in summary.split(". ")[:3] if s.strip()]

        return jsonify({
            "title": title,
            "author": "Unknown",
            "date": "N/A",
            "image": image,
            "summary": "<br>".join(bullets)
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
