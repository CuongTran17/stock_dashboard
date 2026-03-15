import asyncio
import websockets

async def test_proxy():
    uri = "ws://127.0.0.1:8000/api/ws/dnse"
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected to proxy!")
            
            # Send a subscription message
            msg = '{"action":"subscribe","data":{"symbol":"SSI","channel":"stock"}}'
            print(f"Sending: {msg}")
            await websocket.send(msg)
            
            print("Waiting for messages...")
            for _ in range(5):
                response = await websocket.recv()
                print(f"Received: {response[:100]}")
                
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_proxy())
