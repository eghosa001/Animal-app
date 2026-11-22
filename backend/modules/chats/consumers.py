"""Read-only ASGI socket: authenticated hint stream, never a message-write path."""
import asyncio
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .realtime import chat_group_name, validate_socket_ticket


class ConversationUpdateConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group_joined = False
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        protocols = self.scope.get("subprotocols") or []
        candidates = [
            p.removeprefix("anima.ticket.")
            for p in protocols if p.startswith("anima.ticket.")
        ]
        if len(candidates) != 1 or "anima.chat.v1" not in protocols:
            await self.close(code=4401)
            return
        self.ticket = candidates[0]
        self.user_id = await database_sync_to_async(validate_socket_ticket)(
            self.ticket, self.conversation_id
        )
        if self.user_id is None:
            await self.close(code=4403)
            return
        self.group = chat_group_name(self.conversation_id)
        try:
            await self.channel_layer.group_add(self.group, self.channel_name)
        except Exception:
            await self.close(code=4503)
            return
        self.group_joined = True
        await self.accept(subprotocol="anima.chat.v1")
        self.expiry_task = asyncio.create_task(self._close_when_session_expires())

    async def _close_when_session_expires(self):
        # A stolen short-lived ticket cannot maintain a long-lived socket.
        await asyncio.sleep(14 * 60)
        await self.close(code=4401)

    async def receive_json(self, content, **kwargs):
        # No chat body ever travels from an unthrottled socket.
        if isinstance(content, dict) and content.get("type") == "ping":
            await self.send_json({"type": "pong"})
            return
        await self.close(code=4400)

    async def chat_update(self, event):
        # Recheck access and revocations before delivering each private notice.
        permitted = await database_sync_to_async(validate_socket_ticket)(
            self.ticket, self.conversation_id, max_age=None
        )
        if permitted != self.user_id:
            await self.close(code=4403)
            return
        if event.get("conversation_id") != str(self.conversation_id):
            return
        await self.send_json({
            "type": event["kind"],
            "conversation_id": event["conversation_id"],
            "message_id": event["message_id"],
            "server_timestamp": event["server_timestamp"],
        })

    async def disconnect(self, close_code):
        task = getattr(self, "expiry_task", None)
        if task is not None:
            task.cancel()
        if getattr(self, "group_joined", False):
            await self.channel_layer.group_discard(self.group, self.channel_name)
