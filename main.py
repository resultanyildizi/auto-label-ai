
import os
import jwt
import time
import requests
import dotenv
from flask import Flask, request, jsonify

dotenv.load_dotenv()

# Replace with your GitHub App credentials
PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY", "none")  # PEM private key string
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "none")  # Github client id

app = Flask(__name__)

# Function to generate a JWT for GitHub App
def generate_jwt():
    current_time = int(time.time())
    payload = {
        "iat": current_time,  # Issued at time
        "exp": current_time + 600,  # Token expires in 10 minutes
        "iss": CLIENT_ID, # Github Client Id
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return token

# Function to get the installation access token
def get_installation_token(installation_id):
    jwt_token = generate_jwt()
    headers = {"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    response = requests.post(url, headers=headers)
    if response.status_code == 201:
        return response.json()["token"]
    else:
        raise Exception(f"Failed to fetch installation token: {response.text}")

# Webhook to listen for issue creation
@app.route("/webhook", methods=["POST"])
def webhook():
    event = request.headers.get("X-GitHub-Event", "")
    payload = request.json 
    if payload is None:
        return jsonify({""})

    if event == "issues" and payload["action"] == "opened":
        issue = payload["issue"]
        repository = payload["repository"]
        issue_title = issue["title"]
        issue_url = issue["html_url"]
        repo_name = repository["full_name"]

        print(f"Issue created in {repo_name}: {issue_title} - {issue_url}")

        # You can respond to the issue here using the installation token
        installation_id = payload["installation"]["id"]
        token = get_installation_token(installation_id)
        respond_to_issue(issue_url, token)

    return jsonify({"status": "success"})

# Function to respond to the issue
def respond_to_issue(issue_url, token):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    comment_url = f"{issue_url}/comments"
    data = {"body": "Thank you for opening this issue. We will look into it!"}
    response = requests.post(comment_url, json=data, headers=headers)
    if response.status_code == 201:
        print("Successfully posted a comment.")
    else:
        print(f"Failed to post a comment: {response.text}")

if __name__ == "__main__":
    app.run(port=5000)


