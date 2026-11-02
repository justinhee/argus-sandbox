import pickle


def import_rules(request_body: bytes) -> dict:
    """Load fraud rules uploaded by a merchant through the dashboard."""
    return pickle.loads(request_body)
