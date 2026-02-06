from flask import Flask, render_template, request, jsonify
from newspaper import Article, Config
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


# 🧠 Summarization function
def summarize_text(text, max_len, min_len):
    prompt = f"Summarize the following text in {max_len} words or less:\n{text}"
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

        full_text = ""
        title = "Custom Text"
        author = "User"
        date = "N/A"
        image = "/static/news.jpg"

        # 🌐 HANDLE URL INPUT
        if url and url.strip() != "":
            try:
                config = Config()
                config.browser_user_agent = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
                config.request_timeout = 20

                article = Article(url, config=config)
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

        # ✍️ TEXT FALLBACK
        if not full_text and text:
            full_text = text

        # 🚫 VALIDATION
        if not full_text or len(full_text.split()) < 50:
            return jsonify({"error": "Please provide at least 50 words or a valid article URL."})

        # ⏱ LIMIT TEXT SIZE (HF token limit protection)
        full_text = " ".join(full_text.split()[:800])

        # 📏 SUMMARY LENGTH
        if summary_length == "short":
            max_len, min_len = 80, 30
        elif summary_length == "long":
            max_len, min_len = 200, 80
        else:
            max_len, min_len = 130, 50

        # 🧠 SUMMARIZE
        summary_text = summarize_text(full_text, max_len, min_len)

        # 🌍 TRANSLATE
        if target_lang and target_lang != "en":
            summary_text = GoogleTranslator(source="auto", target=target_lang).translate(summary_text)

        # 🔹 BULLET POINTS
        sentences = summary_text.split(". ")
        bullets = [f"• {s.strip().rstrip('.')}" for s in sentences[:3] if s.strip()]

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

