from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

# Initialize Flask application
app = Flask(__name__)
# Enable CORS to allow the React frontend to make requests
CORS(app)

# The base URL for the OpenAI Chat Completions API
API_URL = "https://api.openai.com/v1/chat/completions"

# OpenAI API key (set this as environment variable in production!)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_llm_response(prompt):
    """
    Interacts with the OpenAI API.
    """
    print(f"Received prompt: '{prompt}'")
    try:
        if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
            return "Please provide a valid OpenAI API key."

        payload = {
            "model": "gpt-4o-mini",   # ✅ Changed model to GPT-4
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
        
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Extract the text from the response
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        
        return "An unexpected response format was received from the LLM API."

    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        return "An error occurred while connecting to the LLM API. Please check your API key and network connection."
    except KeyError as e:
        return f"KeyError: Missing expected key in API response. Details: {e}"

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    API endpoint to handle chat requests.
    """
    try:
        data = request.get_json()
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
            
        llm_response = get_llm_response(user_message)
        
        return jsonify({"response": llm_response})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # To run, make sure you have Flask, flask-cors, and requests installed:
    # pip install Flask flask-cors requests
    # Then, run this script: python app.py
    app.run(debug=True, port=5000)
