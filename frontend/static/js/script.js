const API_BASE = "/api";

// --- Chat ---
async function sendMessage() {
  const input = document.getElementById("user-message");
  const chatWindow = document.getElementById("chat-window");
  const message = input.value.trim();
  if (!message) return;

  // Display user message
  chatWindow.innerHTML += `<div class="message user">${message}</div>`;
  input.value = "";

  // Add loading indicator
  const loadingId = "loading-" + Date.now();
  chatWindow.innerHTML += `<div class="message ai" id="${loadingId}">Clara is thinking...</div>`;
  chatWindow.scrollTop = chatWindow.scrollHeight;

  try {
    console.log('Sending request to:', `${API_BASE}/chat`);
    const requestBody = JSON.stringify({ message });
    console.log('Request body:', requestBody);
    
    const res = await fetch(`${API_BASE}/chat/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: requestBody
    });
    
    console.log('Response status:', res.status);
    console.log('Response headers:', Object.fromEntries(res.headers.entries()));
    
    // Try to get the response body as text first
    const rawResponse = await res.text();
    console.log('Raw response:', rawResponse);
    
    let data;
    try {
      data = JSON.parse(rawResponse);
      console.log('Parsed response data:', data);
    } catch (parseErr) {
      console.error('Failed to parse response as JSON:', parseErr);
      throw new Error(`Invalid JSON response: ${rawResponse}`);
    }

    // Remove loading indicator
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();

    // Handle placeholder vs real AI response
    if (data.response && data.response.startsWith("(AI placeholder)")) {
      chatWindow.innerHTML += `<div class="message ai">⚠️ ${data.response}</div>`;
    } else if (data.error) {
      console.error('Server error:', data.error);
      chatWindow.innerHTML += `<div class="message ai error">⚠️ ${data.error}</div>`;
    } else if (data.response) {
      chatWindow.innerHTML += `<div class="message ai">${data.response}</div>`;
    } else {
      console.error('Unexpected response format:', data);
      chatWindow.innerHTML += `<div class="message ai error">Unexpected response format</div>`;
    }
    chatWindow.scrollTop = chatWindow.scrollHeight;
  } catch (err) {
    console.error('Request failed:', err);
    const loadingEl = document.getElementById(loadingId);
    if (loadingEl) loadingEl.remove();
    chatWindow.innerHTML += `<div class="message ai error">Error: ${err.message}</div>`;
  }
}

// --- Quiz ---
let currentQuiz = null;
let currentTopic = "";
let score = 0;
let answered = 0;

async function generateQuiz() {
  // Reset state for new quiz
  score = 0;
  answered = 0;
  currentQuiz = null;

  currentTopic = document.getElementById("quiz-topic").value.trim();
  const container = document.getElementById("quiz-container");
  if (!currentTopic) {
    container.innerHTML = "<p>Please enter a topic.</p>";
    return;
  }

  container.innerHTML = "<p>Generating quiz...</p>";

  try {
    const res = await fetch(`${API_BASE}/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic: currentTopic, num_questions: 5 })
    });
    const quiz = await res.json();

    if (quiz.error) {
      container.innerHTML = `<p>Error: ${quiz.error}</p>`;
      return;
    }

    currentQuiz = quiz;
    container.innerHTML = "";
    quiz.questions.forEach((q, i) => {
      const options = q.options.map((opt, idx) =>
        `<li onclick="checkAnswer(${i}, ${idx}, ${q.answer})">${String.fromCharCode(65 + idx)}. ${opt}</li>`
      ).join("");
      container.innerHTML += `
        <div class="quiz-question" id="q${i}">
          <p><strong>Q${i + 1}:</strong> ${q.q}</p>
          <ul>${options}</ul>
          <p class="explanation" style="display:none;"><em>Answer:</em> ${q.options[q.answer]}<br/>
          <em>Explanation:</em> ${q.explanation}</p>
        </div>
      `;
    });
  } catch (err) {
    container.innerHTML = `<p>Error: ${err.message}</p>`;
  }
}

function checkAnswer(qIndex, selected, correct) {
  const questionDiv = document.getElementById(`q${qIndex}`);
  const options = questionDiv.querySelectorAll("li");
  options.forEach((li, idx) => {
    if (idx === correct) {
      li.style.background = "#c8f7c5"; // green
    } else if (idx === selected) {
      li.style.background = "#f7c5c5"; // red
    }
    li.style.pointerEvents = "none";
  });
  questionDiv.querySelector(".explanation").style.display = "block";

  answered++;
  if (selected === correct) score++;

  // If all questions answered, save results
  if (answered === currentQuiz.questions.length) {
    saveQuizResult();
  }
}

async function saveQuizResult() {
  try {
    const res = await fetch(`${API_BASE}/progress/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic: currentTopic,
        score: score,
        total: currentQuiz.questions.length,
        answers: currentQuiz.questions.map((q) => ({
          question: q.q,
          correct: q.options[q.answer],
          explanation: q.explanation
        }))
      })
    });
    const data = await res.json();
    alert(`Quiz completed! Score: ${score}/${currentQuiz.questions.length}`);
    console.log("Progress saved:", data);
  } catch (err) {
    console.error("Failed to save quiz result:", err);
  } finally {
    // Reset counters for next quiz
    score = 0;
    answered = 0;
  }
}

// --- Progress ---
async function loadProgress() {
  const container = document.getElementById("progress-container");
  container.innerHTML = "<p>Loading progress...</p>";

  try {
    const res = await fetch(`${API_BASE}/progress`);
    const data = await res.json();

    if (!data.events || data.events.length === 0) {
      container.innerHTML = "<p>No progress recorded yet.</p>";
      return;
    }

    container.innerHTML = "<ul>" + data.events.map(ev =>
      `<li>[${ev.type}] ${ev.topic || ''} - ${ev.timestamp} 
       ${ev.type === "quiz" ? `(Score: ${ev.score}/${ev.total})` : ""}</li>`
    ).join("") + "</ul>";
  } catch (err) {
    container.innerHTML = `<p>Error: ${err.message}</p>`;
  }
}
