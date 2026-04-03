from src.db import Database


def handle_request() -> str:
    # TODO replace with service-layer call
    return Database().ping()
