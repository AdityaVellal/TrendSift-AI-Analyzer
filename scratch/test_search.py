import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_duckduckgo(keyword):
    print(f"DEBUG: Searching DuckDuckGo for: '{keyword}'")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": keyword},
            headers=headers,
            timeout=15
        )
        print(f"DEBUG: Response Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select(".result")
        print(f"DEBUG: Found {len(results)} raw result containers")
        
        for i, res in enumerate(results[:3]):
            title_tag = res.select_one(".result__a")
            if title_tag:
                print(f"DEBUG Result {i+1}: {title_tag.get_text()}")
            else:
                print(f"DEBUG Result {i+1}: Title tag not found")
                
        if not results:
            # If no results found, let's see a snippet of the HTML to see if we're blocked
            print("DEBUG: HTML Snippet (first 500 chars):")
            print(response.text[:500])

    except Exception as e:
        print(f"DEBUG Error: {e}")

if __name__ == "__main__":
    test_duckduckgo("UI design trends")
