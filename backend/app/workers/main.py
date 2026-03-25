from app.workers.tasks import run_article_pipeline


if __name__ == "__main__":
    run_article_pipeline.send("frequent urination with cystitis", "women seeking informational guidance")
