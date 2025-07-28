import requests
from bs4 import BeautifulSoup

def RealtimeSearchEngine(query):
    print(f"DEBUG: Performing real-time search for query: '{query}'")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        url = f"https://www.google.com/search?q={query}"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        selectors = [
            "div.BNeawe",
            "div.V3yFp",
            "div.LGOjhe",
            "div.d6DCz",
            "span.hgKElc",
            "div.IZ6rdc",
            "div.kno-rdesc > span",
            "div.liYKde > div.ifM9O",
            "div.webanswers-webanswers_table__webanswers-table-wrapper",
        ]

        result_text = None
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                result_text = element.get_text(strip=True, separator=' ')
                print(f"DEBUG: Found result with selector '{selector}'.")
                break
        
        if not result_text:
            print("DEBUG: No direct answer box found. Falling back to general search result snippets.")
            general_snippet_selectors = [
                "div.VwiC3b > span.LrzXr",
                "div.s3v9rd > span",
                "span.st",
            ]
            for selector in general_snippet_selectors:
                snippet_element = soup.select_one(selector)
                if snippet_element:
                    result_text = snippet_element.get_text(strip=True, separator=' ')
                    print(f"DEBUG: Found result from a general search snippet with selector '{selector}'.")
                    break

        if result_text:
            return result_text
        else:
            print("WARNING: Could not find a suitable result snippet after trying multiple selectors.")
            return "I could not find a clear answer for that query from Google."

    except requests.exceptions.RequestException as e:
        print(f"ERROR: A network error occurred during search: {e}")
        return "I am having trouble connecting to the internet to perform that search."
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during search: {e}")
        return f"An unexpected error occurred while processing your search: {str(e)}"