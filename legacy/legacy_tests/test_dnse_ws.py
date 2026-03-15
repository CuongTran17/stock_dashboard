import asyncio
import websockets
import json

async def test_ws():
    url = "wss://datafeed-lts-krx.dnse.com.vn:443/wss"
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as ws:
            print("Connected! Sending subscription...")
            # Try a few common formats for DNSE Entrade WebSocket
            topics = [
                "plaintext/quotes/krx/mdds/tick/v1/roundlot/symbol/FPT"
            ]
            # Format 1
            msg1 = json.dumps({"action": "subscribe", "topics": topics})
            await ws.send(msg1)
            
            # Format 2
            msg2 = json.dumps({"type": "sub", "topic": topics[0]})
            await ws.send(msg2)
            
            # Format 3: action: 'on', topic...
            msg3 = json.dumps({"action": "on", "data": {"topic": topics[0]}})
            await ws.send(msg3)

            for _ in range(5):
                res = await asyncio.wait_for(ws.recv(), timeout=5)
                print("Received:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test_ws())
