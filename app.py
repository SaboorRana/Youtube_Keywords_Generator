from flask import Flask, render_template, request, jsonify, send_from_directory
import yake
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from bs4 import BeautifulSoup
from itertools import permutations
import os
from flask_cors import CORS
import traceback

nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
os.makedirs(nltk_data_path, exist_ok=True)
nltk.data.path.append(nltk_data_path)

# Download missing NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', download_dir=nltk_data_path)
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', download_dir=nltk_data_path)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', download_dir=nltk_data_path)
# nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
# nltk.data.path.insert(0, nltk_data_path)
# print("Using NLTK data directory:", nltk_data_path)

def fetch_related_searches(query):
    """Fetches related search terms from Google/Bing"""
    try:
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        suggestions = [s.text for s in soup.find_all("p") if len(s.text.split()) > 2][:10]
        return suggestions
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return []

def get_relevant_synonyms(word):
    """Fetch synonyms while avoiding irrelevant words"""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonym = lemma.name().replace("_", " ")
            if synonym.lower() != word.lower():
                synonyms.add(synonym)
    return list(synonyms)[:2]

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
    return title_keywords + synonyms + general_keywords

def generate_keywords(title, description=""):
    """Generates structured, high-quality keywords"""
    stop_words = set(stopwords.words("english"))
    title_tokens = [word.lower() for word in word_tokenize(title) if word.isalnum() and word.lower() not in stop_words]

    synonyms_map = {word: get_relevant_synonyms(word) for word in title_tokens}
    enriched_keywords = []
    for word, synonyms in synonyms_map.items():
        for synonym in synonyms:
            enriched_keywords.append(synonym)
            enriched_keywords.extend([" ".join(perm) for perm in permutations([synonym] + title_tokens, 2)][:3])

    text_to_analyze = title + " " + description
    kw_extractor = yake.KeywordExtractor(n=3, top=30)
    yake_keywords = [word for word, _ in kw_extractor.extract_keywords(text_to_analyze)]

    title_bigrams = [" ".join(title_tokens[i:i+2]) for i in range(len(title_tokens)-1)]
    title_trigrams = [" ".join(title_tokens[i:i+3]) for i in range(len(title_tokens)-2)]

    related_searches = fetch_related_searches(title)
    negation_keywords = intelligent_negations(title)

    title_keywords = title_trigrams + title_bigrams + title_tokens
    synonym_keywords = enriched_keywords[:10]
    general_keywords = yake_keywords + negation_keywords + related_searches

    structured_keywords = refine_keywords(title_keywords, synonym_keywords, general_keywords)[:30]
    return structured_keywords

# Create the Flask app
app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET", "POST"])
def home():
    print("Received Request:", request.method)
    if request.method == "POST":
        try:
            data = request.get_json() or {}
            title = data.get("title", "").strip()
            description = data.get("description", "").strip()
            
            if not title:
                print("⚠️ Missing title!")
                return jsonify({"error": "Title is required."}), 400
            
            generated_keywords = generate_keywords(title, description)
            print("Generated Keywords:", generated_keywords[:30])
            return jsonify({"keywords": generated_keywords[:30]})
        except Exception as e:
            error_details = traceback.format_exc()
            print("❌ Error in POST request:")
            print(error_details)
            return jsonify({"error": "Server error", "message": str(e)}), 500
    return render_template("index.html")

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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.png')
def favicon_png():
    return send_from_directory('static', 'favicon.png', mimetype='image/png')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, host="0.0.0.0")









# import os
# import shutil
# import nltk

# # Set the directory for nltk_data (adjust as needed)
# nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')

# def ensure_resource(resource_path, package_name):
#     """
#     Remove existing resource and download fresh copy.
#     resource_path: Path relative to nltk_data_dir (e.g., 'corpora/wordnet')
#     package_name: Package name to download (e.g., 'wordnet')
#     """
#     full_path = os.path.join(nltk_data_dir, resource_path)
#     if os.path.exists(full_path):
#         print(f"Removing existing {package_name} data at {full_path}")
#         shutil.rmtree(full_path)
#     print(f"Downloading {package_name}...")
#     nltk.download(package_name, download_dir=nltk_data_dir)
#     print(f"{package_name} downloaded.")

# # Ensure nltk_data_dir exists
# if not os.path.exists(nltk_data_dir):
#     os.makedirs(nltk_data_dir)

# # List of required resources with their relative paths and package names
# resources = [
#     ('tokenizers/punkt', 'punkt'),
#     ('corpora/stopwords', 'stopwords'),
#     ('corpora/wordnet', 'wordnet'),
# ]

# for rel_path, pkg in resources:
#     ensure_resource(rel_path, pkg)


# from flask import Flask, render_template, request, jsonify, send_from_directory
# import yake
# import requests
# import nltk
# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords, wordnet
# from bs4 import BeautifulSoup
# from itertools import permutations
# import os
# from flask_cors import CORS
# # Removed dotenv import and load_dotenv() since not needed in production

# # Append custom nltk_data path (if used)
# nltk_data_path = os.path.join(os.path.dirname(__file__), "nltk_data")
# nltk.data.path.append(nltk_data_path)

