import os
import requests
import datetime
from flask import request, jsonify
from transformers import T5Tokenizer, T5ForConditionalGeneration

GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")


def fetch_commits_from_github(duration, username):
    api_url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        return None, response.status_code

    repos = response.json()
    commits = []
    current_date = datetime.datetime.utcnow()
    start_date = current_date - datetime.timedelta(days=duration)

    for repo in repos:
        repo_name = repo["name"]
        owner = repo["owner"]["login"]
        commits_url = f"https://api.github.com/repos/{owner}/{repo_name}/commits"
        languages_url = f"https://api.github.com/repos/{owner}/{repo_name}/languages"

        # Fetch language breakdown
        lang_response = requests.get(languages_url, headers=headers)
        lang_data = {}
        if lang_response.status_code == 200:
            lang_data = lang_response.json()
            total_bytes = sum(lang_data.values())
            for lang in lang_data:
                lang_data[lang] = round((lang_data[lang] / total_bytes) * 100, 2)  # percentage

        params = {
            "since": start_date.isoformat() + "Z",
            "author": username
        }

        repo_commits_response = requests.get(commits_url, headers=headers, params=params)

        if repo_commits_response.status_code == 200:
            repo_commits = repo_commits_response.json()
            for commit in repo_commits:
                commit_message = commit.get("commit", {}).get("message", "")
                commit_date = commit.get("commit", {}).get("committer", {}).get("date", "")
                commit_url = commit.get("url")

                loc_additions = 0
                loc_deletions = 0
                commit_detail_response = requests.get(commit_url, headers=headers)
                if commit_detail_response.status_code == 200:
                    commit_detail = commit_detail_response.json()
                    stats = commit_detail.get("stats", {})
                    loc_additions = stats.get("additions", 0)
                    loc_deletions = stats.get("deletions", 0)

                # LOC distribution across languages (estimated, not exact per commit)
                loc_per_language = {}
                for lang, percent in lang_data.items():
                    loc_per_language[lang] = {
                        "estimated_additions": round((percent / 100) * loc_additions),
                        "estimated_deletions": round((percent / 100) * loc_deletions)
                    }

                commits.append({
                    "message": commit_message,
                    "repo": repo_name,
                    "date": commit_date,
                    "additions": loc_additions,
                    "deletions": loc_deletions,
                    "language_distribution": lang_data,  # percentages
                    "loc_per_language": loc_per_language  # estimated LOC
                })

    return commits, 200


# Controller function to handle commit fetching
def get_commits():
    duration = request.args.get("duration")
    user = request.args.get("username")

    if not duration:
        return jsonify({"error": "Duration is required"}), 400

    try:
        duration = int(duration)
    except ValueError:
        return jsonify({"error": "Duration must be a valid number"}), 400

    commits, status_code = fetch_commits_from_github(duration, user)

    if status_code != 200:
        return jsonify({"error": "Failed to fetch commits from GitHub"}), status_code

    if not commits:
        return jsonify({"message": "No commits found for the given duration."}), 200

    return jsonify(commits)


GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
API_KEY = os.getenv("T5-API")


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
            additions = commit.get("additions")
            deletions = commit.get("deletions")
            lang_dist = commit.get("language_distribution", {})
            loc_per_lang = commit.get("loc_per_language", {})
            if not message:
                continue

            prompt = f"Explain the commit message in 40 words: {message}"

            response = requests.post(
                f"{GEMINI_API_URL}?key={API_KEY}",
                json={
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        }
                    ]
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                res_json = response.json()
                elaboration = (
                    res_json.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "No explanation available.")
                )
            else:
                elaboration = f"Error: {response.status_code}, Unable to explain message."

            elaborated_commits.append({
                "original": message,
                "elaboration": elaboration,
                "repo": repo,
                "date": date,
                "additions": additions,
                "deletions": deletions,
                "language_distribution": lang_dist,
                "loc_per_language": loc_per_lang
            })
        # summarization = summary(elaborated_commits)
        return jsonify({
            "elaborated_commits": elaborated_commits
        }), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def summary(elaborated_commits):
    try:
        if not elaborated_commits or not isinstance(elaborated_commits, list):
            return jsonify({"error": "Elaborated commits must be a list"}), 400

        commits_text = ""
        for idx, commit in enumerate(elaborated_commits, 1):
            commits_text += (
                f"Commit {idx}:\n"
                f"Repository: {commit.get('repo')}\n"
                f"Date: {commit.get('date')}\n"
                f"Elaboration: {commit.get('elaboration')}\n"
                f"Additions: {commit.get('additions')}, Deletions: {commit.get('deletions')}\n"
                f"Languages Used: {commit.get('language_distribution')}\n"
                f"LOC Per Language: {commit.get('loc_per_language')}\n\n"
            )

        prompt = (
            "You are an assistant summarizing commit activity from multiple repositories. "
            "Based on the following elaborated commits, give an overall summary grouped by categories like: "
            "features added, bugs fixed, refactoring, documentation, tests, etc. Be concise but informative.\n\n"
            + commits_text
        )

        # Send the summary prompt to Gemini
        response = requests.post(
            f"{GEMINI_API_URL}?key={API_KEY}",
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ]
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            res_json = response.json()
            summary_text = (
                res_json.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "No summary available.")
            )
        else:
            summary_text = f"Error: {response.status_code}, Unable to generate summary."

        return jsonify({"summary": summary_text}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

#
# def generate_report():
#     try:
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
#             # Custom prompt for T5 (T5 understands general instructions too)
#             input_text = f"Explain the commit: {message}"
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


# current_dir = os.path.dirname(os.path.abspath(__file__))
# models_dir = os.path.join(current_dir, '..', 'models')
# models_dir = os.path.abspath(models_dir)
#
# tokenizer = T5Tokenizer.from_pretrained(models_dir)
# model = T5ForConditionalGeneration.from_pretrained(models_dir)

tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5ForConditionalGeneration.from_pretrained("t5-small")

def generation_report():
    try:
        # Get JSON payload
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

            input_text = f"Explain the work done in code based on the following commit message: {message}"
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
