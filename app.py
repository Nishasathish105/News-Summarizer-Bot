from flask import Flask, render_template, request, jsonify
from newspaper import Article
from deep_translator import GoogleTranslator
from huggingface_hub import InferenceClient
import os

app = Flask(__name__, static_folder="static", template_folder="templates")

# 🔑 Hugging Face API Token
HF_TOKEN = os.environ.get("HF_API_TOKEN")

if not HF_TOKEN:
    print("❌ ERROR: Hugging Face API Token not found")

client = InferenceClient(token=HF_TOKEN)


@app.route("/")
def index():
    return render_template("index.html")


# 🧠 Summarization function (FIXED for new HF API)
def summarize_text(text, max_len, min_len):
    prompt = f"Summarize the following text in {max_len} words or less: {text}"
    response = client.text_generation(
        prompt,
        model="facebook/bart-large-cnn",
        max_new_tokens=max_len
    )
    return response.generated_text


@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        url = request.form.get("url")
        text = request.form.get("text")
        summary_length = request.form.get("length")
        target_lang = request.form.get("language")

        # Defaults
        full_text = ""
        title = "Custom Text"
        author = "User"
        date = "N/A"
        image = "/static/news.jpg"

        # 🌐 URL input
        if url:
            try:
                article = Article(
                    url,
                    browser_user_agent="Mozilla/5.0"
                )
                article.download()
                article.parse()

                if article.text and len(article.text.split()) > 50:
                    full_text = article.text
                    title = article.title or "News Article"
                    author = ", ".join(article.authors) if article.authors else "Unknown"
                    date = (
                        article.publish_date.strftime("%B %d, %Y")
                        if article.publish_date else "Unknown"
                    )
                    image = article.top_image or image
            except Exception as e:
                print("⚠️ URL parsing failed:", e)

        # ✍️ Text fallback
        if not full_text:
            full_text = text

        if not full_text or len(full_text.split()) < 50:
            return jsonify({"error": "Please paste at least 50 words."})

        # ⏱ Limit text size
        full_text = " ".join(full_text.split()[:800])

        # 📏 Summary length
        if summary_length == "short":
            max_len, min_len = 80, 30
        elif summary_length == "long":
            max_len, min_len = 200, 80
        else:
            max_len, min_len = 130, 50

        # 🧠 Summarize
        summary_text = summarize_text(full_text, max_len, min_len)

        # 🌍 Translate
        if target_lang and target_lang != "en":
            summary_text = GoogleTranslator(
                source="auto",
                target=target_lang
            ).translate(summary_text)

        # 🔹 Bullet points
        sentences = summary_text.split(". ")
        bullets = [
            f"• {s.strip().rstrip('.')}"
            for s in sentences[:3]
            if s.strip()
        ]

        return jsonify({
            "title": title,
            "author": author,
            "date": date,
            "image": image,
            "summary": "<br>".join(bullets)
        })

    except Exception as e:
        print("❌ ERROR:", e)
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
