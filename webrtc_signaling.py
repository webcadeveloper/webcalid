import asyncio
import websockets
import json

class SignalingServer:
    def __init__(self):
        self.connections = {}
    
    async def handle_websocket(self, websocket, path):
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
    server = await websockets.serve(signaling_server.handle_websocket, "0.0.0.0", 8765)
    print("WebRTC Signaling Server started on port 8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_server())
