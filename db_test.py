import psycopg
import os
import dotenv

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
    cursor.execute(
        "SELECT * FROM crawl_jobs"
    )
    rows = cursor.fetchall()
    print(rows)

    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()