import asyncio
import websockets
import json
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalingServer:
    def __init__(self):
        self.connections = {}
    
    async def handle_websocket(self, websocket):
        try:
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'register':
                    self.connections[data['id']] = websocket
                elif data['type'] in ['offer', 'answer', 'candidate']:
                    target_id = data['target']
                    if target_id in self.connections:
                        await self.connections[target_id].send(json.dumps({
                            'type': data['type'],
                            'data': data['data']
                        }))
        except websockets.exceptions.ConnectionClosed:
            # Remove connection when closed
            for key, value in list(self.connections.items()):
                if value == websocket:
                    del self.connections[key]

signaling_server = SignalingServer()

async def start_server():
    async def handler(websocket):
        logger.info("New WebSocket connection attempt")
        try:
            await signaling_server.handle_websocket(websocket)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed normally")
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}", exc_info=True)
    
    try:
        server = await websockets.serve(
            handler,
            "0.0.0.0",
            8765,
            ping_interval=30,
            ping_timeout=10
        )
        logger.info("WebRTC Signaling Server started on port 8765")
        await server.wait_closed()
    except Exception as e:
        logger.error(f"Failed to start signaling server: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(start_server())
