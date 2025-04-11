import os
import requests
import datetime
from flask import request, jsonify
from transformers import T5Tokenizer, T5ForConditionalGeneration

GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

# Helper function
def fetch_commits_from_github(duration):
    api_url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        return None, response.status_code

    repos = response.json()
    commits = []
    current_date = datetime.datetime.utcnow()
    start_date = current_date - datetime.timedelta(days=duration)

    for repo in repos:
        repo_name = repo['name']
        owner = repo['owner']['login']
        commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits"

        params = {
            "since": start_date.isoformat()
        }

        repo_commits_response = requests.get(commits_url, headers=headers, params=params)

        if repo_commits_response.status_code == 200:
            repo_commits = repo_commits_response.json()
            for commit in repo_commits:
                commit_message = commit.get("commit", {}).get("message", "")
                commits.append({
                    "message": commit_message,
                    "repo": repo_name,
                    "date": commit["commit"]["committer"]["date"]
                })

    return commits, 200


# Controller function to handle commit fetching
def get_commits():
    duration = request.args.get("duration")

    if not duration:
        return jsonify({"error": "Duration is required"}), 400

    try:
        duration = int(duration)
    except ValueError:
        return jsonify({"error": "Duration must be a valid number"}), 400

    commits, status_code = fetch_commits_from_github(duration)

    if status_code != 200:
        return jsonify({"error": "Failed to fetch commits from GitHub"}), status_code

    if not commits:
        return jsonify({"message": "No commits found for the given duration."}), 200

    return jsonify(commits)


tokenizer = T5Tokenizer.from_pretrained("t5-large")
model = T5ForConditionalGeneration.from_pretrained("t5-large")


def generate_report():
    try:
        data = request.get_json()
        commits = data.get("commits")

        if not commits or not isinstance(commits, list):
            return jsonify({"error": "Commits must be a list"}), 400

        elaborated_commits = []

        for commit in commits:
            message = commit.get("message")
            repo = commit.get("repo")
            date = commit.get("date")

            if not message:
                continue

            # Custom prompt for T5 (T5 understands general instructions too)
            input_text = f"Explain the commit: {message}"
            input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=64, truncation=True)

            output_ids = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True)
            elaboration = tokenizer.decode(output_ids[0], skip_special_tokens=True)

            elaborated_commits.append({
                "original": message,
                "elaboration": elaboration,
                "repo": repo,
                "date": date
            })

        return jsonify({"elaborated_commits": elaborated_commits}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# current_dir = os.path.dirname(os.path.abspath(__file__))
# models_dir = os.path.join(current_dir, '..', 'models')
# models_dir = os.path.abspath(models_dir)
#
# tokenizer = T5Tokenizer.from_pretrained(models_dir)
# model = T5ForConditionalGeneration.from_pretrained(models_dir)
#
#
# def generate_report():
#     try:
#         # Get JSON payload
#         data = request.get_json()
#         commits = data.get("commits")
#
#         if not commits or not isinstance(commits, list):
#             return jsonify({"error": "Commits must be a list"}), 400
#
#         elaborated_commits = []
#
#         for commit in commits:
#             message = commit.get("message")
#             repo = commit.get("repo")
#             date = commit.get("date")
#
#             if not message:
#                 continue
#
#             input_text = f"Explain the work done in code based on the following commit message: {message}"
#             input_ids = tokenizer.encode(input_text, return_tensors="pt", max_length=64, truncation=True)
#
#             output_ids = model.generate(input_ids, max_length=128, num_beams=4, early_stopping=True)
#             elaboration = tokenizer.decode(output_ids[0], skip_special_tokens=True)
#
#             elaborated_commits.append({
#                 "original": message,
#                 "elaboration": elaboration,
#                 "repo": repo,
#                 "date": date
#             })
#
#         return jsonify({"elaborated_commits": elaborated_commits}), 200
#
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500
