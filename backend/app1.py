from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

# Initialize Flask application
app = Flask(__name__)
# Enable CORS to allow the React frontend to make requests
CORS(app)

# The base URL for the Gemini API
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"

# A free API key is required for this API. You can get one from Google AI Studio.
# For security, consider setting this as an environment variable in a production environment.
# For this example, you can paste your key directly.
# Replace "YOUR_API_KEY_HERE" with your actual API key.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_llm_response(prompt):
    """
    Interacts with the Gemini API.
    """
    print(f"Received prompt: '{prompt}'")
    try:
        if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
            return "Please provide a valid Gemini API key in the app.py file."

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        # The API key is passed as a query parameter in the URL
        response = requests.post(f"{API_URL}?key={GEMINI_API_KEY}", data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Extract the text from the response, handling potential nested structures
        if 'candidates' in data and len(data['candidates']) > 0:
            if 'parts' in data['candidates'][0]['content'] and len(data['candidates'][0]['content']['parts']) > 0:
                return data['candidates'][0]['content']['parts'][0]['text']
        
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
