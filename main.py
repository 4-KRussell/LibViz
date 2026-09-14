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
    # r = requests.get(f'https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,references.title,references.paperId', headers={'x-api-key': sem_key})
    # good = r.status_code
    #
    # if good == 200:
    #     requestJsonDict = r.json()
    #     print(requestJsonDict["title"])
    #     for reference in requestJsonDict["references"]:
    #         print(reference["title"])
    #         print(reference["paperId"])
    # else:
    #     print(r.text)
    paper_ids = ['2e9d221c206e9503ceb452302d68d10e293f2a10', '0b44fcbeea9415d400c5f5789d6b892b6f98daff', 'f52de7242e574b70410ca6fb70b79c811919fc00']

    # clean_batch = fetch_batch(paper_ids, sem_key)
    # print(clean_batch)

    bfs(paper_id, sem_key)

if __name__ == "__main__":
    main()