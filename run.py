from flask import Flask
from flask_cors import CORS
from app.routes import main
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})
app.register_blueprint(main)

json_content = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
json_path = "/tmp/google-credentials.json"

if not json_content:
    raise RuntimeError("Google credentials not found. Please set GOOGLE_APPLICATION_CREDENTIALS_JSON.")

if not os.path.exists(json_path):
    with open(json_path, "w") as f:
        f.write(json_content)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 