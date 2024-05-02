import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fogverse import Consumer
from dotenv import load_dotenv
import uvicorn
import asyncio
import threading


app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>UAV Video Input</h1>
        <img id='messages' alt="uav-data">
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                messages.src = event.data
            };
        </script>
    </body>
</html>
"""

class Client(Consumer):
    def __init__(self, socket: WebSocket, loop=None):
        self.socket = socket
        self.auto_encode = False
        self.consumer_topic = "final_uav_1"
        # self.consumer_conf = {'group_id': str(uuid.uuid4())}
        # self.topic_pattern = os.getenv('TOPIC_PATTERN')
        Consumer.__init__(self,loop=loop)

    async def send(self, data):
        # headers = self.message.headers
        # headers = {key: value.decode() for key, value in headers}
        # data = {
        #     'src': data,
        #     'headers': headers,
        # }
        await self.socket.send_bytes(data)

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Create new event loop and consumer
    loop = asyncio.new_event_loop()
    consumer = Client(websocket, loop=loop)
    thread = threading.Thread(target=run_consumer, args=(websocket, loop, consumer))
    thread.start()

    try:
        while True:
            data = await websocket.receive_bytes()
            print("here")
            await websocket.send(data)
    except WebSocketDisconnect:
            print("WebSocket disconnected")

# async def main(websocket, loop):
#     consumer = Client(websocket, loop=loop)
#     tasks = [consumer.run()]
#     try:
#         await asyncio.gather(*tasks)
#     finally:
#         for t in tasks:
#             t.close()

def run_consumer(websocket: WebSocket, loop, consumer):
    try:
        loop.run_until_complete(consumer.run())
    finally:
        loop.close()

if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)
