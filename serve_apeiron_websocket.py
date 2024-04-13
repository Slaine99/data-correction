import asyncio
import websockets
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the WebSocket server URL
WEBSOCKET_SERVER_URL = "localhost"
WEBSOCKET_SERVER_PORT = 8000

# Set to store connected clients
connected_clients = set()


# Function to handle new WebSocket connections
async def handle_connection(websocket, path):
    # Add client to the set of connected clients
    connected_clients.add(websocket)

    try:
        # Continuously listen for incoming messages
        async for message in websocket:
            # Broadcast the message to all connected clients
            await asyncio.gather(*[client.send(message) for client in connected_clients])
    except websockets.exceptions.ConnectionClosedError:
        logger.info("Connection closed by client")
    finally:
        # Remove client from the set of connected clients when connection is closed
        connected_clients.remove(websocket)


# Start the WebSocket server
async def start_server():
    logger.info(f"Starting WebSocket server at ws://{WEBSOCKET_SERVER_URL}:{WEBSOCKET_SERVER_PORT}")
    async with websockets.serve(handle_connection, WEBSOCKET_SERVER_URL, WEBSOCKET_SERVER_PORT):
        await asyncio.Future()  # Run forever


# Run the WebSocket server
if __name__ == "__main__":
    asyncio.run(start_server())
