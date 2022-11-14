from handler import MessageHandler
from fabric_protos_python.peer import chaincode_pb2 as pb

class ChaincodeStub:
    client: MessageHandler
    channel_id: str
    tx_id: str
    chaincode_input: pb.ChaincodeInput
    signed_proposal: pb.SignedProposal

    def __init__(
            self, 
            client: MessageHandler, 
            channel_id: str, 
            tx_id: str, 
            chaincode_input: pb.ChaincodeInput, 
            signed_proposal: pb.SignedProposal
            ) -> None:
        self.client = client
        self.channel_id = channel_id
        self.tx_id = tx_id
        self.chaincode_input = chaincode_input
        self.signed_proposal = signed_proposal

