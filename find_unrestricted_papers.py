import requests
import os
import dotenv

def search_papers(query, api_key, limit=10):
    result = requests.get(
        'https://api.semanticscholar.org/graph/v1/paper/search',
        headers={'x-api-key': api_key},
        params={'query': query, 'limit': limit, 'fields': 'title,paperId'}
    )
    if result.status_code != 200:
        print(f"search failed: {result.status_code} {result.text}")
        return []

    return result.json()['data']

def has_references(paper_id, api_key):
    result = requests.get(
        f'https://api.semanticscholar.org/graph/v1/paper/{paper_id}',
        headers={'x-api-key': api_key},
        params={'fields': 'title,references'}
    )
    if result.status_code != 200:
        print(f"  request failed: {result.status_code} {result.text}")
        return False

    data = result.json()
    return data['references'] is not None

import time

def main():
    dotenv.load_dotenv()
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

    query = input("Enter a search topic: ").strip()
    if not query:
        print("No query entered, exiting.")
        return

    candidates = search_papers(query, api_key)
    time.sleep(1.1)

    for paper in candidates:
        if has_references(paper['paperId'], api_key):
            print(f"GOOD SEED: {paper['title']} ({paper['paperId']})")
        else:
            print(f"restricted: {paper['title']}")
        time.sleep(1.1)

if __name__ == "__main__":
    main()