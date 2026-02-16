let lastArticleURL = "";

/* ---------------- SUBMIT FORM ---------------- */
document.getElementById("summarizeForm").addEventListener("submit", async function(e) {
  e.preventDefault();

  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const summaryContainer = document.getElementById("articleSummary");
  const readButton = document.getElementById("readAloud");

  loading.classList.remove("hidden");
  result.classList.add("hidden");

  const payload = {
    url: document.getElementById("url").value,
    text: document.getElementById("text").value,
    language: document.getElementById("language").value,
    length: "medium"
  };

  lastArticleURL = payload.url;

  try {
    const response = await fetch("/summarize", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    loading.classList.add("hidden");

    if (data.error) {
      alert(data.error);
      return;
    }

    result.classList.remove("hidden");
    readButton.classList.remove("hidden");

    document.getElementById("articleTitle").textContent = data.title;
    document.getElementById("articleAuthor").textContent = data.author;
    document.getElementById("articleDate").textContent = data.date;
    document.getElementById("articleImage").src = data.image;

    summaryContainer.innerHTML = "";
    data.summary.forEach(line => {
      const li = document.createElement("li");
      li.textContent = line;
      summaryContainer.appendChild(li);
    });

  } catch(err) {
    loading.classList.add("hidden");
    alert("Server error");
    console.error(err);
  }
});


/* ---------------- READ ALOUD ---------------- */
const readButton = document.getElementById("readAloud");
let speaking = false;

readButton.addEventListener("click", () => {

  const text = document.getElementById("articleSummary").innerText;
  if (!text.trim()) return alert("No summary available");

  if (speaking) {
    speechSynthesis.cancel();
    readButton.textContent = "🔊 Read Aloud";
    speaking = false;
    return;
  }

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = document.getElementById("language").value || "en-US";

  speechSynthesis.speak(utterance);
  readButton.textContent = "⏹ Stop Reading";
  speaking = true;

  utterance.onend = () => {
    readButton.textContent = "🔊 Read Aloud";
    speaking = false;
  };
});


/* ---------------- COPY SUMMARY ---------------- */
document.getElementById("copySummary").addEventListener("click", () => {
  const text = document.getElementById("articleSummary").innerText;

  if (!text.trim()) {
    alert("No summary to copy");
    return;
  }

  navigator.clipboard.writeText(text);
  alert("Summary copied!");
});


/* ---------------- OPEN ARTICLE ---------------- */
document.getElementById("openArticle").addEventListener("click", () => {
  if (!lastArticleURL || lastArticleURL.trim() === "") {
    alert("No article URL available.");
    return;
  }

  window.open(lastArticleURL, "_blank");
});


/* ---------------- DARK MODE ---------------- */
document.getElementById("modeToggle").addEventListener("click", () => {
  document.body.classList.toggle("light-mode");
});


/* ---------------- SPEECH TO TEXT (MIC) ---------------- */
const micBtn = document.getElementById("micBtn");
const textArea = document.getElementById("text");

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();

  recognition.lang = "en-IN";
  recognition.continuous = false;
  recognition.interimResults = false;

  micBtn.addEventListener("click", () => {
    recognition.start();
    micBtn.textContent = "🎤...";
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    textArea.value += " " + transcript;
    micBtn.textContent = "🎙️";
  };

  recognition.onerror = () => {
    micBtn.textContent = "🎙️";
    alert("Microphone permission denied");
  };

  recognition.onend = () => {
    micBtn.textContent = "🎙️";
  };

} else {
  micBtn.disabled = true;
  micBtn.title = "Speech recognition not supported in this browser";
}
