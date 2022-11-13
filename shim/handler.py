from fabric_protos_python.peer.chaincode_shim_pb2_grpc import Chaincode
from utils import *

class MessageHandler:
    chaincode_id: str
    chaincode: Chaincode
    state: str = ChaincodeState.CREATED.name

    def __init__(self, chaincode_id: str, chaincode: Chaincode) -> None:
        self.chaincode_id = chaincode_id
        self.chaincode = chaincode

    def chat_with_peer(self, request_iterator, context):
        for raw_msg in request_iterator:
            msg = Message(raw_msg)
            print('Received message from peer:', msg, ', state:', self.state)

            if self.state == ChaincodeState.CREATED.name:
                self.handle_registered(msg)
            elif self.state == ChaincodeState.ESTABLISHED.name:
                self.handle_ready(msg)
            elif self.state == ChaincodeState.READY.name:
                self.handle_actions(msg)

    def handle_registered(self, msg: Message):
        if msg.type == MessageType.REGISTERED.name:
            print('Successfully registered with peer node. State transferred to ESTABLISHED')
            self.state = ChaincodeState.ESTABLISHED.name
        else:
            error: Message = error_message('Chaincode is in CREATED state, can only process messages of type REGISTERED, but received ' + msg.type)
            print(error.payload)
            yield error.to_chaincode_message()

    def handle_ready(self, msg: Message):
        if msg.type == MessageType.READY.name:
            print('Successfully established communication with peer node. State transferred to READY')
            self.state = ChaincodeState.READY.name
        else:
            error: Message = error_message('Chaincode is in ESTABLISHED state, it can only process READY messages, but received ' + msg.type)
            print(error.payload)
            yield error.to_chaincode_message()

    def handle_actions(self, msg: Message):
        log_prefix: str = '%s Received %s, ' % (msg.logging_prefix(), msg.type)
        if msg.type == MessageType.RESPONSE.name or msg.type == MessageType.ERROR.name:
            print(log_prefix + 'handling response...')
            self.handle_response(msg)
        elif msg.type == MessageType.INIT:
            print(log_prefix + 'initializing chaincode...')
            self.init_chaincode(msg)
        elif msg.type == MessageType.TRANSACTION:
            print(log_prefix + 'invoking transaction on chaincode...')
            self.invoke_transaction(msg)
        else:
            error: Message = error_message('Chaincode is in READY state, it cannot process ' + msg.type + ' messages')
            print(error.payload)
            yield error.to_chaincode_message()

    # TODO: Fill remaining methods
    def handle_response(self, msg: Message):
        pass

    def init_chaincode(self, msg: Message):
        pass

    def invoke_transaction(self, msg: Message):
        pass
