import asyncio
import websockets
from aiohttp import web
import json

# WebSocket handler
async def handle_websocket(websocket, path):
    async for message in websocket:
        print(f"Received WebSocket message: {message}")
        await websocket.send(f"Echo: {message}")

# HTTP handler (API REST)
async def handle_api(request):
    data = await request.json()
    # Aquí procesas la solicitud de la API, como crear un caso, por ejemplo
    return web.json_response({'message': 'Case created successfully'})

# Crear servidor WebSocket y HTTP juntos
async def start_servers():
    # Servidor WebSocket
    websocket_server = await websockets.serve(handle_websocket, 'localhost', 3000)

    # Servidor HTTP (API)
    app = web.Application()
    app.add_routes([web.post('/api/cases', handle_api)])

    # Iniciar ambos servidores
    web_server = web.AppRunner(app)
    await web_server.setup()
    site = web.TCPSite(web_server, 'localhost', 3001)
    await site.start()

    # Mantener ambos servidores corriendo
    await websocket_server.wait_closed()

if __name__ == '__main__':
    asyncio.run(start_servers())