# def fetch_related_searches(query):
#     """Fetches related search terms from Google/Bing"""
#     try:
#         url = f"https://www.google.com/search?q={query}"
#         response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
#         soup = BeautifulSoup(response.text, "html.parser")
#         suggestions = [s.text for s in soup.find_all("p") if len(s.text.split()) > 2][:10]
#         return suggestions
#     except Exception:
#         return []

# def get_relevant_synonyms(word):
#     """Fetch synonyms while avoiding irrelevant words"""
#     synonyms = set()
#     for syn in wordnet.synsets(word):
#         for lemma in syn.lemmas():
#             synonym = lemma.name().replace("_", " ")
#             if synonym.lower() != word.lower():
#                 synonyms.add(synonym)
#     return list(synonyms)[:2]

# def intelligent_negations(title):
#     """Generate intelligent negative keywords based on the title"""
#     negations_map = {
#         "build": ["common mistakes in app development"],
#         "ai": ["non-AI app ideas"],
#         "app": ["how not to build an app"]
#     }
#     title_words = title.lower().split()
#     relevant_negations = [phrase for word in title_words for phrase in negations_map.get(word, [])]
#     return relevant_negations

# def refine_keywords(title_keywords, synonyms, general_keywords):
#     """Reorders keywords to ensure relevant ones come first, synonyms in the middle, and single words last"""
#     return title_keywords + synonyms + general_keywords

# def generate_keywords(title, description=""):
#     """Generates structured, high-quality keywords"""
#     stop_words = set(stopwords.words("english"))
#     title_tokens = [word.lower() for word in word_tokenize(title) if word.isalnum() and word.lower() not in stop_words]

#     synonyms_map = {word: get_relevant_synonyms(word) for word in title_tokens}
#     enriched_keywords = []
#     for word, synonyms in synonyms_map.items():
#         for synonym in synonyms:
#             enriched_keywords.append(synonym)
#             enriched_keywords.extend([" ".join(perm) for perm in permutations([synonym] + title_tokens, 2)][:3])

#     text_to_analyze = title + " " + description
#     kw_extractor = yake.KeywordExtractor(n=3, top=30)
#     yake_keywords = [word for word, _ in kw_extractor.extract_keywords(text_to_analyze)]

#     title_bigrams = [" ".join(title_tokens[i:i+2]) for i in range(len(title_tokens)-1)]
#     title_trigrams = [" ".join(title_tokens[i:i+3]) for i in range(len(title_tokens)-2)]

#     related_searches = fetch_related_searches(title)
#     negation_keywords = intelligent_negations(title)

#     title_keywords = title_trigrams + title_bigrams + title_tokens
#     synonym_keywords = enriched_keywords[:10]
#     general_keywords = yake_keywords + negation_keywords + related_searches

#     structured_keywords = refine_keywords(title_keywords, synonym_keywords, general_keywords)[:30]
#     return structured_keywords

# app = Flask(__name__)
# CORS(app)

# # @app.route("/", methods=["GET", "POST"])
# # def home():
# #     print("Received Request:", request.method)
# #     if request.method == "POST":
# #         data = request.get_json() or {}
# #         title = data.get("title", "").strip()
# #         description = data.get("description", "").strip()
        
# #         if title:
# #             generated_keywords = generate_keywords(title, description)
# #             print("Generated Keywords:", generated_keywords[:30])
# #             return jsonify({"keywords": generated_keywords[:30]})
# #         else:
# #             print("⚠️ Missing title!")
# #             return jsonify({"error": "Title is required."}), 400
# #     return render_template("index.html")
# @app.route("/", methods=["GET", "POST"])
# def home():
#     print("Received Request:", request.method)
#     if request.method == "POST":
#         try:
#             data = request.get_json() or {}
#             title = data.get("title", "").strip()
#             description = data.get("description", "").strip()
            
#             if not title:
#                 print("⚠️ Missing title!")
#                 return jsonify({"error": "Title is required."}), 400
            
#             generated_keywords = generate_keywords(title, description)
#             print("Generated Keywords:", generated_keywords[:30])
#             return jsonify({"keywords": generated_keywords[:30]})
#         except Exception as e:
#             import traceback
#             error_details = traceback.format_exc()
#             # Log the full error details to the server log:
#             print("❌ Error in POST request:")
#             print(error_details)
#             # Optionally, in debug mode, you can return the error message (not recommended in production)
#             return jsonify({"error": "Server error", "message": str(e)}), 500
#     else:
#         return render_template("index.html")

# @app.route("/about_us")
# def about_us():
#     return render_template("about_us.html")

# @app.route("/blog")
# def blog():
#     return render_template("blog.html")

# @app.route("/contact")
# def contact():
#     return render_template("contact.html")

# @app.route("/privacy_policy")
# def privacy_policy():
#     return render_template("privacy_policy.html")

# @app.route("/terms_of_service")
# def terms_of_service():
#     return render_template("terms_of_service.html")

# @app.route('/favicon.ico')
# def favicon():
#     return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# @app.route('/favicon.png')
# def favicon_png():
#     return send_from_directory('static', 'favicon.png', mimetype='image/png')

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(port=port, host="0.0.0.0")
