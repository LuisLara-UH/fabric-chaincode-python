from fabric_protos_python.peer.chaincode_shim_pb2_grpc import Chaincode
from fabric_protos_python.peer import chaincode_pb2
from utils import *
from stub import ChaincodeStub

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
            self.handle_message(msg, 'init')
        elif msg.type == MessageType.TRANSACTION:
            print(log_prefix + 'invoking transaction on chaincode...')
            self.handle_message(msg, 'invoke')
        else:
            error: Message = error_message('Chaincode is in READY state, it cannot process ' + msg.type + ' messages')
            print(error.payload)
            yield error.to_chaincode_message()

    # TODO: Fill remaining methods
    def handle_response(self, msg: Message):
        pass

    def handle_message(self, msg: Message, action: str):
        try:
            input = chaincode_pb2.ChaincodeInput.deserializeBinary(msg.payload)
        except:
            print('%s Incorrect payload format. Sending ERROR message back to peer' % msg.logging_prefix())
            nextStateMsg = Message({
                type: MessageType.ERROR.name,
                payload: msg.payload,
                txid: msg.txid,
                channel_id: msg.channel_id
            })

        if input:
            try:
                stub = ChaincodeStub(self, msg.channel_id, msg.txid, input, msg.proposal)
            except Exception as e:
                print('Failed to construct a chaincode stub instance from the INIT message: %s' % e)
                nextStateMsg = Message({
                    type: MessageType.ERROR.name,
                    payload: bytes(e.toString()),
                    txid: msg.txid,
                    channel_id: msg.channel_id
                })

                yield nextStateMsg.to_chaincode_message()

            if stub:
                if action == 'init':
                    resp = self.chaincode.Init(stub)
                    method = 'Init'
                else:
                    resp = self.chaincode.Invoke(stub)
                    method = 'Invoke'

                # check that a response object has been returned otherwise assume an error.

                if not resp or not resp.status:
                    errMsg = '%s Calling chaincode %s() has not called success or error.' % (msg.logging_prefix(), method)
                    print(errMsg)

                    resp = {
                        status: ResponseCode.ERROR.value,
                        message: errMsg
                    }
                
                print('%s Calling chaincode %s(), response status: %s' % (msg.logging_prefix(), method, resp.status))

                response = { message: resp.message, status: resp.status, payload: resp.payload }

                if resp.status >= ResponseCode.ERROR.value:
                    errMsg = '%s Calling chaincode %s() returned error response [%s]. Sending COMPLETED message back to peer' % (msg.logging_prefix(), method, resp.message)
                    print(errMsg)

                    nextStateMsg = Message({
                        type: MessageType.COMPLETED.name,
                        payload: response.serializeBinary(),
                        txid: msg.txid,
                        channel_id: msg.channel_id,
                        chaincode_event: stub.chaincodeEvent
                    })
                else:
                    print('%s Calling chaincode %s() succeeded. Sending COMPLETED message back to peer' % (msg.logging_prefix(), method))

                    nextStateMsg = Message({
                        type: MessageType.COMPLETED.name,
                        payload: response.serializeBinary(),
                        txid: msg.txid,
                        channel_id: msg.channel_id,
                        chaincode_event: stub.chaincodeEvent
                    })

                yield nextStateMsg.to_chaincode_message()
        else:
            yield nextStateMsg.to_chaincode_message()
