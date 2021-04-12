import json
import logging
import time
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
        # if you need to do any work checking sensors, maintaining comms with the Arduino, etc. this is where to do it
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
    """
    Expects:
    {
        "MoveTo": <INTEGER_NODE>
    }
    """
    if message is None:
        # if you need to do any work checking sensors, maintaining comms with the Arduino, etc. this is where to do it
        return stopped_handler

    logging.info("Handling message in the stopped state")
    bci_move_to_node: int = message['MoveTo']
    reply = {
        "State": "MOVING",
        "Node": bci_move_to_node,
        "Reason": "Requested by BCI"
    }
    SOCKET.send(get_json_bytes(reply))
    logging.debug(f"Sent reply: {reply}")
    return moving_handler


destination_reached = False


def moving_handler(message: Union[dict, None]) -> Callable[[Union[dict, None]], Callable]:
    """
    Expects:
    {
        "State": "STOP",
        "Reason": "Requested by BCI user"
    }
    --or--
    {
        "MoveTo": <INTEGER_NODE>
    }
    """
    if message is None:
        # do some work controlling the chair or communicating with other subsystems

        if destination_reached:
            return finished_handler(None)  # notice this is an actual func call - send finished message immediately
        else:
            return moving_handler
    return moving_handler  # TODO handle messages


def finished_handler(message: Union[dict, None]) -> Callable[[Union[dict, None]], Callable]:
    """
    This state probably will just send the notification before transitioning back to STOPPED.
    """
    assert message is None
    reply = {
        "State": "FINISHED",
        "Reason": "Reached requested node"
    }
    SOCKET.send(get_json_bytes(reply))
    logging.debug(f"Sent finished message: {reply}")
    return stopped_handler


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
            # no message to receive yet, will still call the state so it can do work if necessary
            current_state = current_state(None)
        time.sleep(1)
