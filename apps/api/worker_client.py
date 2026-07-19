from celery import Celery


def enqueue_ingest_task(
    *,
    document_id: str | None,
    force: bool,
    requested_by: str,
    broker_url: str,
) -> str:
    app = Celery("relay", broker=broker_url)
    result = app.send_task(
        "tasks.ingest_knowledge",
        kwargs={
            "document_id": document_id,
            "force": force,
            "requested_by": requested_by,
        },
    )
    return str(result.id)
