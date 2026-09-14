import psycopg
import dotenv
import os
import igraph
import leidenalg
import cairo
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from pyvis.network import Network

def visualize_parition(edges, papers, partition):
    net = Network(height="900px", width="100%", notebook=False)

    for cluster_id, cluster in enumerate(partition):
        for vertex in cluster:
            paper_id, title = papers[vertex]
            net.add_node(
                vertex,
                label=title[:30] if title else paper_id[:8],
                title=title if title else paper_id,
                group=cluster_id,
            )

    for citing_index, cited_index in edges:
        net.add_edge(citing_index, cited_index)

    net.write_html("clusters.html", notebook=False)

def top_terms(tfidf_matrix, feature_names, cluster_index, n = 5):
    row = tfidf_matrix[cluster_index].toarray()[0]
    top_indices = row.argsort()[::-1][:n]
    return [feature_names[i] for i in top_indices]

def main():
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
    cursor = connection.cursor()

    cursor.execute("SELECT crawl_job_id FROM papers GROUP BY crawl_job_id ORDER BY crawl_job_id DESC LIMIT 1")
    crawl_job_id = cursor.fetchone()[0]

    cursor.execute("SELECT paper_id, title FROM papers WHERE crawl_job_id = %s", (crawl_job_id,))
    papers = cursor.fetchall()
    print(len(papers))

    cursor.execute("SELECT citing_paper_id, cited_paper_id FROM citations WHERE citing_paper_id IN (SELECT paper_id FROM papers WHERE crawl_job_id = %s) AND cited_paper_id IN (SELECT paper_id FROM papers WHERE crawl_job_id = %s)",
                   (crawl_job_id, crawl_job_id))
    cited_papers = cursor.fetchall()
    print(len(cited_papers))

    paper_dict = dict()
    for index, (paper_id, title) in enumerate(papers):
        paper_dict[paper_id] = index

    edges = []
    for citing_paper_id, cited_paper_id in cited_papers:
        citing_index = paper_dict[citing_paper_id]
        cited_index = paper_dict[cited_paper_id]
        edges.append((citing_index, cited_index))

    print(len(edges))

    g = igraph.Graph(n=len(papers), edges=edges, directed=True)
    print(g.summary())
    print(g.vcount(), g.ecount())

    g_undirected = g.as_undirected(mode="collapse")
    partition = leidenalg.find_partition(g_undirected, leidenalg.ModularityVertexPartition)

    print(len(partition))
    print(partition.summary())

    sizes = sorted([len(c) for c in partition], reverse=True)
    print(sizes[:20])

    for vertex in partition[0]:
        print(papers[vertex][1])

    igraph.plot(partition, target="clusters.png", vertex_size = 5, bbox =(1200, 1200))

    cluster_documents = []
    for cluster in partition:
        titles_in_cluster = [papers[vertex][1] for vertex in cluster if papers[vertex][1] is not None]
        combined_text = " ".join(titles_in_cluster)
        cluster_documents.append(combined_text)

    print(cluster_documents[0][:300])
    print(len(cluster_documents))

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(cluster_documents)
    feature_names = vectorizer.get_feature_names_out()

    print(tfidf_matrix.shape)

    print(top_terms(tfidf_matrix, feature_names, 0))

    for i in range(len(partition)):
        if len(partition[i]) > 5:
            terms = top_terms(tfidf_matrix, feature_names, i)
            label = ", ".join(terms)
            print(f"Cluster {i} (size {len(partition[i])}): {label}")

            cursor.execute("INSERT INTO clusters (crawl_job_id, label) VALUES (%s, %s) RETURNING cluster_id",
                           (crawl_job_id, label))
            new_cluster_id = cursor.fetchone()[0]
            for vertex in partition[i]:
                paper_id = papers[vertex][0]
                cursor.execute(
                    "UPDATE papers SET cluster_id = %s WHERE paper_id = %s",
                    (new_cluster_id, paper_id)
                )

    connection.commit()

    visualize_parition(edges, papers, partition)

if __name__ == "__main__":
    main()