CREATE TABLE crawl_jobs(
   id SERIAL PRIMARY KEY,
   seed_paper_id TEXT NOT NULL,
   status TEXT NOT NULL DEFAULT 'running',
   created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE clusters(
    cluster_id SERIAL NOT NULL PRIMARY KEY,
    crawl_job_id INTEGER NOT NULL,
    FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id),
    label TEXT
);

CREATE TABLE papers(
    paper_id TEXT PRIMARY KEY,
    title TEXT,
    crawl_job_id INTEGER NOT NULL,
    FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id),
    cluster_id INTEGER,
    FOREIGN KEY (cluster_id) REFERENCES clusters(cluster_id)

);

CREATE TABLE citations(
    citing_paper_id TEXT NOT NULL,
    FOREIGN KEY (citing_paper_id) REFERENCES papers(paper_id),
    cited_paper_id TEXT NOT NULL,
    FOREIGN KEY (cited_paper_id) REFERENCES papers(paper_id),
    PRIMARY KEY(citing_paper_id, cited_paper_id)
);