import logging
import trafilatura
import requests
from bs4 import BeautifulSoup

class BrowserService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1"
        })

    def fetch_page(self, url: str) -> str:
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text_content = trafilatura.extract(downloaded, include_comments=False, include_tables=True)
                if text_content and len(text_content) > 200:
                    return f"Content of {url}:\n\n{text_content[:8000]}"

            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"
            
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "").strip()
            
            if not description:
                og_desc = soup.find("meta", attrs={"property": "og:description"})
                if og_desc:
                    description = og_desc.get("content", "").strip()

            headers = [h.get_text().strip() for h in soup.find_all(['h1', 'h2'])]
            headers_text = "\n".join(headers[:5])
            
            result = (
                f"Page Metadata for {url}:\n"
                f"Title: {title}\n"
                f"Description: {description}\n"
                f"Headers: {headers_text}\n"
            )
            
            if "TikTok" in title and "TikTok" in description and len(description) < 50:
                return "FAIL_PROTECTED_CONTENT"
                
            return result

        except Exception as e:
            logging.error(f"Browser error for {url}: {e}")
            return f"Error fetching {url}: {str(e)}"