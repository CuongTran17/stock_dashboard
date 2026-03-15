import asyncio
import websockets
import json

async def receive_market_data():
    uri = "ws://127.0.0.1:8000/api/ws/market"
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected to VNStock Intraday Stream!")
            for _ in range(3):
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received action: {data.get('action')}")
                
                # Print an example of one symbol
                cache = data.get('data', {})
                if "FPT" in cache and len(cache["FPT"]) > 0:
                    print(f"FPT latest tick: {cache['FPT'][0]}")
                elif "HPG" in cache and len(cache["HPG"]) > 0:
                    print(f"HPG latest tick: {cache['HPG'][0]}")
                else:
                    print("Waiting for data to fetch in the background...")
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(receive_market_data())
