"""This file contains the graph utilities for the application."""

from app.schemas import Message


def dump_messages(messages: list[Message]) -> list[dict]:
    """Dump the messages to a list of dictionaries.

    Args:
        messages (list[Message]): The messages to dump.

    Returns:
        list[dict]: The dumped messages.
    """
    return [message.model_dump() for message in messages]


def prepare_messages(messages: list[Message]) -> list[dict]:
    """Prepare the messages for Agno.

    Args:
        messages (list[Message]): The messages to prepare.

    Returns:
        list[dict]: The prepared messages as dicts for Agno.
    """
    return dump_messages(messages)
