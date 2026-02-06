from flask import Flask, render_template, request, jsonify
from deep_translator import GoogleTranslator
import requests
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

# HuggingFace token
HF_TOKEN = os.environ.get("HF_API_TOKEN")

# NEW ENDPOINT (UPDATED)
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

        # UNIVERSAL ARTICLE READER
        if url and url.strip():
            try:
                reader_url = "https://r.jina.ai/" + url
                response = requests.get(reader_url, timeout=20)
                full_text = response.text

                first_line = full_text.split("\n")[0]
                if len(first_line) < 150:
                    title = first_line.strip()

            except Exception as e:
                print("Reader failed:", e)

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
            "image": "/static/news.jpg",
            "summary": "<br>".join(bullets)
        })

    except Exception as e:
        print("SERVER ERROR:", e)
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
