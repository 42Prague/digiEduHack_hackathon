from flask import Flask
from flask_cors import CORS
def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})


    # register blueprints
    from .routes.ingest_routes import ingest_bp
    from .routes.query_routes import query_bp
    from .routes.query_routes import generate_data_bp

    app.register_blueprint(ingest_bp, url_prefix="/api")
    app.register_blueprint(query_bp, url_prefix="/api")
    app.register_blueprint(generate_data_bp, url_prefix="/api")

    # initialize DB (create table if missing)
    from .db.vector_store import VectorStore
    VectorStore().initialize()

    return app
