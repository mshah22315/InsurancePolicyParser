from flask import Flask
from dotenv import load_dotenv
from .db import db
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Register blueprints
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Configure Celery
    from celery_config import make_celery, celery
    make_celery(app)
    
    # Register pipeline blueprint (after Celery is configured)
    from .routes.pipeline_routes import pipeline_bp
    app.register_blueprint(pipeline_bp)
    
    return app 