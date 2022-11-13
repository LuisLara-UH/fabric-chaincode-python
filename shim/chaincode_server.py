import grpc
import logging
import concurrent.futures
from fabric_protos_python.peer.chaincode_shim_pb2_grpc import Chaincode, ChaincodeServicer, add_ChaincodeServicer_to_server
from fabric_protos_python.peer import chaincode_shim_pb2
from handler import MessageHandler

class ChaincodeServer(ChaincodeServicer):
    chaincode_id: str
    address: str
    chaincode: Chaincode

    def __init__(self) -> None:
        self.chaincode_id = ''

    def Start(self):
        server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        add_ChaincodeServicer_to_server(
            self, server)
        server.add_insecure_port('[::]:9999')
        server.start()
        server.wait_for_termination()

    def Connect(self, request_iterator, context):
        print('Connecting chaincode server...')

        try:
            client = MessageHandler(self.chaincode_id, self.chaincode)
            client.chat_with_peer(request_iterator, context)
        except:
            print('Error while connecting to peer')

if __name__ == '__main__':
    logging.basicConfig()
    ChaincodeServer().Start()