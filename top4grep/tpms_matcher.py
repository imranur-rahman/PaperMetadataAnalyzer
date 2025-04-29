# tpms_matcher.py

import os
import requests
import sqlite3
import time
import math
from bs4 import BeautifulSoup
from markitdown import MarkItDown
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from datetime import datetime

# ----------- Config ----------- #
DBLP_SEARCH_API = "https://dblp.org/search/publ/api?q=author:{}&format=json"
DBLP_AUTHOR_BASE = "https://dblp.org"
DECAY_HALF_LIFE = 5  # years
MARKITDOWN = MarkItDown()
CURRENT_YEAR = datetime.now().year

# ----------- Utility Functions ----------- #
def exponential_decay_weight(year, current_year=CURRENT_YEAR, half_life=DECAY_HALF_LIFE):
    age = current_year - int(year)
    return math.exp(-math.log(2) * age / half_life)

def fetch_html(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

# ----------- Step 1: Crawl CFP Page ----------- #
def extract_pc_members(cfp_url):
    html = fetch_html(cfp_url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find link to Program Committee
    pc_link = None
    for a in soup.find_all("a"):
        if "committee" in a.text.lower() or "program" in a.text.lower():
            pc_link = a.get("href")
            if not pc_link.startswith("http"):
                pc_link = os.path.join(os.path.dirname(cfp_url), pc_link)
            break

    if pc_link:
        html = fetch_html(pc_link)
        soup = BeautifulSoup(html, 'html.parser')

    # Extract names from list/table
    pc_members = []
    for tag in soup.find_all(['li', 'p', 'td']):
        text = tag.get_text().strip()
        if len(text.split()) >= 2 and not text.lower().startswith("program"):
            pc_members.append(text)

    return pc_members

# ----------- Step 2: Fetch Publications ----------- #
def fetch_dblp_publications(author_name):
    query = author_name.replace(" ", "+")
    resp = requests.get(DBLP_SEARCH_API.format(query))
    if resp.status_code != 200:
        return []
    data = resp.json()
    hits = data.get("result", {}).get("hits", {}).get("hit", [])

    all_papers = []
    for hit in hits:
        info = hit.get("info", {})
        year = info.get("year")
        title = info.get("title")
        if year and title:
            all_papers.append((title, int(year)))
    return all_papers

# ----------- Step 3: Build Reviewer Profiles ----------- #
def build_reviewer_profiles(pc_list):
    profiles = {}
    for name in pc_list:
        papers = fetch_dblp_publications(name)
        if not papers:
            continue
        text_blob = []
        for title, year in papers:
            weight = exponential_decay_weight(year)
            text_blob.append((title, weight))
        profiles[name] = text_blob
        time.sleep(1)  # Avoid DBLP throttling
    return profiles

# ----------- Step 4: Parse Submission PDF ----------- #
def extract_text_from_pdf(pdf_path):
    result = MARKITDOWN.convert(pdf_path)
    return result.text_content

# ----------- Step 5: Build Corpus and Vectorize ----------- #
def vectorize_profiles_and_paper(profiles, paper_text):
    corpus = []
    reviewer_names = []
    for reviewer, weighted_titles in profiles.items():
        weighted_text = " ".join([title * round(weight * 10) for title, weight in weighted_titles])
        corpus.append(weighted_text)
        reviewer_names.append(reviewer)
    corpus.append(paper_text)

    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform(corpus)
    paper_vec = vectors[-1]
    reviewer_vecs = vectors[:-1]

    scores = cosine_similarity(paper_vec, reviewer_vecs)[0]
    ranked = sorted(zip(reviewer_names, scores), key=lambda x: x[1], reverse=True)
    return ranked

# ----------- Main Function ----------- #
def match_reviewers(cfp_url, submission_pdf):
    print("Extracting PC members...")
    pc_list = extract_pc_members(cfp_url)
    print(f"Found {len(pc_list)} PC members")

    print("Building reviewer profiles...")
    profiles = build_reviewer_profiles(pc_list)

    print("Parsing submission PDF...")
    paper_text = extract_text_from_pdf(submission_pdf)

    print("Computing similarity scores...")
    ranked_reviewers = vectorize_profiles_and_paper(profiles, paper_text)

    print("Top matches:")
    for i, (name, score) in enumerate(ranked_reviewers[:10], 1):
        print(f"{i}. {name} - Score: {score:.4f}")

    return ranked_reviewers

# Example usage:
# match_reviewers("https://conf.researchr.org/track/ase-2025/ase-2025-papers", "example_submission.pdf")
