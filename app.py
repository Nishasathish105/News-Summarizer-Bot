from flask import Flask, render_template, request, jsonify
from newspaper import Article, Config
from deep_translator import GoogleTranslator
from huggingface_hub import InferenceClient
import os
import requests
from bs4 import BeautifulSoup

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
def summarize_text(text, max_len):
    prompt = f"Summarize the following news article in {max_len} words:\n{text}"
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
                # ---- Try newspaper3k first ----
                config = Config()
                config.browser_user_agent = "Mozilla/5.0"
                config.request_timeout = 20

                article = Article(url, config=config)
                article.download()
                article.parse()

                if article.text and len(article.text.split()) > 50:
                    full_text = article.text
                    title = article.title or "News Article"
                    author = ", ".join(article.authors) if article.authors else "Unknown"
                    date = article.publish_date.strftime("%B %d, %Y") if article.publish_date else "Unknown"
                    image = article.top_image or image

            except:
                pass

            # ---- FALLBACK SCRAPER (for blocked sites) ----
            if not full_text:
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0",
                        "Accept-Language": "en-US,en;q=0.9"
                    }

                    r = requests.get(url, headers=headers, timeout=15)
                    soup = BeautifulSoup(r.text, "html.parser")

                    paragraphs = soup.find_all("p")
                    article_text = " ".join(p.get_text() for p in paragraphs)

                    if len(article_text.split()) > 50:
                        full_text = article_text
                        title_tag = soup.find("title")
                        if title_tag:
                            title = title_tag.get_text()

                except Exception as e:
                    print("Fallback scraper failed:", e)

        # ✍️ TEXT INPUT FALLBACK
        if not full_text and text:
            full_text = text

        # 🚫 VALIDATION
        if not full_text or len(full_text.split()) < 50:
            return jsonify({"error": "Please provide at least 50 words or a valid article URL."})

        # ⏱ Limit size (HF free tier safety)
        full_text = " ".join(full_text.split()[:800])

        # 📏 SUMMARY LENGTH
        if summary_length == "short":
            max_len = 80
        elif summary_length == "long":
            max_len = 200
        else:
            max_len = 130

        # 🧠 SUMMARIZE
        summary_text = summarize_text(full_text, max_len)

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


