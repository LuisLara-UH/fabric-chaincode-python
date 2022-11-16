from fabric_protos_python.peer import chaincode_pb2 as pb
from fabric_protos_python.common import common_pb2 as cm_pb
from fabric_protos_python.peer import proposal_pb2 as pr_pb
from fabric_protos_python import msp
from fabric_protos_python.peer import chaincode_event_pb2 as e_pb
import os

env = os.environ.get("PYTHON_ENV")

VALIDATION_PARAMETER = 'VALIDATION_PARAMETER'
EMPTY_KEY_SUBSTITUTE = '\x01'

class ChaincodeStub:
    channel_id: str
    tx_id: str
    chaincode_input: pb.ChaincodeInput
    signed_proposal: pr_pb.SignedProposal
    validation_parameter_meta_key: str
    creator: dict
    txTimestamp: any # Type?

    def __init__(
            self, 
            client, 
            channel_id: str, 
            tx_id: str, 
            chaincode_input: pb.ChaincodeInput, 
            signed_proposal: pr_pb.SignedProposal
            ) -> None:
        self.client = client
        self.channel_id = channel_id
        self.tx_id = tx_id
        self.chaincode_input = chaincode_input
        self.signed_proposal = signed_proposal

        self.validationParameterMetakey = VALIDATION_PARAMETER;

        if self.signed_proposal:
            decoded_sp = {
                signature: self.signed_proposal.getSignature()
            }

            try:
                proposal = pb.Proposal.deserializeBinary(self.signed_proposal.getProposalBytes())
                decoded_sp.proposal = {}
                self.proposal = proposal
            except Exception as e:
                raise Exception('Failed extracting proposal from signedProposal. ' + e)

            proposal_header = proposal.getHeader_asU8()
            if not proposal_header or proposal_header.length == 0:
                raise Exception('Proposal header is empty')
            

            proposal_payload = proposal.getPayload_asU8()
            if not proposal_payload or proposal_payload.length == 0:
                raise Exception('Proposal payload is empty')

            try:
                header = cm_pb.Header.deserializeBinary(proposal_header)
                decoded_sp.proposal.header = {}
            except Exception as e:
                raise Exception('Could not extract the header from the proposal: ' + e)

            try:
                signature_header = cm_pb.SignatureHeader.deserializeBinary(header.getSignatureHeader())
                decoded_sp.proposal.header.signatureHeader = {nonce: signature_header.getNonce_asU8(), creator_u8: signature_header.getCreator_asU8()}
            except Exception as e:
                raise Exception('Decoding SignatureHeader failed: ' + e)

            try:
                creator = msp.SerializedIdentity.deserializeBinary(signature_header.getCreator_asU8())
                decoded_sp.proposal.header.signatureHeader.creator = creator
                self.creator = {mspid: creator.getMspid(), idBytes: creator.getIdBytes_asU8()}
            except Exception as e:
                raise Exception('Decoding SerializedIdentity failed: ' + e)

            try:
                channel_header = cm_pb.ChannelHeader.deserializeBinary(header.getChannelHeader_asU8())
                decoded_sp.proposal.header.channelHeader = channel_header
                self.txTimestamp = channel_header.getTimestamp()
            except Exception as e:
                raise Exception('Decoding ChannelHeader failed: ' + e)

            try:
                ccpp = pb.ChaincodeProposalPayload.deserializeBinary(proposal_payload)
                decoded_sp.proposal.payload = ccpp
            except Exception as e:
                raise Exception('Decoding ChaincodeProposalPayload failed: %s' + e)

            # self.transientMap = new Map();
            # ccpp.getTransientmapMap().forEach((value, key) => {
            #     this.transientMap.set(key, Buffer.from(value));
            # });

            self.signed_proposal = decoded_sp

            # this.binding = computeProposalBinding(decodedSP);

    def getArgs(self):
        """
        Returns the arguments as array of strings from the chaincode invocation request.
        """
        return self.args

    
    def getStringArgs(self):
        """ Returns the arguments as array of strings from the chaincode invocation request """
        return self.args

    def getBufferArgs(self):
        return self.bufferArgs

    def getFunctionAndParameters(self):
        """
        Returns an object containing the chaincode function name to invoke, and the array
        of arguments to pass to the target function
        """
        values = self.getStringArgs()
        if values.Length >= 1:
            return {
                fcn: values[0],
                params: values.slice(1)
            }
        else:
            return {
                fcn: '',
                params: []
            }

    def getTxID(self):
        """
        Returns the transaction ID for the current chaincode invocation request. The transaction
        ID uniquely identifies the transaction within the scope of the channel.
        """
        return self.tx_id

    
    def getChannelID(self):
        """
        Returns the channel ID for the proposal for chaincode to process.
        This would be the 'channel_id' of the transaction proposal
        """
        return self.channel_id

    def getCreator(self):
        """
        This object contains the essential identity information of the chaincode invocation's submitter,
        including its organizational affiliation (mspid) and certificate (id_bytes)
        """
        return self.creator

    def getMspID(self):
        """
        Returns the MSPID of the peer that started this chaincode
        """
        if 'CORE_PEER_LOCALMSPID' in env:
            return env.CORE_PEER_LOCALMSPID
        else:
            raise Exception('CORE_PEER_LOCALMSPID is unset in chaincode process')

    # def getTransient(self):
    #     """
    #     Returns the transient map that can be used by the chaincode but not
    #     saved in the ledger, such as cryptographic information for encryption and decryption
    #     """
    #     return self.transientMap

    
    def getSignedProposal(self):
        """
        Returns a fully decoded object of the signed transaction proposal
        """
        return self.signedProposal

    def getTxTimestamp(self):
        """
        Returns the timestamp when the transaction was created. This
        is taken from the transaction {@link ChannelHeader}, therefore it will indicate the
        client's timestamp, and will have the same value across all endorsers.
        """
        return self.txTimestamp
    
    def getBinding(self):
        return self.binding

    async def getState(self, key):
        """
        Retrieves the current value of the state variable <code>key</code>
        """
        print('getState called with key:%s', key)
        # Access public data by setting the collection to empty string
        collection = ''
        return await self.handler.handleGetState(collection, key, self.channel_id, self.tx_id)

    async def putState(self, key, value):
        """
        Writes the state variable <code>key</code> of value <code>value</code>
        to the state store. If the variable already exists, the value will be
        overwritten.
        """
        # Access public data by setting the collection to empty string
        collection = ''
        if isinstance(value, str):
            value = bytes(value)
        return await self.handler.handlePutState(collection, key, value, self.channel_id, self.tx_id)

    async def deleteState(self, key):
        """
        Deletes the state variable <code>key</code> from the state store.
        """
        # Access public data by setting the collection to empty string
        collection = ''
        return await self.handler.handleDeleteState(collection, key, self.channel_id, self.tx_id)

    async def setStateValidationParameter(self, key, ep):
        """
        Sets the key-level endorsement policy for 'key'
        """
        # Access public data by setting the collection to empty string
        collection = ''
        return self.handler.handlePutStateMetadata(collection, key, self.validation_parameter_meta_key, ep, self.channel_id, self.tx_id)

    async def getStateValidationParameter(self, key):
        """
        getStateValidationParameter retrieves the key-level endorsement policy
        for `key`. Note that this will introduce a read dependency on `key` in
        the transaction's readset.
        """
        # Access public data by setting the collection to empty string
        collection = ''
        res = await self.handler.handleGetStateMetadata(collection, key, self.channel_id, self.tx_id)
        return res[self.validationParameterMetakey]
    
    async def invokeChaincode(self, chaincode_name, args, channel):
        """
        Locally calls the specified chaincode <code>invoke()</code> using the
        same transaction context; that is, chaincode calling chaincode doesn't
        create a new transaction message.<br><br>
        """
        if channel and channel.length > 0:
            chaincode_name = chaincode_name + '/' + channel
        return await self.handler.handleInvokeChaincode(chaincode_name, args, self.channel_id, self.txId)

    def setEvent(self, name, payload):
        """
        Allows the chaincode to propose an event on the transaction proposal. When the transaction
        is included in a block and the block is successfully committed to the ledger, the block event
        will be delivered to the current event listeners that have been registered with the peer's
        event producer. Note that the block event gets delivered to the listeners regardless of the
        status of the included transactions (can be either valid or invalid), so client applications
        are responsible for checking the validity code on each transaction. Consult each SDK's documentation
        for details.
        """
        if not isinstance(name, str) or name == '':
            raise Exception('Event name must be a non-empty string')

        # Because this is passed directly into gRPC as an object, rather
        # than a serialized protocol buffer message, it uses snake_case
        # rather than camelCase like the rest of the code base.
        self.chaincodeEvent = e_pb.ChaincodeEvent()
        self.chaincodeEvent.setPayload(payload)
        self.chaincodeEvent.setEventName(name)

    async def getPrivateData(self, collection, key):
        """
        getPrivateData returns the value of the specified `key` from the specified
        `collection`. Note that GetPrivateData doesn't read data from the
        private writeset, which has not been committed to the `collection`. In
        other words, GetPrivateData doesn't consider data modified by PutPrivateData
        that has not been committed.
        """
        print('getPrivateData called with collection:%s, key:%s' % (collection, key))
        if not collection or not isinstance(collection, str):
            raise Exception('collection must be a valid string')
        if not key or not isinstance(key, str):
            raise Exception('key must be a valid string')

        return await self.handler.handleGetState(collection, key, self.channel_id, self.tx_id)

    async def getPrivateDataHash(self, collection, key):
        """
        getPrivateDataHash returns the hash of the value of the specified `key` from
        the specified `collection`.
        """
        print('getPrivateDataHash called with collection:%s, key:%s' % (collection, key))
        if not collection or not isinstance(collection, str):
            raise Exception('collection must be a valid string')
        if not key or not isinstance(key, str): 
            raise Exception('key must be a valid string')

        return await self.handler.handleGetPrivateDataHash(collection, key, self.channel_id, self.tx_id)

    async def putPrivateData(self, collection, key, value):
        """
        putPrivateData puts the specified `key` and `value` into the transaction's
        private writeSet. Note that only hash of the private writeSet goes into the
        transaction proposal response (which is sent to the client who issued the
        transaction) and the actual private writeSet gets temporarily stored in a
        transient store. PutPrivateData doesn't effect the `collection` until the
        transaction is validated and successfully committed. Simple keys must not be
        an empty string and must not start with null character (0x00), in order to
        avoid range query collisions with composite keys, which internally get
        prefixed with 0x00 as composite key namespace.
        """
        print('putPrivateData called with collection:%s, key:%s' % (collection, key))
        if not collection or not isinstance(collection, str):
            raise Exception('collection must be a valid string')
        if not key or not isinstance(key, str):
            raise Exception('key must be a valid string')
        if not value:
            raise Exception('value must be valid')
        if isinstance(value, str):
            value = bytes(value)

        return self.handler.handlePutState(collection, key, value, self.channel_id, self.tx_id)

    async def deletePrivateData(self, collection, key):
        """
        deletePrivateData records the specified `key` to be deleted in the private writeset of
        the transaction. Note that only hash of the private writeset goes into the
        transaction proposal response (which is sent to the client who issued the
        transaction) and the actual private writeset gets temporarily stored in a
        transient store. The `key` and its value will be deleted from the collection
        when the transaction is validated and successfully committed.
        """
        print('deletePrivateData called with collection:%s, key:%s' % (collection, key))
        if not collection or not isinstance(collection, str): 
            raise Exception('collection must be a valid string')
        if not key or not isinstance(key, str): 
            raise Exception('key must be a valid string')

        return self.handler.handleDeleteState(collection, key, self.channel_id, self.tx_id)

    async def purgePrivateData(self, collection, key):
        """
        PurgePrivateData records the specified `key` to be purged in the private writeset
        of the transaction. Note that only hash of the private writeset goes into the
        transaction proposal response (which is sent to the client who issued the
        transaction) and the actual private writeset gets temporarily stored in a
        transient store. The `key` and its value will be deleted from the collection
        when the transaction is validated and successfully committed, and will
        subsequently be completely removed from the private data store (that maintains
        the historical versions of private writesets) as a background operation.
        """
        # Access public data by setting the collection to empty string
        print('purgePrivateData called with collection:%s, key:%s' % (collection, key))
        if not collection or not isinstance(collection, str):
            raise Exception('collection must be a valid string')
        if not key or not isinstance(key, str):
            raise Exception('key must be a valid string')
        
        return await self.handler.handlePurgeState(collection, key, self.channel_id, self.tx_id)

    async def setPrivateDataValidationParameter(self, collection, key, ep):
        """
        SetPrivateDataValidationParameter sets the key-level endorsement policy
        for the private data specified by `key`.
        """
        return self.handler.handlePutStateMetadata(collection, key, self.validationParameterMetakey, ep, self.channel_id, self.tx_id)
    
    
    async def getPrivateDataValidationParameter(self,collection, key):
        """
        GetPrivateDataValidationParameter retrieves the key-level endorsement
        policy for the private data specified by `key`. Note that this introduces
        a read dependency on `key` in the transaction's readset.
        """
        res = await self.handler.handleGetStateMetadata(collection, key, self.channel_id, self.tx_id)
        return res[self.validationParameterMetakey]
