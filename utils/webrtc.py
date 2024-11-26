import asyncio
import nest_asyncio
import websockets
import json
import logging
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import threading
from contextlib import asynccontextmanager

# Enable nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CallState:
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ON_HOLD = "on_hold"
    ENDED = "ended"

class WebRTCHandler:
    def __init__(self):
        self.state = CallState.IDLE
        self.connection = None
        self.call_start_time = None
        self._volume = 1.0
        self._muted = False
        self._recording_stream = None
        self._recording = None
        self.signaling_url = "ws://0.0.0.0:8765"
        
    async def _connect_to_signaling_server(self):
        try:
            self.connection = await websockets.connect(self.signaling_url)
            logger.info("Connected to signaling server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to signaling server: {e}")
            return False
            
    def start_call(self, number: str) -> bool:
        """Start a new call"""
        if self.state != CallState.IDLE:
            logger.warning("Cannot start call: Call already in progress")
            return False
            
        try:
            self.state = CallState.CONNECTING
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Connect to signaling server
            success = loop.run_until_complete(self._connect_to_signaling_server())
            if not success:
                self.state = CallState.IDLE
                return False
                
            # Send call initiation
            message = {
                "type": "call_start",
                "number": number,
                "timestamp": datetime.now().isoformat()
            }
            loop.run_until_complete(self.connection.send(json.dumps(message)))
            
            # Start audio stream
            self._start_audio_stream()
            
            self.state = CallState.CONNECTED
            self.call_start_time = datetime.now()
            logger.info(f"Call started to {number}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting call: {e}")
            self.state = CallState.IDLE
            return False
            
    def end_call(self) -> bool:
        """End the current call"""
        if self.state == CallState.IDLE:
            return True
            
        try:
            # Stop recording if active
            if self._recording_stream:
                self._stop_recording()
                
            # Send end call message
            if self.connection:
                loop = asyncio.get_event_loop()
                message = {
                    "type": "call_end",
                    "timestamp": datetime.now().isoformat()
                }
                loop.run_until_complete(self.connection.send(json.dumps(message)))
                loop.run_until_complete(self.connection.close())
                
            self._stop_audio_stream()
            self.state = CallState.IDLE
            self.call_start_time = None
            logger.info("Call ended")
            return True
            
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
            
    def _start_audio_stream(self):
        """Initialize audio stream for the call"""
        try:
            self._recording_stream = sd.Stream(
                channels=2,
                samplerate=44100,
                callback=self._audio_callback
            )
            self._recording_stream.start()
        except Exception as e:
            logger.error(f"Error starting audio stream: {e}")
            raise
            
    def _stop_audio_stream(self):
        """Stop the audio stream"""
        if self._recording_stream:
            self._recording_stream.stop()
            self._recording_stream.close()
            self._recording_stream = None
            
    def _audio_callback(self, indata, outdata, frames, time, status):
        """Handle audio stream data"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        if not self._muted:
            outdata[:] = indata * self._volume
            
    def set_volume(self, volume: float):
        """Set the call volume"""
        self._volume = max(0.0, min(1.0, volume))
        
    def set_mute(self, muted: bool):
        """Mute/unmute the call"""
        self._muted = muted
        
    def get_call_duration(self) -> int:
        """Get the current call duration in seconds"""
        if self.call_start_time and self.state in [CallState.CONNECTED, CallState.ON_HOLD]:
            return int((datetime.now() - self.call_start_time).total_seconds())
        return 0
