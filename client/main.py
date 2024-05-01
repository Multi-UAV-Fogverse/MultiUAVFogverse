import os
import uuid
from fastapi import FastAPI, WebSocket
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
        <div id="messages">
        </div>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('IMG')
                message.src = event.data
                messages.appendChild(message)
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
        self.socket.send(data)

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    consumer = Client(websocket)  # Create a Client instance with the WebSocket object
    await consumer.run()  # Run the Client
    try:
        while True:
            data = await websocket.receive()
            await websocket.send(data)
    finally:
        # Clean up
        consumer._close()

if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)
