import json
import logging
import uuid

import aio_pika

from app.db.session import async_session_factory
from app.events.publisher import get_channel
from app.models.enums import UserRole
from app.services.user_service import change_user_role

logger = logging.getLogger(__name__)

QUEUE_NAME = "auth.creator_activated"

_consumer_tag: str | None = None


async def _handle_creator_activated(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            body = json.loads(message.body)
            user_id = uuid.UUID(body["data"]["user_id"])
            print("Processing creator.activated for user %s", user_id)
            async with async_session_factory() as db:
                user = await change_user_role(db, user_id, UserRole.creator)
                if user:
                    logger.info("User %s role updated to creator", user_id)
                else:
                    logger.warning("User %s not found, skipping role update", user_id)
        except Exception:
            logger.error("Failed to process creator.activated message", exc_info=True)


async def start_consuming() -> None:
    global _consumer_tag
    channel = get_channel()
    if not channel:
        logger.warning("RabbitMQ channel not available, skipping consumer setup")
        return

    try:
        queue = await channel.get_queue(QUEUE_NAME)
        _consumer_tag = await queue.consume(_handle_creator_activated)
        logger.info("Started consuming from %s", QUEUE_NAME)
    except Exception:
        logger.error("Failed to start consuming from %s", QUEUE_NAME, exc_info=True)


async def stop_consuming() -> None:
    global _consumer_tag
    if _consumer_tag is None:
        return

    channel = get_channel()
    if not channel:
        return

    try:
        queue = await channel.get_queue(QUEUE_NAME)
        await queue.cancel(_consumer_tag)
        _consumer_tag = None
        logger.info("Stopped consuming from %s", QUEUE_NAME)
    except Exception:
        logger.error("Failed to stop consuming from %s", QUEUE_NAME, exc_info=True)
