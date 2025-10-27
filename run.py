import os

# if os.getenv("DEV", False):
#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "site-to-agent-69c06280f316.json"
# else:
json_content = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
json_path = "/tmp/google-credentials.json"

if not json_content:
    raise RuntimeError("Google credentials not found. Please set GOOGLE_APPLICATION_CREDENTIALS_JSON.")

if not os.path.exists(json_path):
    with open(json_path, "w") as f:
        f.write(json_content)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path
else:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_path

# Now import the rest (after env is set)
from flask import Flask
from flask_cors import CORS
from app.routes import main

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})
app.register_blueprint(main)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)