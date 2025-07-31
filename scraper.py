import os
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.warhammercommunity.com"
PDF_DIR = "pdfs"

os.makedirs(PDF_DIR, exist_ok=True)

def fetch_pdfs():
    response = requests.get(BASE_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.pdf')]

    for link in pdf_links:
        download_pdf(link)

def download_pdf(url):
    filename = os.path.join(PDF_DIR, os.path.basename(url))
    if not os.path.exists(filename):
        print(f"Downloading {url}...")
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        print(f"{filename} already exists.")

if __name__ == "__main__":
    fetch_pdfs()
