from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from .db import db
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_object('config.Config')
    
    # Enable CORS for frontend integration with credentials support
    CORS(app, 
         origins=["http://localhost:5000", "http://127.0.0.1:5000", 
                  "http://localhost:5001", "http://127.0.0.1:5001",
                  "http://localhost:5173", "http://127.0.0.1:5173",
                  "http://localhost:3000", "http://127.0.0.1:3000"],
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Register API adapter blueprint for frontend integration
    from .routes.api_adapter_routes import api_adapter_bp
    app.register_blueprint(api_adapter_bp)
    
    # Configure Celery
    from celery_config import make_celery, celery
    make_celery(app)
    
    # Register pipeline blueprint (after Celery is configured)
    from .routes.pipeline_routes import pipeline_bp
    app.register_blueprint(pipeline_bp)
    
    return app 