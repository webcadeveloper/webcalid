import asyncio
import websockets
import json

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
    async def handler(websocket, path):
        try:
            await signaling_server.handle_websocket(websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logging.error(f"Error in WebSocket handler: {e}")
    
    try:
        server = await websockets.serve(
            handler,
            host="0.0.0.0",
            port=8765,
            ping_interval=30,
            ping_timeout=10
        )
        print("WebRTC Signaling Server started on port 8765")
        await server.wait_closed()
    except Exception as e:
        logging.error(f"Failed to start signaling server: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(start_server())
