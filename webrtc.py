import json
import asyncio
import nest_asyncio
import websockets
import sounddevice as sd
import soundfile as sf
import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import os
import threading
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enable nested event loops
nest_asyncio.apply()

@dataclass
class WebRTCConfig:
    ice_servers: list[dict[str, list[str]]] | None = None
    signaling_url: str = "ws://0.0.0.0:8765"
    recording_path: str = "recordings"

    def __post_init__(self):
        if self.ice_servers is None:
            self.ice_servers = [{"urls": ["stun:stun.l.google.com:19302"]}]

class CallState:
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ON_HOLD = "on_hold"
    RECORDING = "recording"
    ENDED = "ended"

class WebRTCHandler:
    def __init__(self, config: WebRTCConfig | None = None):
        self.config = config if config is not None else WebRTCConfig()
        self.connection = None
        self.call_start_time = None
        self._volume = 1.0
        self._muted = False
        self.state = CallState.IDLE
        self._recording = None
        self._recording_stream = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._loop = None
        self._thread_local = threading.local()
        
    @asynccontextmanager
    async def _get_event_loop(self):
        """Ensure we have a proper event loop in the current thread."""
        try:
            if not hasattr(self._thread_local, 'loop'):
                self._thread_local.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._thread_local.loop)
            yield self._thread_local.loop
        except Exception as e:
            logger.error(f"Event loop error: {e}")
            raise
        finally:
            if hasattr(self._thread_local, 'loop'):
                self._thread_local.loop.close()
                delattr(self._thread_local, 'loop')
        
        # Ensure recording directory exists
        os.makedirs(self.config.recording_path, exist_ok=True)

    def start_call(self, number: str) -> bool:
        if self.state != CallState.IDLE:
            logger.warning("Cannot start call: Call already in progress")
            return False
            
        try:
            self.state = CallState.CONNECTING
            logger.info(f"Starting call to {number}")
            
            async def _start_call_async():
                async with self._get_event_loop() as loop:
                    for attempt in range(self._max_reconnect_attempts):
                        try:
                            success = await self._connect_and_call(number)
                            if success:
                                self.state = CallState.CONNECTED
                                self.call_start_time = loop.time()
                                logger.info("Call connected successfully")
                                return True
                        except Exception as e:
                            logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                            if attempt < self._max_reconnect_attempts - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            continue
                    return False
            
            # Run in the current thread's event loop
            success = asyncio.run(_start_call_async())
            if not success:
                self.state = CallState.IDLE
                logger.error("Failed to establish call after multiple attempts")
            return success
            
        except Exception as e:
            logger.error(f"Error starting call: {e}", exc_info=True)
            self.state = CallState.IDLE
            return False

    async def _connect_and_call(self, number: str) -> bool:
        try:
            self.connection = await websockets.connect(self.config.signaling_url)
            await self.connection.send(json.dumps({
                "type": "call",
                "number": number,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Wait for connection confirmation
            response = await asyncio.wait_for(self.connection.recv(), timeout=5.0)
            data = json.loads(response)
            return data.get('status') == 'connected'
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def end_call(self) -> None:
        if self.state in [CallState.CONNECTED, CallState.ON_HOLD, CallState.RECORDING]:
            if self._recording_stream:
                self.stop_recording()
            
            asyncio.get_event_loop().run_until_complete(self._disconnect())
            self.state = CallState.ENDED
            self.call_start_time = None

    async def _disconnect(self) -> None:
        if self.connection:
            try:
                await self.connection.send(json.dumps({
                    "type": "end_call",
                    "timestamp": datetime.now().isoformat()
                }))
                await self.connection.close()
            except:
                pass
            finally:
                self.connection = None

    def start_recording(self) -> bool:
        if self.state != CallState.CONNECTED:
            return False
            
        try:
            filename = f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = os.path.join(self.config.recording_path, filename)
            
            # Setup recording stream
            self._recording = sf.SoundFile(
                filepath, 
                mode='w',
                samplerate=44100,
                channels=2
            )
            
            # Start recording stream
            self._recording_stream = sd.InputStream(
                callback=self._audio_callback,
                channels=2,
                samplerate=44100
            )
            self._recording_stream.start()
            
            self.state = CallState.RECORDING
            return True
            
        except Exception as e:
            print(f"Recording error: {e}")
            return False

    def stop_recording(self) -> Optional[str]:
        if self.state != CallState.RECORDING:
            return None
            
        try:
            if self._recording_stream:
                self._recording_stream.stop()
                self._recording_stream.close()
                self._recording_stream = None
                
            if self._recording:
                filepath = self._recording.name
                self._recording.close()
                self._recording = None
                self.state = CallState.CONNECTED
                return filepath
                
        except Exception as e:
            print(f"Error stopping recording: {e}")
            
        return None

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Audio callback status: {status}")
        if self._recording:
            self._recording.write(indata * self._volume)

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        if self._recording_stream:
            self._recording_stream.stop()
            self._recording_stream.start()

    def set_mute(self, muted: bool) -> None:
        self._muted = muted
        if self._recording_stream:
            if muted:
                self._recording_stream.stop()
            else:
                self._recording_stream.start()

    def get_call_duration(self) -> Optional[int]:
        if self.call_start_time and self.state in [CallState.CONNECTED, CallState.RECORDING, CallState.ON_HOLD]:
            return int((asyncio.get_event_loop().time() - self.call_start_time))
        return None

    def get_state(self) -> str:
        return self.state