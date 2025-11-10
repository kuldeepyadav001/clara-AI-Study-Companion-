from flask import Blueprint, request, jsonify
from backend.services.storage import (
    read_progress,
    save_study_event,
    save_quiz_result
)

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("", methods=["GET"])
def get_progress():
    progress = read_progress()
    return jsonify(progress)

@progress_bp.route("/study", methods=["POST"])
def add_study_event():
    data = request.get_json(force=True) or {}
    event = {
        "type": "study",
        "topic": data.get("topic"),
        "notes": data.get("notes"),
        "timestamp": data.get("timestamp")  # allow frontend to set; otherwise storage can add
    }
    save_study_event(event)
    return jsonify({"status": "ok", "event": event})

@progress_bp.route("/quiz", methods=["POST"])
def add_quiz_result():
    data = request.get_json(force=True) or {}
    result = {
        "type": "quiz",
        "topic": data.get("topic"),
        "score": data.get("score"),
        "total": data.get("total"),
        "answers": data.get("answers"),
        "timestamp": data.get("timestamp")
    }
    save_quiz_result(result)
    return jsonify({"status": "ok", "result": result})
