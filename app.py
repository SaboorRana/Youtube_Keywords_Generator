from flask import Flask, render_template, request
import yake
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from bs4 import BeautifulSoup
from itertools import permutations
import os


nltk.download('punkt', download_dir='nltk_data')
nltk.data.path.append(os.path.join(os.path.dirname(__file__), "nltk_data"))
from nltk.tokenize import word_tokenize
nltk.download("stopwords")
nltk.download("wordnet")

app = Flask(__name__)

def fetch_related_searches(query):
    """Fetches related search terms from Google/Bing"""
    try:
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        suggestions = [s.text for s in soup.find_all("p") if len(s.text.split()) > 2][:10]  # Extract meaningful phrases
        return suggestions
    except Exception:
        return []

def get_relevant_synonyms(word):
    """Fetch synonyms while avoiding irrelevant words"""
    synonyms = set()
    
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace("_", " ")
            if synonym.lower() != word.lower():
                synonyms.add(synonym)
    
    return list(synonyms)[:2]  # Select only the best 2 synonyms

def intelligent_negations(title):
    """Generate intelligent negative keywords based on the title"""
    negations_map = {
        "build": ["common mistakes in app development"],
        "ai": ["non-AI app ideas"],
        "app": ["how not to build an app"]
    }
    
    title_words = title.lower().split()
    relevant_negations = [phrase for word in title_words for phrase in negations_map.get(word, [])]
    
    return relevant_negations

def refine_keywords(title_keywords, synonyms, general_keywords):
    """Reorders keywords to ensure relevant ones come first, synonyms in the middle, and single words last"""
    return title_keywords + synonyms + general_keywords  # Title-related → Synonyms → General single words

def generate_keywords(title, description=""):
    """Generates structured, high-quality keywords"""
    stop_words = set(stopwords.words("english"))
    
    title_tokens = [word.lower() for word in word_tokenize(title) if word.isalnum() and word.lower() not in stop_words]

    # Generate synonyms for important words
    synonyms_map = {word: get_relevant_synonyms(word) for word in title_tokens}
    
    # Generate variations using permutations
    enriched_keywords = []
    for word, synonyms in synonyms_map.items():
        for synonym in synonyms:
            enriched_keywords.append(synonym)
            enriched_keywords.extend([" ".join(perm) for perm in permutations([synonym] + title_tokens, 2)][:3])  

    # Extract keywords using YAKE
    text_to_analyze = title + " " + description
    kw_extractor = yake.KeywordExtractor(n=3, top=30)
    yake_keywords = [word for word, _ in kw_extractor.extract_keywords(text_to_analyze)]

    # Generate bigrams & trigrams from title
    title_bigrams = [" ".join(title_tokens[i:i+2]) for i in range(len(title_tokens)-1)]
    title_trigrams = [" ".join(title_tokens[i:i+3]) for i in range(len(title_tokens)-2)]

    # Fetch related searches
    related_searches = fetch_related_searches(title)

    # Include intelligent negations
    negation_keywords = intelligent_negations(title)

    # Separate keyword categories
    title_keywords = title_trigrams + title_bigrams + title_tokens
    synonym_keywords = enriched_keywords[:10]  # Limit synonym-based words
    general_keywords = yake_keywords + negation_keywords + related_searches

    # Reorder keywords for better search ranking
    structured_keywords = refine_keywords(title_keywords, synonym_keywords, general_keywords)[:30]

    return structured_keywords

@app.route("/", methods=["GET", "POST"])
def index():
    keywords = []

    if request.method == "POST":
        data = request.get_json()
        title = data.get("title", "")
        description = data.get("description", "")

        if title:
            generated_keywords = generate_keywords(title, description)
            return {"keywords": generated_keywords[:30]}  # Return JSON

    return render_template("index.html", keywords=keywords)
@app.route("/about_us")
def about_us():
    return render_template("about_us.html")
@app.route("/blog")
def blog():
    return render_template("blog.html")
@app.route("/contact")
def contact():
    return render_template("contact.html")
@app.route("/privacy_policy")
def privacy_policy():
    return render_template("privacy_policy.html")
@app.route("/terms_of_service")
def terms_of_service():
    return render_template("terms_of_service.html")

if __name__ == "__main__":
    app.run(debug=True)