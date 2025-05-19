from collections import defaultdict
import nltk
from textblob import TextBlob
import numpy as np


def analyze_commit_text(text):
    tokens = nltk.word_tokenize(text)
    tags = nltk.pos_tag(tokens)

    noun_count = sum(1 for word, tag in tags if tag.startswith('NN'))
    verb_count = sum(1 for word, tag in tags if tag.startswith('VB'))

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    unique_tokens = len(set(tokens))
    total_tokens = len(tokens)
    type_token_ratio = unique_tokens / total_tokens if total_tokens else 0

    return {
        'length': total_tokens,
        'noun_ratio': noun_count / total_tokens if total_tokens else 0,
        'verb_ratio': verb_count / total_tokens if total_tokens else 0,
        'polarity': polarity,
        'subjectivity': subjectivity,
        'type_token_ratio': type_token_ratio
    }


def build_style_profile(json_data):
    style_profile = defaultdict(list)

    for entry in json_data:
        dev = entry.get("repo")
        text = entry.get("original", "") + " " + entry.get("elaboration", "")
        result = analyze_commit_text(text)

        for key, value in result.items():
            style_profile[dev].append(value)

    return style_profile


def summarize_profile(dev, metrics):
    avg_length = np.mean(metrics['length'])
    noun_ratio = np.mean(metrics['noun_ratio'])
    verb_ratio = np.mean(metrics['verb_ratio'])
    polarity = np.mean(metrics['polarity'])
    subjectivity = np.mean(metrics['subjectivity'])
    ttr = np.mean(metrics['type_token_ratio'])

    sentiment = "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"

    style = f"{dev} commits tend to be written in "
    style += "brief" if avg_length < 7 else "detail" + ". "
    style += "action-oriented" if verb_ratio > noun_ratio else "object-focused" + ". "
    style += f"Commit messages with a generally {sentiment} tone. "
    style += f"The vocabulary used is {'diverse' if ttr > 0.3 else 'limited'}."
    style += f"It is written in a {'subjective' if subjectivity > 0.5 else 'objective'} manner."

    return style
