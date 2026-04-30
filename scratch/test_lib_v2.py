from duckduckgo_search import DDGS

def test_ddgs(keyword):
    print(f"DEBUG: Searching with NEW DDGS library for: '{keyword}'")
    try:
        with DDGS() as ddgs:
            # The text() method in new versions of DDGS is very robust
            results = ddgs.text(keyword, max_results=3)
            print(f"DEBUG: Found {len(results)} results")
            for i, r in enumerate(results):
                print(f"DEBUG Result {i+1}: {r.get('title')} -> {r.get('href')}")
    except Exception as e:
        print(f"DEBUG Error: {e}")

if __name__ == "__main__":
    test_ddgs("artificial intelligence")
