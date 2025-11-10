import logging
logger = logging.getLogger(__name__)
import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
logger.debug("Loading .env file")

# Try to initialize OpenAI client. Support both the newer `from openai import OpenAI`
# style and the older `import openai` style for compatibility.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    logger.debug("Found OPENAI_API_KEY in environment")
else:
    logger.error("No OPENAI_API_KEY found in environment!")

_client = None
_use_openai = False
_using_new_sdk = False
logger.debug(f"AI client initialized: available={_use_openai}, new_sdk={_using_new_sdk}")

try:
    # Newer OpenAI client (openai >= 1.x)
    from openai import OpenAI
    logger.debug("Successfully imported OpenAI")
    if OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY)
        _use_openai = True  # Set this before initialization
        _using_new_sdk = True
        logger.debug("Successfully initialized OpenAI client")
        # Verify the client works
        try:
            _client.models.list()
            logger.debug("OpenAI client can list models")
        except Exception as e:
            logger.error(f"Error testing OpenAI client: {e}")
            _use_openai = False
            _using_new_sdk = False
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {e}")
    try:
        # Fallback to older openai package interface
        import openai
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            _client = openai
            _use_openai = True
            _using_new_sdk = False
            logger.debug("Successfully initialized legacy OpenAI client")
    except Exception as e:
        logger.error(f"Error initializing legacy OpenAI client: {e}")
        _client = None
        _use_openai = False
        _using_new_sdk = False

SYSTEM_PROMPT = (
    "You are an AI Study Companion that explains clearly, step-by-step, "
    "and adapts to a student's level. Use concise language and examples."
)

def ask_ai(message: str, topic: Optional[str] = None) -> str:
    """
    Sends a Q&A prompt to the AI model and returns plain text.
    If no API key or SDK is available, returns a friendly placeholder.
    """
    if not _use_openai or _client is None:
        return f"(AI placeholder) You asked: '{message}'. Topic: '{topic or 'general'}'. " \
               "Add your OPENAI_API_KEY in .env to get real AI responses."

    user_content = f"Topic: {topic or 'general'}\nQuestion: {message}"

    try:
        if _using_new_sdk:
            # new OpenAI client
            resp = _client.chat.completions.create(
                # use a widely-available model by default to reduce access issues
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2
            )
            # Access several possible response shapes safely
            try:
                return resp.choices[0].message.content.strip()
            except Exception:
                # fallback to dict-like access
                return resp["choices"][0]["message"]["content"].strip()
        else:
            # older openai package
            resp = _client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2
            )
            # older responses may be dict-like
            if isinstance(resp, dict):
                return resp.get("choices", [])[0].get("message", {}).get("content", "").strip()
            # object-like
            try:
                return resp.choices[0].message.content.strip()
            except Exception:
                return str(resp)
    except Exception as e:
        # Log full exception for diagnostics but return a friendly placeholder
        logger.error(f"AI request failed: {e}", exc_info=True)
        msg = str(e)
        # If the error is related to authentication, quota or rate limits, fall back to placeholder
        lowered = msg.lower()
        if any(k in lowered for k in ("quota", "rate limit", "rate_limit", "insufficient_quota", "authentication", "401", "api key")):
            return f"(AI placeholder) The AI service is unavailable: {msg}. Showing a local placeholder response."
        return f"Error from AI: {msg}"

def generate_quiz(topic: str, num_questions: int = 5) -> Dict:
    """
    Generates an MCQ quiz via AI. Returns a structured JSON payload:
    {
      "topic": "...",
      "questions": [
        {
          "q": "Question text",
          "options": ["A", "B", "C", "D"],
          "answer": 1,  # index in options
          "explanation": "..."
        }, ...
      ]
    }
    """
    if not _use_openai or _client is None:
        # Return a deterministic placeholder quiz
        return {
            "topic": topic,
            "questions": [
                {
                    "q": f"Placeholder: What is a key concept in {topic}?",
                    "options": ["Concept A", "Concept B", "Concept C", "Concept D"],
                    "answer": 0,
                    "explanation": "Add OPENAI_API_KEY in .env for real AI-generated quizzes."
                }
            ] * max(1, num_questions)
        }

    prompt = (
        f"Create a {num_questions}-question multiple-choice quiz on '{topic}'. "
        "Return JSON ONLY with fields: topic, questions[]. Each question must have: "
        "q, options (4), answer (index 0-3), explanation (1-2 sentences)."
    )

    try:
        if _using_new_sdk:
            resp = _client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Return strictly valid JSON. No extra commentary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            try:
                content = resp.choices[0].message.content.strip()
            except Exception:
                content = resp["choices"][0]["message"]["content"].strip()
        else:
            resp = _client.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Return strictly valid JSON. No extra commentary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            if isinstance(resp, dict):
                content = resp.get("choices", [])[0].get("message", {}).get("content", "").strip()
            else:
                try:
                    content = resp.choices[0].message.content.strip()
                except Exception:
                    content = str(resp)

        # Ensure valid JSON (the model is instructed to output JSON)
        quiz = json.loads(content)
        if "topic" not in quiz or "questions" not in quiz:
            raise ValueError("Invalid quiz structure")
        return quiz
    except Exception as e:
        # Fallback structure if parsing fails
        return {
            "topic": topic,
            "error": f"AI quiz generation failed: {e}",
            "questions": [
                {
                    "q": f"Fallback: Which of the following relates to {topic}?",
                    "options": ["A", "B", "C", "D"],
                    "answer": 0,
                    "explanation": "Quiz generated by fallback due to parsing error."
                }
            ]
        }
