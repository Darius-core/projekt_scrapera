import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from multiprocessing import Pool, cpu_count
from pymongo import MongoClient
from datetime import datetime

# ========== Funkcje wyciągające z BeautifulSoup

def extract_emails(text):
    pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+')
    return re.findall(pattern, text)

def extract_phones(text):
    return re.findall(r"\+?\d[\d\s\-\(\)]{7,}\d",text)

def extract_addresses(text):
    pattern = re.compile(
        r'(?P<street>(ul\.|al\.|Al\.|plac|Plac)?\s?[A-ZŁŚĆŹŻ][a-ząćęłńóśźżA-Z\s\-]+)\s(?P<number>\d+[a-zA-Z]?(/\d+)?),?\s+(?P<postcode>\d{2}-\d{3})\s+(?P<city>[A-ZŁŚĆŹŻ][a-ząćęłńóśźżA-Z\s\-]+)'
    )

    matches = []
    for match in pattern.finditer(text):
        street = match.group("street")
        number = match.group("number")
        postcode = match.group("postcode")
        city = match.group("city")
        full = f"{street} {number}, {postcode} {city}"
        matches.append(full)
    return matches

def extract_images(soup, base_url):
    return [urljoin(base_url, img['src']) for img in soup.find_all("img",src=True)]

# ========== Główna Funkcja Asyncio

async def fetch_and_parse(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()

            data = {
                "url": url,
                "emails": extract_emails(text),
                "phones": extract_phones(text),
                "addresses": extract_addresses(text),
                "images": extract_images(soup, url),
                "timestamp": datetime.utcnow().isoformat()
            }
            return data
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        return None
    
async def scraper_async(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_parse(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return[r for r in results if r]
    
# ========== Multiprocessing

def scraper_worker(urls):
    return asyncio.run(scraper_async(urls))

# ========== Baza Danych MongoDB

def save_to_mongo(docs):
    client = MongoClient("mongodb://mongo:27017/") #link do łączenia się z bazą
    db = client["webscraper"]
    col = db["results"]
    col.insert_many(docs)

# ========== MAIN

def run_scraper(all_urls, chunk_size=10):
    num_workers = min(cpu_count(), len(all_urls) // chunk_size + 1)
    chunks = [all_urls[i: i+chunk_size] for i in range(0, len(all_urls), chunk_size)]

    with Pool(processes=num_workers) as pool:
        all_results = pool.map(scraper_worker, chunks)

    flat_results = [item for sublist in all_results for item in sublist]
    save_to_mongo(flat_results)
    print(f"[INFO] Saved {len(flat_results)} results to MongoDB")


if __name__ == "__main__":
    test_urls = [
        "https://www.exaple.com",
        "https://www.python.org",
        "https://www.djangoproject.com"
    ]
    run_scraper(test_urls)
