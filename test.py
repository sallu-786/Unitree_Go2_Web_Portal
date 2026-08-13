import asyncio, json, websockets

async def test():
    async with websockets.connect(f"ws://127.0.0.1:9090") as ws:
        await ws.send(json.dumps({
            "op": "call_service",
            "service": "/rosapi/topics",
            "type": "rosapi/Topics"
        }))
        resp = await ws.recv()
        data = json.loads(resp)
        topics = data.get("values", {}).get("topics", [])
        print(len(topics))
        print(topics)

asyncio.run(test())