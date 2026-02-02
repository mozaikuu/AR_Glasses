from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-smart-glasses'
    
    from web_app.routes import main
    app.register_blueprint(main)
    
    return app
