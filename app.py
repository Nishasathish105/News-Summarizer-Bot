from flask import Flask, render_template, request, jsonify
from newspaper import Article
from deep_translator import GoogleTranslator
from transformers import pipeline
import trafilatura

app = Flask(__name__, static_folder="static", template_folder="templates")

# Load HuggingFace model locally
print("Loading AI model... first time takes 2-5 minutes")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
print("Model ready!")


@app.route("/")
def index():
    return render_template("index.html")


# -------- ARTICLE EXTRACTION WITH METADATA --------
def extract_article_text(url):
    text = ""
    title = "News Summary"
    author = "Unknown"
    date = "N/A"
    image = "/static/news.jpg"

    try:
        article = Article(url)
        article.download()
        article.parse()

        text = article.text
        title = article.title or title
        author = ", ".join(article.authors) if article.authors else author

        if article.publish_date:
            date = article.publish_date.strftime("%B %d, %Y")

        if article.top_image:
            image = article.top_image

    except:
        pass

    # fallback extraction (for blocked sites like MSN)
    if not text or len(text.split()) < 50:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            extracted = trafilatura.extract(downloaded)
            if extracted:
                text = extracted

    return text, title, author, date, image


# -------- SUMMARIZATION --------
def summarize_text(text):
    result = summarizer(text[:1200], max_length=150, min_length=50, do_sample=False)
    return result[0]["summary_text"]


@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        data = request.get_json()

        url = data.get("url", "")
        text = data.get("text", "")
        language = data.get("language", "en")

        # default values
        title = "News Summary"
        author = "Unknown"
        date = "N/A"
        image = "/static/news.jpg"

        full_text = ""

        # URL mode
        if url:
            full_text, title, author, date, image = extract_article_text(url)

        # text mode
        if not full_text:
            full_text = text

        if not full_text or len(full_text.split()) < 50:
            return jsonify({"error": "Please provide at least 50 words."})

        summary = summarize_text(full_text)

        if language != "en":
            summary = GoogleTranslator(source="auto", target=language).translate(summary)

        bullets = [s.strip() for s in summary.split(". ")[:3]]

        return jsonify({
            "title": title,
            "author": author,
            "date": date,
            "image": image,
            "summary": bullets
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
