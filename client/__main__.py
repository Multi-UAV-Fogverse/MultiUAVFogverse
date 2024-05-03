import asyncio
import threading
import uuid
import os

from fogverse import Consumer
from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv

def page_not_found(*args):
  return render_template('404.html'), 404

app = Flask(__name__)
app.register_error_handler(404, page_not_found)
socketio = SocketIO(app)

class Client(Consumer):
    def __init__(self, socket: SocketIO, loop=None):
        self.socket = socket
        self.auto_encode = False
        self.consumer_conf = {'group_id': str(uuid.uuid4())}
        self.topic_pattern = "^final_uav_[0-9a-zA-Z-]+$"
        Consumer.__init__(self,loop=loop)

    async def send(self, data):
        headers = self.message.headers
        headers = {key: value.decode() for key, value in headers}
        data = {
            'src': data,
            'headers': headers,
        }
        self.socket.emit(self.message.topic, data)

@app.route('/<uav_id>/')
def index(uav_id=None):
    if not uav_id:
        return page_not_found()
    return render_template('index.html')

async def main(loop):
    consumer = Client(socketio, loop=loop)
    tasks = [consumer.run()]
    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.close()

def run_consumer(loop):
    try:
        loop.run_until_complete(main(loop))
    finally:
        loop.close()

if __name__ == '__main__':
    load_dotenv()
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_consumer, args=(loop,))
    thread.start()
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=False)