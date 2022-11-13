from enum import Enum

class MessageType(Enum):
    REGISTERED = 'REGISTERED', 	    # ChaincodeMessage.Type.REGISTERED
    READY = 'READY', 			    # ChaincodeMessage.Type.READY
    RESPONSE = 'RESPONSE',		    # ChaincodeMessage.Type.RESPONSE
    ERROR = 'ERROR',		        # ChaincodeMessage.Type.ERROR
    INIT = 'INIT',				    # ChaincodeMessage.Type.INIT
    TRANSACTION = 'TRANSACTION',	# ChaincodeMessage.Type.TRANSACTION
    COMPLETED = 'COMPLETED',		# ChaincodeMessage.Type.COMPLETED

class Message:
    type: str               # ChaincodeMessage.Type
    timestamp: int          # ChaincodeMessage.Timestamp
    payload: bytes          # ChaincodeMessage.Payload
    txid: str               # ChaincodeMessage.Txid
    proposal: dict          # ChaincodeMessage.Proposal
    chaincode_event: dict   # ChaincodeMessage.ChaincodeEvent
    channel_id: str         # ChaincodeMessage.ChannelId

    def __init__(self, chaincode_message: object) -> None:
        self.type = chaincode_message.type
        self.timestamp = chaincode_message.timestamp
        self.payload = chaincode_message.payload
        self.txid = chaincode_message.txid
        self.proposal = chaincode_message.proposal
        self.chaincode_event = chaincode_message.chaincode_event
        self.channel_id = chaincode_message.channel_id

    def to_chaincode_message(self) -> object:
        return {
            type: self.type,
            timestamp: self.timestamp,
            payload: self.payload,
            txid: self.txid,
            proposal: self.proposal,
            chaincode_event: self.chaincode_event,
            channel_id: self.channel_id
        }
    
    def logging_prefix(self):
        return '[%s-%s]' % (self.channel_id, self.txid)

def error_message(text: str) -> Message:
    return Message({
        type: MessageType.ERROR.name,
        payload: bytes(text)
    })

class ChaincodeState(Enum):
    CREATED = 'CREATED',
    ESTABLISHED = 'ESTABLISHED',
    READY = 'READY'
