import json
import logging
import time
from enum import Enum, auto
from typing import Callable, Union

import zmq

logging.basicConfig(level=logging.DEBUG)

PORT = "5556"
CONTEXT = zmq.Context()
SOCKET = CONTEXT.socket(zmq.PAIR)
URL = f"tcp://*:{PORT}"
SOCKET.bind(URL)
logging.info(f"Bound socket to {URL}")


def get_json_bytes(message: dict) -> bytes:
    json_stringified = json.dumps(message)
    return json_stringified.encode('UTF-8')


def idle_handler(message: Union[dict, None]) -> Callable[[Union[dict, None]], Callable]:
    """
    One method for each state, takes action according to the message.

    Expects:
    {
        "State": "CONNECTED",
        "Reason": "System start"
    }

    :param message: the message from the BCI, now parsed into Python dict from JSON --or-- NONE if no message yet
    :return: the *_handler() method that should be called next
    """
    if message is None:
        # don't need to do any work in the mean time, so just return this state again
        return idle_handler
    logging.info("Handling message in idle state")
    bci_state = message['State']
    if bci_state != "CONNECTED":
        logging.error(f"Expected CONNECTED state from BCI, got {bci_state}")
        return idle_handler  # stay in state
    # else got what we expected
    reply = {
        "State": "STOPPED",
        "Reason": "Waiting for direction"
    }
    SOCKET.send(get_json_bytes(reply))
    logging.debug(f"Sent reply: {reply}")
    return stopped_handler  # transition to next state


def stopped_handler(message: Union[dict, None]) -> Callable[[Union[dict, None]], Callable]:
    logging.info("Handling message in the stopped state")
    bci_request =


def moving_handler(message: Union[dict, None]) -> Callable[[Union[dict, None]], Callable]:
    pass


def finished_handler(message: Union[dict, None]) -> Callable[[Union[dict, None]], Callable]:
    pass


if __name__ == '__main__':
    current_state = idle_handler  # start in IDLE
    while True:
        try:
            msg = SOCKET.recv(flags=zmq.NOBLOCK)
            logging.debug(f"Received {msg}")
            msg_dict = json.loads(str(msg, 'UTF-8'))
            logging.debug(f"Parsed into dict {msg_dict}")
            current_state = current_state(msg_dict)
        except zmq.Again:
            # no message to receive yet
        time.sleep(1)
