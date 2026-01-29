import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from models import db
from config import config
from ai_task_creator import ai_task_blueprint
from kanban_dashboard import kanban_blueprint
from ticket_preview import ticket_preview_blueprint
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    env = os.environ.get('FLASK_ENV', 'production')
    app.config.from_object(config[env])
    
    # CORS configuration
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(ai_task_blueprint)
    app.register_blueprint(kanban_blueprint)
    app.register_blueprint(ticket_preview_blueprint)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint for Railway"""
        return jsonify({'status': 'healthy', 'service': 'ai-kanban-app'})
    
    # Create tables on startup
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            db.create_all()
            print(f"✅ Database connected and tables created ({env} mode)")
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)