from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()


# Initialize Flask
app = Flask(__name__)
CORS(app)

# ---------- PostgreSQL Configuration ----------
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "chatdb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------- Database Model ----------
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'llm'
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {"id": self.id, "sender": self.sender, "text": self.message}

# ---------- OpenAI API Config ----------
API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_llm_response(prompt):
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
        return "Please provide a valid OpenAI API key."

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 300
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# # ---------- API Endpoints ----------
# @app.route('/api/chat', methods=['POST'])
# def chat_endpoint():
#     try:
#         data = request.get_json()
#         user_message = data.get("message")
#         if not user_message:
#             return jsonify({"error": "No message provided"}), 400

#         # Save user message to DB
#         user_msg = ChatMessage(sender="user", message=user_message)
#         db.session.add(user_msg)
#         db.session.commit()

#         # Get LLM response
#         llm_text = get_llm_response(user_message)

#         # Save LLM response to DB
#         llm_msg = ChatMessage(sender="llm", message=llm_text)
#         db.session.add(llm_msg)
#         db.session.commit()

#         return jsonify({"response": llm_text})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def chat_history():
    # Return all messages
    messages = ChatMessage.query.order_by(ChatMessage.timestamp).all()
    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_message = data.get("message")
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Save user message
        user_msg = ChatMessage(sender="user", message=user_message)
        db.session.add(user_msg)
        db.session.commit()

        # Fetch chat history (last N messages, e.g., 20)
        history = ChatMessage.query.order_by(ChatMessage.timestamp).all()
        llm_messages = []
        for msg in history[-20:]:
            role = "user" if msg.sender == "user" else "assistant"
            llm_messages.append({"role": role, "content": msg.message})

        # Call OpenAI with history
        payload = {
            "model": "gpt-4.1-mini",
            "messages": llm_messages,
            "max_tokens": 300
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        llm_text = response.json()["choices"][0]["message"]["content"].strip()

        # Save LLM response
        llm_msg = ChatMessage(sender="llm", message=llm_text)
        db.session.add(llm_msg)
        db.session.commit()

        return jsonify({"response": llm_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Create tables within app context
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True, port=5000)

