from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
import requests

app = Flask(__name__)

# Założenie że MongoDB jest pod nazwą "mongo"
client = MongoClient("mongodb://mongo:27017/")
db = client["webscraper"]
col = db["results"]

#strona główna z formularzem
@app.route("/",methods=["GET","POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                res = requests.post("http://silnik:8000/scrape", json={"url": url})
            except Exception as e:
                print("[ERROR] Nie udało się połączyć z silnikiem: ", e)

        return redirect("/")
    
    results = list(col.find().sort("timestamp", -1).limit(10))
    return render_template("index.html", results=results)

# wyświetlanie szczegółów rekordu
@app.route("/details/<id>")
def details(id):
    from bson import ObjectId
    record = col.find_one({"id":ObjectId(id)})
    return render_template("details.html", record=record)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)