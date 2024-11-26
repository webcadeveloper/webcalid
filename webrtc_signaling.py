import asyncio
import websockets
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalingServer:
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
    async def register(self, websocket: websockets.WebSocketServerProtocol, client_id: str):
        self.connections[client_id] = websocket
        logger.info(f"Client {client_id} registered")
        
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        for client_id, ws in list(self.connections.items()):
            if ws == websocket:
                del self.connections[client_id]
                logger.info(f"Client {client_id} unregistered")
                break

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        msg_type = message.get('type')
        
        if msg_type == 'register':
            await self.register(websocket, message['clientId'])
        elif msg_type in ['offer', 'answer', 'candidate']:
            target_id = message.get('target')
            if target_id and target_id in self.connections:
                await self.connections[target_id].send(json.dumps(message))
                logger.debug(f"Forwarded {msg_type} from {message.get('clientId')} to {target_id}")
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON message received")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed normally")
        except Exception as e:
            logger.error(f"Connection handler error: {e}")
        finally:
            await self.unregister(websocket)

async def main():
    server = SignalingServer()
    
    async def handler(websocket):
        await server.handle_connection(websocket)
    
    try:
        async with websockets.serve(
            handler,
            "0.0.0.0",
            8765,
            ping_interval=30,
            ping_timeout=10,
            compression=None
        ) as ws_server:
            logger.info("WebRTC Signaling Server started on port 8765")
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
