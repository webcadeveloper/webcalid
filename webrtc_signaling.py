import asyncio
import websockets
import json
import logging
import traceback
from typing import Dict, Any, Optional
from websockets.exceptions import ConnectionClosed, InvalidHandshake

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalingServer:
    def __init__(self):
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
    async def register(self, websocket: websockets.WebSocketServerProtocol, client_id: str):
        """Register a new client connection"""
        try:
            self.connections[client_id] = websocket
            logger.info(f"Client {client_id} registered successfully")
            await self._notify_connection_status(client_id, True)
        except Exception as e:
            logger.error(f"Error registering client {client_id}: {str(e)}")
            logger.debug(f"Registration error traceback: {traceback.format_exc()}")
            raise
        
    async def unregister(self, websocket: websockets.WebSocketServerProtocol):
        """Unregister a client connection"""
        try:
            for client_id, ws in list(self.connections.items()):
                if ws == websocket:
                    del self.connections[client_id]
                    logger.info(f"Client {client_id} unregistered successfully")
                    await self._notify_connection_status(client_id, False)
                    break
        except Exception as e:
            logger.error(f"Error unregistering client: {str(e)}")
            logger.debug(f"Unregistration error traceback: {traceback.format_exc()}")
            
    async def _notify_connection_status(self, client_id: str, connected: bool):
        """Notify other clients about connection status changes"""
        try:
            message = {
                'type': 'connection_status',
                'client_id': client_id,
                'connected': connected,
                'timestamp': asyncio.get_event_loop().time()
            }
            await self._broadcast_message(message, exclude=client_id)
        except Exception as e:
            logger.error(f"Error notifying connection status: {str(e)}")
            logger.debug(f"Notification error traceback: {traceback.format_exc()}")

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        try:
            msg_type = message.get('type')
            client_id = message.get('clientId')
            
            if not msg_type:
                logger.error("Message received without type")
                await self._send_error(websocket, "Missing message type")
                return
                
            logger.debug(f"Handling message type: {msg_type} from client: {client_id}")
            
            if msg_type == 'register':
                if not client_id:
                    logger.error("Registration attempt without client ID")
                    await self._send_error(websocket, "Missing client ID")
                    return
                await self.register(websocket, client_id)
                
            elif msg_type in ['offer', 'answer', 'candidate']:
                target_id = message.get('target')
                if not target_id:
                    logger.error(f"Missing target for {msg_type} message")
                    await self._send_error(websocket, f"Missing target for {msg_type}")
                    return
                    
                if target_id in self.connections:
                    await self.connections[target_id].send(json.dumps(message))
                    logger.debug(f"Forwarded {msg_type} from {client_id} to {target_id}")
                else:
                    logger.warning(f"Target client {target_id} not found")
                    await self._send_error(websocket, f"Target client {target_id} not found")
            else:
                logger.warning(f"Unknown message type received: {msg_type}")
                await self._send_error(websocket, f"Unknown message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            logger.debug(f"Message handling error traceback: {traceback.format_exc()}")
            await self._send_error(websocket, "Internal server error")

    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol):
        """Handle new WebSocket connections"""
        try:
            # Handle CORS
            origin = websocket.request_headers.get('Origin')
            if origin:
                await self._handle_cors(websocket, origin)
                
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message received: {str(e)}")
                    await self._send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    logger.debug(f"Message processing error traceback: {traceback.format_exc()}")
                    await self._send_error(websocket, "Error processing message")
                    
        except ConnectionClosed:
            logger.info("Connection closed normally")
        except InvalidHandshake as e:
            logger.error(f"Invalid handshake: {str(e)}")
        except Exception as e:
            logger.error(f"Connection handler error: {str(e)}")
            logger.debug(f"Connection handler error traceback: {traceback.format_exc()}")
        finally:
            await self.unregister(websocket)
            
    async def _handle_cors(self, websocket: websockets.WebSocketServerProtocol, origin: str):
        """Handle CORS headers for WebSocket connections"""
        try:
            allowed_origins = ['*']  # Configure as needed
            if origin in allowed_origins or '*' in allowed_origins:
                response_headers = {
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Methods': 'GET, POST',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Max-Age': '3600',
                }
                for key, value in response_headers.items():
                    websocket.response_headers[key] = value
        except Exception as e:
            logger.error(f"Error handling CORS: {str(e)}")
            
    async def _send_error(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Send error message to client"""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': message,
                'timestamp': asyncio.get_event_loop().time()
            }))
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
            
    async def _broadcast_message(self, message: Dict[str, Any], exclude: Optional[str] = None):
        """Broadcast message to all connected clients except excluded one"""
        for client_id, websocket in self.connections.items():
            if client_id != exclude:
                try:
                    await websocket.send(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {str(e)}")

async def main():
    server = SignalingServer()
    
    async def handler(websocket):
        await server.handle_connection(websocket)
    
    try:
        # Create WebSocket server without extra_headers
        async with websockets.serve(
            handler,
            "0.0.0.0",
            8765,
            ping_interval=30,
            ping_timeout=10,
            compression=None
        ) as ws_server:
            logger.info("WebRTC Signaling Server started successfully on port 8765")
            await asyncio.Future()  # run forever
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.debug(f"Server error traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.debug(f"Fatal error traceback: {traceback.format_exc()}")