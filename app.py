from flask import Flask, render_template, request, jsonify
from transformers import pipeline
from newspaper import Article
from deep_translator import GoogleTranslator

app = Flask(__name__)

# Load summarization model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/summarize', methods=['POST'])
def summarize():
    url = request.form.get('url')
    text = request.form.get('text')
    summary_length = request.form.get('length')  # short, medium, long
    target_lang = request.form.get('language')  # e.g. hi, kn, ta

    try:
        # Extract text from URL or input
        if url:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            title = article.title
            author = ", ".join(article.authors) if article.authors else "Unknown"
            date = article.publish_date.strftime("%B %d, %Y") if article.publish_date else "Unknown"
            image = article.top_image
            full_text = article.text
        else:
            title = "Custom Text"
            author = "User"
            date = "N/A"
            image = "/static/news.jpg"
            full_text = text

        # 🛡️ Safety check before summarizing
        if not full_text or len(full_text.split()) < 50:
            return jsonify({"error": "Article text too short or could not be extracted. Try another URL or paste text manually."})

        # Adjust summary length
        if summary_length == "short":
            max_len, min_len = 80, 30
        elif summary_length == "long":
            max_len, min_len = 200, 80
        else:  # medium default
            max_len, min_len = 130, 50

        # Summarize text safely
        try:
            summary = summarizer(full_text, max_length=max_len, min_length=min_len, do_sample=False)
        except Exception as e:
            return jsonify({"error": f"Summarization failed: {str(e)}"})

        summary_text = summary[0]['summary_text']

        # Translate summary if user chose a non-English language
        if target_lang and target_lang != "en":
            translated_summary = GoogleTranslator(source='auto', target=target_lang).translate(summary_text)
        else:
            translated_summary = summary_text

        # Format summary as bullet points (removed double dots)
        sentences = translated_summary.split('. ')
        bullets = [f"• {s.strip().rstrip('.')}" for s in sentences[:3] if s.strip()]
        formatted_summary = "<br>".join(bullets)

        return jsonify({
            'title': title,
            'author': author,
            'date': date,
            'image': image,
            'summary': formatted_summary
        })

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
