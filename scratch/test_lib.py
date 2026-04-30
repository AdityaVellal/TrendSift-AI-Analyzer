from duckduckgo_search import DDGS

def test_ddgs(keyword):
    print(f"DEBUG: Searching with DDGS library for: '{keyword}'")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(keyword, max_results=3))
            print(f"DEBUG: Found {len(results)} results")
            for i, r in enumerate(results):
                print(f"DEBUG Result {i+1}: {r.get('title')} -> {r.get('href')}")
    except Exception as e:
        print(f"DEBUG Error: {e}")

if __name__ == "__main__":
    test_ddgs("UI design trends")
