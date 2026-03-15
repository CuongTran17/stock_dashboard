import asyncio
import websockets
import json

async def test_ws():
    url = "wss://ws-openapi.dnse.com.vn"
    try:
        async with websockets.connect(url, open_timeout=5, close_timeout=2) as ws:
            print("WS connected!")
            # Send sub message
            await ws.send(json.dumps({"action": "subscribe", "data": {"symbol": "FPT", "channel": "stock"}}))
            # Wait for response
            res = await asyncio.wait_for(ws.recv(), timeout=5)
            print("WS response:", res)
    except Exception as e:
        print("WS ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test_ws())
