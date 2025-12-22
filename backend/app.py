from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import traceback
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    # Resolve frontend paths relative to project root to avoid cwd issues
    project_root = Path(__file__).resolve().parent.parent
    frontend_dir = project_root / "frontend"
    static_dir = str(frontend_dir / "static")
    templates_dir = str(frontend_dir / "templates")

    app = Flask(
        __name__,
        static_folder=static_dir,        # Folder with css/, js/, images/
        template_folder=templates_dir    # Folder with index.html
    )
    
    # Enable CORS with proper configuration
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "allow_headers": ["Content-Type", "Authorization"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        }
    })
    
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
            
    @app.after_request
    def after_request(response):
        if not response.headers.get('Access-Control-Allow-Origin'):
            response.headers.add('Access-Control-Allow-Origin', '*')
        if not response.headers.get('Access-Control-Allow-Headers'):
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        if not response.headers.get('Access-Control-Allow-Methods'):
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # Error handler for all exceptions
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f"An error occurred: {str(error)}")
        logger.error(traceback.format_exc())
        error_response = {
            "error": str(error),
            "status": "error",
            "traceback": traceback.format_exc()
        }
        logger.error(f"Full error response: {error_response}")
        return jsonify(error_response), 500

    @app.before_request
    def log_request():
        logger.debug(f"Incoming request: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        if request.is_json:
            logger.debug(f"JSON data: {request.get_json()}")

    # Register blueprints (modular routes)
    # Import inside function so app can still start even if blueprints error
    try:
        from routes.chat import chat_bp
        from routes.quiz import quiz_bp
        from routes.progress import progress_bp

        # Register blueprints directly under /api
        app.register_blueprint(chat_bp, url_prefix="/api/chat")
        app.register_blueprint(quiz_bp, url_prefix="/api")
        app.register_blueprint(progress_bp, url_prefix="/api")
        
        # Debug URL rules
        for rule in app.url_map.iter_rules():
            logger.debug(f"Route: {rule}, Methods: {rule.methods}")
        
        # Log registered routes
        logger.debug("Registered routes:")
        for rule in app.url_map.iter_rules():
            logger.debug(f"  {rule.endpoint}: {rule.rule}")
    except Exception as e:
        logger.warning(f"Could not register blueprints: {e}")

    # ---------------- Frontend routes ----------------
    @app.route("/")
    def index():
        try:
            return render_template("index.html")
        except Exception as e:
            logger.error(f"Error serving index.html: {str(e)}")
            return jsonify({"error": "Failed to load index page"}), 500
    # -------------------------------------------------

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return jsonify({"status": "healthy"}), 200

    return app

def get_env_config():
    try:
        return {
            'debug': os.getenv("FLASK_DEBUG", "true").lower() == "true",
            'host': os.getenv("FLASK_HOST", "0.0.0.0"),
            'port': int(os.getenv("FLASK_PORT", "5000"))
        }
    except ValueError as e:
        logger.error(f"Environment configuration error: {str(e)}")
        return {'debug': True, 'host': "0.0.0.0", 'port': 5000}

if __name__ == "__main__":
    app = create_app()
    config = get_env_config()
    app.run(
        debug=config['debug'],
        host=config['host'],
        port=config['port']
    )
