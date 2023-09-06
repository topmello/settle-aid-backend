from typing import Dict, Any, Set, Tuple
from fastapi import WebSocket

TMessagePayload = Any
# (sender_id, receiver_id): set of websockets
TActiveConnections = Dict[Tuple[int, int], Set[WebSocket]]


class WSManager:
    def __init__(self):
        self.active_connections: TActiveConnections = {}

    async def connect(self, sender_id: int, receiver_id: int, ws: WebSocket):
        key = (sender_id, receiver_id)
        self.active_connections.setdefault(key, set()).add(ws)

    async def disconnect(self, sender_id: int, receiver_id: int, ws: WebSocket):
        key = (sender_id, receiver_id)
        self.active_connections[key].remove(ws)

    async def send_message(self, sender_id: int, receiver_id: int, message: TMessagePayload):
        key = (sender_id, receiver_id)
        for ws in self.active_connections.get(key, []):
            await ws.send_json(message)


ws_manager = WSManager()
