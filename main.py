import time

import requests
import os
import dotenv

DEPTH_LIMIT = 10
NODE_CAP = 50

def clean_paper(raw_paper_dict):
    paperId = raw_paper_dict['paperId']
    title = raw_paper_dict['title']
    reference_ids = raw_paper_dict['references']

    clean_references = []

    if reference_ids is None:
        reference_ids = []
    else:
        for reference_id in reference_ids:
            if reference_id["paperId"] is not None:
                clean_references.append(reference_id["paperId"])

    return {"paperId": paperId, "title": title, "references": clean_references}

def fetch_batch(paper_ids, api_key):
    batch = []
    for startIndex in range(0, len(paper_ids), 500):
        chunk = paper_ids[startIndex:startIndex + 500]

        result = requests.post('https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,references.title,references.paperId', headers={'x-api-key': api_key}, json={'ids': chunk})
        print(result.status_code)
        if result.status_code == 200:
            # print(result.json())
            raw_paper_dict = result.json()
            for paper_dict in raw_paper_dict:
                batch.append(clean_paper(paper_dict))
        else:
            print(result.text)
        time.sleep(1.1)

    return batch

def bfs(seed_id, api_key):
    visited = set()
    frontier = [seed_id]
    next_frontier = []
    current_depth = 0
    num_nodes = 0

    while current_depth < DEPTH_LIMIT and num_nodes < NODE_CAP:
        current_batch = fetch_batch(frontier, api_key)
        for node in current_batch:
            if node["paperId"] not in visited:
                print(node["title"])
                visited.add(node["paperId"])
                for reference in node["references"]:
                    if reference not in visited and reference not in next_frontier:
                        next_frontier.append(reference)
        frontier = next_frontier
        if not frontier:
            break
        next_frontier = []
        current_depth += 1
        num_nodes = len(visited)
        time.sleep(1.1)

def main():
    dotenv.load_dotenv()
    sem_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

    paper_id = 'ARXIV:1706.03762'
    bfs(paper_id, sem_key)

if __name__ == "__main__":
    main()