from flask import Flask, request, jsonify
from scraper import run_scraper

app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Brak URL-a"}), 400
    
    run_scraper([url])
    return jsonify({"status": "OK", "url": url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)