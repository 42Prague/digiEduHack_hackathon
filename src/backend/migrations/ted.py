from swx_api.app.models.qa_article import QaArticleCreate
from swx_api.app.services.qa_article_service import QaArticleService
from swx_api.core.database.db import SessionLocal  # import the session factory

def seed_articles():
    sample_articles = [
        {
            "title": "Academic Calendar 2024/25",
            "url": "https://www.czu.cz/en/r-6990-studies/academic-calendar",
            "source": "czu.cz",
            "content": """
                The academic year 2024/2025 starts on September 23, 2024.
                The winter semester runs from September to January.
                The summer semester begins on February 17, 2025.
                Exam periods follow each semester.
            """,
        },
        {
            "title": "Erasmus+ Application Guide",
            "url": "https://pef.czu.cz/en/r-9328-international-relations",
            "source": "pef.czu.cz",
            "content": """
                CZU students can apply for Erasmus+ from March to May 2025.
                Applications must be submitted via the Mobility Online portal.
                Each student must provide a Learning Agreement and proof of language proficiency.
            """,
        }
    ]

    db = SessionLocal()  # create the actual session
    try:
        for article in sample_articles:
            QaArticleService.create_new_qa_article(
                db=db,
                data=QaArticleCreate(
                    title=article["title"],
                    url=article["url"],
                    source=article["source"],
                    content=article["content"]
                )
            )
        db.commit()
        print("✅ Sample QA articles seeded successfully.")
    finally:
        db.close()  # always close session

if __name__ == "__main__":
    seed_articles()
