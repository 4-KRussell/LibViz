import time

import psycopg
import requests
import os
import dotenv

DEPTH_LIMIT = 15
NODE_CAP = 4000

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

def fetch_batch(paper_ids, api_key, max_retries=3):
    batch = []
    for startIndex in range(0, len(paper_ids), 500):
        chunk = paper_ids[startIndex:startIndex + 500]

        for attempt in range(max_retries):
            result = requests.post(
                'https://api.semanticscholar.org/graph/v1/paper/batch?fields=title,references.title,references.paperId',
                headers={'x-api-key': api_key},
                json={'ids': chunk}
            )
            if result.status_code == 200:
                raw_paper_dict = result.json()
                for paper_dict in raw_paper_dict:
                    batch.append(clean_paper(paper_dict))
                break
            else:
                print(result.status_code, result.text)
                time.sleep(3 * (attempt + 1))
        time.sleep(1.1)

    return batch

def bfs(seed_id, api_key, connection):

    cur = connection.cursor()
    cur.execute("INSERT INTO crawl_jobs (seed_paper_id) VALUES (%s) RETURNING id", (seed_id,))
    crawl_job_id = cur.fetchone()[0]
    connection.commit()

    visited = set()
    frontier = [seed_id]
    next_frontier = []
    current_depth = 0
    num_nodes = 0

    pending_citations = []

    while current_depth < DEPTH_LIMIT and num_nodes < NODE_CAP:
        remaining_budget = NODE_CAP - num_nodes
        if len(frontier) > remaining_budget:
            frontier = frontier[:remaining_budget]

        current_batch = fetch_batch(frontier, api_key)
        for node in current_batch:
            if node["paperId"] not in visited:
                cur.execute(
                    "INSERT INTO papers (paper_id, title, crawl_job_id) VALUES (%s, %s, %s) ON CONFLICT (paper_id) DO NOTHING",
                    (node["paperId"], node["title"], crawl_job_id)
                )
                print(node["title"])
                visited.add(node["paperId"])
                for reference in node["references"]:
                    if reference not in visited and reference not in next_frontier:
                        next_frontier.append(reference)
                    pending_citations.append((node["paperId"], reference))
        frontier = next_frontier
        if not frontier:
            break
        next_frontier = []
        current_depth += 1
        num_nodes = len(visited)
        time.sleep(1.1)

    for citing_id, cited_id in pending_citations:
        if citing_id in visited and cited_id in visited:
            cur.execute(
                "INSERT INTO citations (citing_paper_id, cited_paper_id) VALUES (%s, %s) ON CONFLICT (citing_paper_id, cited_paper_id) DO NOTHING",
                (citing_id, cited_id)
            )
    connection.commit()

    return crawl_job_id

def main():
    dotenv.load_dotenv()
    sem_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")

    dotenv.load_dotenv()
    DB_HOST = os.getenv("DB_HOST")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    DB_PORT = os.getenv("DB_PORT")
    connection = psycopg.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
        port=DB_PORT,
    )

    paper_id = 'DOI:10.1038/s41586-020-2012-7'
    crawl_job_id = bfs(paper_id, sem_key, connection)
    print(f"Crawl job id: {crawl_job_id}")
    connection.close()

if __name__ == "__main__":
    main()