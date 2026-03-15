import asyncio
import websockets

base = "wss://ws-openapi.dnse.com.vn"
paths = ["", "/", "/wss", "/ws", "/websocket", "/mqtt", "/socket", "/openapi", "/stream"]

async def probe(url):
    try:
        async with websockets.connect(url, open_timeout=5, close_timeout=2):
            print("OK", url)
    except Exception as e:
        print("FAIL", url, "=>", type(e).__name__, e)

async def probe_mqtt(url):
    try:
        async with websockets.connect(url, subprotocols=["mqtt"], open_timeout=5, close_timeout=2) as ws:
            print("OK_MQTT", url, "subprotocol=", ws.subprotocol)
    except Exception as e:
        print("FAIL_MQTT", url, "=>", type(e).__name__, e)

async def main():
    for p in paths:
        await probe(base + p)
    print("--- with mqtt subprotocol ---")
    for p in paths:
        await probe_mqtt(base + p)

asyncio.run(main())
