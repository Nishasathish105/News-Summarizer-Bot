document.getElementById("summarizeForm").addEventListener("submit", async function(e) {
  e.preventDefault();

  const loading = document.getElementById("loading");
  const result = document.getElementById("result");
  const summaryContainer = document.getElementById("articleSummary");
  const readButton = document.getElementById("readAloud");

  result.classList.add("hidden");
  loading.classList.remove("hidden");

  const formData = new FormData(this);

  try {
      const response = await fetch("/summarize", {
          method: "POST",
          body: formData
      });

      const data = await response.json();
      loading.classList.add("hidden");

      if (data.error) {
          alert("Error: " + data.error);
          return;
      }

      readButton.classList.remove("hidden");
      result.classList.remove("hidden");

      document.getElementById("articleTitle").textContent = data.title;
      document.getElementById("articleAuthor").textContent = data.author;
      document.getElementById("articleDate").textContent = data.date;
      document.getElementById("articleImage").src = data.image;

      summaryContainer.innerHTML = "";
      const sentences = data.summary.split(/<br>/);
      sentences.forEach((sentence) => {
          if (sentence.trim()) {
              const li = document.createElement("li");
              li.textContent = sentence.trim(); // no extra dots
              summaryContainer.appendChild(li);
          }
      });
  } catch (err) {
      loading.classList.add("hidden");
      alert("An error occurred while summarizing.");
      console.error(err);
  }
});

// 🎧 Read Aloud
const readButton = document.getElementById("readAloud");
let isSpeaking = false;

readButton.addEventListener("click", () => {
  const summaryText = document.getElementById("articleSummary").innerText;
  if (!summaryText.trim()) {
    alert("No summary available to read.");
    return;
  }

  if (isSpeaking) {
    window.speechSynthesis.cancel();
    readButton.textContent = "🔊 Read Aloud";
    isSpeaking = false;
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(summaryText);
  const selectedLang = document.getElementById("language").value;

  if (selectedLang === "hi") utterance.lang = "hi-IN";
  else if (selectedLang === "kn") utterance.lang = "kn-IN";
  else if (selectedLang === "ta") utterance.lang = "ta-IN";
  else if (selectedLang === "te") utterance.lang = "te-IN";
  else if (selectedLang === "ml") utterance.lang = "ml-IN";
  else utterance.lang = "en-US";

  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
  isSpeaking = true;
  readButton.textContent = "⏹ Stop Reading";

  utterance.onend = () => {
    readButton.textContent = "🔊 Read Aloud";
    isSpeaking = false;
  };
});

// 📋 Copy Summary
document.getElementById("copySummary").addEventListener("click", () => {
  const summaryText = document.getElementById("articleSummary").innerText;
  if (!summaryText.trim()) {
    alert("No summary to copy.");
    return;
  }
  navigator.clipboard.writeText(summaryText);
  alert("Summary copied to clipboard!");
});

// 🌐 Open Original Article
document.getElementById("openArticle").addEventListener("click", () => {
  const url = document.getElementById("url").value;
  if (url.trim()) {
    window.open(url, "_blank");
  } else {
    alert("Please enter a valid article URL.");
  }
});

// 🌗 Light/Dark Mode Toggle
const modeToggle = document.getElementById("modeToggle");
modeToggle.addEventListener("click", () => {
  document.body.classList.toggle("light-mode");
  modeToggle.textContent = document.body.classList.contains("light-mode")
    ? "🌞 Light Mode"
    : "🌙 Dark Mode";
});

// 🎙️ Speech-to-Text
const micBtn = document.getElementById("micBtn");
const textArea = document.getElementById("text");
let recognition;

if ("webkitSpeechRecognition" in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-IN";

  micBtn.addEventListener("click", () => {
    recognition.start();
    micBtn.textContent = "🎤 Listening...";
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    textArea.value += " " + transcript;
    micBtn.textContent = "🎙️";
  };

  recognition.onerror = () => {
    alert("Speech recognition error. Please try again.");
    micBtn.textContent = "🎙️";
  };

  recognition.onend = () => {
    micBtn.textContent = "🎙️";
  };
} else {
  micBtn.disabled = true;
  micBtn.title = "Speech recognition not supported";
}
