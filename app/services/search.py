import logging
from duckduckgo_search import DDGS

class SearchService:
    def __init__(self):
        self.max_results = 3

    def search(self, query: str) -> str:
        try:
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(query, max_results=self.max_results)
                for r in ddgs_gen:
                    title = r.get('title', 'No Title')
                    body = r.get('body', 'No Content')
                    href = r.get('href', '#')
                    results.append(f"Title: {title}\nLink: {href}\nContent: {body}")
            
            if not results:
                return "Поиск не дал результатов."
                
            return "\n\n".join(results)
            
        except Exception as e:
            logging.error(f"Search error: {e}")
            return f"Ошибка при выполнении поиска: {str(e)}"