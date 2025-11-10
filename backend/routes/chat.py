from flask import Blueprint, request, jsonify
from backend.services.ai_api import ask_ai
import logging

chat_bp = Blueprint("chat_bp", __name__)
logger = logging.getLogger(__name__)


@chat_bp.route("/", methods=["POST"])
def chat():
    logger.debug("Chat endpoint hit")
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(f"Raw data: {request.get_data(as_text=True)}")
    logger.debug(f"Form data: {request.form}")
    logger.debug(f"JSON data: {request.get_json(silent=True)}")
    
    try:
        # Parse JSON body safely
        data = request.get_json(silent=True)
        if data is None:
            error_msg = "Invalid or missing JSON body"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400

        user_message = (data.get("message") or "").strip()
        topic = data.get("topic")

        if not user_message:
            error_msg = "Message is required"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400

        # Protect against excessively large messages
        if len(user_message) > 5000:
            error_msg = "Message too long"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400

        try:
            ai_response = ask_ai(user_message, topic=topic)
            logger.debug(f"AI response: {ai_response}")
            return jsonify({"message": user_message, "response": ai_response}), 200
        except Exception as e:
            error_msg = f"AI call failed: {str(e)}"
            logger.exception(error_msg)
            return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(error_msg)
        return jsonify({"error": error_msg}), 500
    # Parse JSON body safely
    data = request.get_json(silent=True)
    if data is None:
        logger.error("Invalid or missing JSON body")
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    user_message = (data.get("message") or "").strip()
    topic = data.get("topic")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Protect against excessively large messages
    if len(user_message) > 5000:
        return jsonify({"error": "Message too long"}), 400

    try:
        ai_response = ask_ai(user_message, topic=topic)
    except Exception as e:
        logger.exception("AI call failed")
        ai_response = f"Error from AI service: {e}"

    # Return consistent payload expected by the frontend
    return jsonify({"message": user_message, "response": ai_response}), 200
