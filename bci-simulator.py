import zmq
import time
import json

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect(f"tcp://localhost:{port}")
print("connected")


def get_json_bytes(message: dict) -> bytes:
    json_stringified = json.dumps(message)
    return json_stringified.encode('UTF-8')


msg = {
    "State": "CONNECTED",
    "Reason": "System start"
}
socket.send(get_json_bytes(msg))
print(f"Sent {msg}")
time.sleep(5)
msg = {
    "MoveTo": 5
}
socket.send(get_json_bytes(msg))
print(f"Sent {msg}")
