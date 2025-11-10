from flask import Blueprint, request, jsonify
from backend.services.ai_api import generate_quiz
from backend.services.storage import save_quiz_result

quiz_bp = Blueprint("quiz", __name__)

@quiz_bp.route("", methods=["POST"])
def quiz():
    data = request.get_json(force=True) or {}
    topic = data.get("topic", "").strip()
    num_questions = int(data.get("num_questions", 5))

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    quiz_payload = generate_quiz(topic, num_questions=num_questions)

    # Optionally pre-save the quiz metadata (e.g., generated quiz)
    save_quiz_result({
        "topic": topic,
        "quiz": quiz_payload,
        "status": "generated"
    })

    return jsonify(quiz_payload)
