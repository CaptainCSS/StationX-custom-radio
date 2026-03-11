import socketio
import time

sio = socketio.Client()

@sio.event
def connect():
    print("Connected")

@sio.on('all_requests')
def on_all_requests(data):
    print("all_requests", data)

@sio.on('new_request')
def on_new_request(data):
    print("new_request", data)

sio.connect("http://localhost:3000")
time.sleep(2)
sio.disconnect()
