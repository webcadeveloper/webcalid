import json
import asyncio
import websockets
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class WebRTCConfig:
    ice_servers: list = None
    signaling_url: str = "ws://localhost:8765"

class WebRTCHandler:
    def __init__(self, config: WebRTCConfig = None):
        self.config = config or WebRTCConfig()
        self.connection = None
        self.call_start_time = None
        self._volume = 1.0
        self._muted = False

    def start_call(self, number: str) -> bool:
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._connect_and_call(number))
        except Exception as e:
            print(f"Error starting call: {e}")
            return False

    async def _connect_and_call(self, number: str) -> bool:
        try:
            self.connection = await websockets.connect(self.config.signaling_url)
            await self.connection.send(json.dumps({
                "type": "call",
                "number": number
            }))
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def end_call(self) -> None:
        if self.connection:
            asyncio.get_event_loop().run_until_complete(self._disconnect())

    async def _disconnect(self) -> None:
        if self.connection:
            await self.connection.close()
            self.connection = None

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))

    def set_mute(self, muted: bool) -> None:
        self._muted = muted

    def get_call_duration(self) -> Optional[int]:
        if self.call_start_time:
            return int((asyncio.get_event_loop().time() - self.call_start_time))
        return None