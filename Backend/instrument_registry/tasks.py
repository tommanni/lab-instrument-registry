from huey.contrib.djhuey import db_task

from instrument_registry.embedding import precompute_instrument_embeddings


@db_task()
def run_embedding_precompute(*, batch_size: int = 100, force: bool = False) -> dict:
    """
    Huey task wrapper around the shared precompute helper.

    Returns the summary dictionary produced by precompute_instrument_embeddings.
    """
    return precompute_instrument_embeddings(batch_size=batch_size, force=force)
