import os
import requests
import datetime
from transformers import T5Tokenizer, T5ForConditionalGeneration
import spacy
import pytextrank
# import nltk
from flask import request, jsonify
from ..utils.text_analysis import build_style_profile, summarize_profile
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from collections import defaultdict, Counter
import re
import math
import pandas as pd
from nltk import word_tokenize
from nltk.util import ngrams

nlp = spacy.load("en_core_web_lg")
nlp.add_pipe("textrank")
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
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}]
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

        analysis = analyze(elaborated_commits)
        elaborated_commits = classification(elaborated_commits)
        summarization = summary(elaborated_commits)
        patterns_analysis = analyze_commit_patterns(elaborated_commits)

        return jsonify({
            "elaborated_commits": elaborated_commits,
            "summarization": summarization,
            "analysis": analysis,
            "patterns_analysis": patterns_analysis
        }), 200

    except Exception as e:
        # Log the full traceback of the exception
        # logging.error(f"Error occurred during report generation: {str(e)}")
        # logging.error(traceback.format_exc())  # Logs the full traceback

        # Return a more detailed error response
        return jsonify({"error": f"An error occurred during report generation: {str(e)}"}), 500

import traceback
# import logging
#
# logging.basicConfig(level=logging.ERROR)


def preprocess_text(text):
    text = text.lower()
    tokens = word_tokenize(text)
    tokens = [token for token in tokens if re.match(r'^[a-zA-Z_]+$', token)]
    return tokens


def get_ngrams(tokens, n):
    """Generate n-grams from token list"""
    return list(ngrams(tokens, n))


def calculate_pmi(corpus, ngram, ngram_counts):
    """Calculate Pointwise Mutual Information for an n-gram"""
    n = len(ngram)
    total_ngrams = len(ngram_counts)

    # Count of the n-gram
    ngram_count = ngram_counts.get(ngram, 0)
    if ngram_count == 0:
        return 0

    # Calculate P(ngram)
    p_ngram = ngram_count / total_ngrams

    # Calculate P(w1) * P(w2) * ... for each word in the n-gram
    p_product = 1
    for word in ngram:
        # Count how many times this word appears in any n-gram
        word_count = sum(count for ng, count in ngram_counts.items() if word in ng)
        p_word = word_count / total_ngrams
        p_product *= p_word

    if p_product == 0:
        return 0

    pmi = math.log2(p_ngram / p_product)
    return pmi


def analyze_commit_patterns(commits):
    """Analyze commit messages for n-grams and collocations"""
    try:
        # Extract all commit messages
        commit_messages = [item['original'] for item in commits]

        # Tokenize all messages
        all_tokens = []
        for message in commit_messages:
            all_tokens.extend(preprocess_text(message))

        # Generate bigrams and trigrams
        bigrams = get_ngrams(all_tokens, 2)
        trigrams = get_ngrams(all_tokens, 3)

        # Count frequencies
        bigram_counts = Counter(bigrams)
        trigram_counts = Counter(trigrams)

        # Calculate PMI for all bigrams
        bigram_pmi = {}
        for bigram in set(bigrams):
            bigram_pmi[bigram] = calculate_pmi(all_tokens, bigram, bigram_counts)

        # Create a DataFrame of bigrams with counts and PMI
        bigram_data = []
        for bigram, count in bigram_counts.most_common():
            pmi = bigram_pmi.get(bigram, 0)
            bigram_data.append({
                'bigram': ' '.join(bigram),
                'count': count,
                'pmi': pmi
            })

        bigram_df = pd.DataFrame(bigram_data)

        # Convert to dictionary for JSON serialization
        patterns_analysis = {
            'top_bigrams': bigram_df.sort_values('pmi', ascending=False).head(10).to_dict('records'),
            'top_trigrams': [{'trigram': ' '.join(t), 'count': c} for t, c in trigram_counts.most_common(5)]
        }

        return patterns_analysis

    except Exception as e:
        logging.error(f"Error in analyze_commit_patterns: {str(e)}")
        return {"error": str(e)}


def classification(elaborated_commit):
    texts = [entry["elaboration"].strip() for entry in elaborated_commit]

    # Vectorize with TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(texts)

    # KMeans Clustering
    kmeans = KMeans(n_clusters=4, random_state=42)
    labels = kmeans.fit_predict(X)

    # Define category mappings
    label_map = {
        0: "New Features",
        1: "Testing/Debugging",
        2: "Initializations",
        3: "Maintenance/Miscellaneous"
    }

    for i, entry in enumerate(elaborated_commit):
        entry["category"] = label_map[labels[i]]

    return elaborated_commit


def summary(elaborated_commits):
    combined_text = " ".join(entry["elaboration"].strip() for entry in elaborated_commits)
    doc = nlp(combined_text)
    summary_sentences = [sent.text.strip() for sent in doc._.textrank.summary(limit_phrases=10, limit_sentences=10)]
    return summary_sentences


def analyze(elaborated_commits):
    profile_data = build_style_profile(elaborated_commits)

    summary_result = {}
    for dev in profile_data:
        metric_map = defaultdict(list)
        for i in range(len(profile_data[dev])):
            for key in ['length', 'noun_ratio', 'verb_ratio', 'polarity', 'subjectivity', 'type_token_ratio']:
                metric_map[key].append(profile_data[dev][i])
        summary_result[dev] = summarize_profile(dev, metric_map)

    return summary_result

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
