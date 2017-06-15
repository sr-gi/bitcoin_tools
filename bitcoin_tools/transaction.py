from bitcoin_tools.keys import serialize_pk, ecdsa_tx_sign
from bitcoin_tools.script import InputScript, OutputScript, Script, SIGHASH_ALL, SIGHASH_SINGLE, SIGHASH_NONE, \
    SIGHASH_ANYONECANPAY
from bitcoin_tools.utils import change_endianness, decode_varint, encode_varint, int2bytes, \
    is_public_key, is_btc_addr, parse_element, parse_varint, get_prev_ScriptPubKey
from copy import deepcopy
from ecdsa import SigningKey


class TX:
    """ Defines a class TX (transaction) that holds all the modifiable fields of a Bitcoin transaction, such as
    version, number of inputs, reference to previous transactions, input and output scripts, value, etc.
    """

    def __init__(self):
        self.version = ""
        self.inputs = ""
        self.outputs = ""
        self.nLockTime = ""
        self.prev_tx_id = []
        self.prev_out_index = []
        self.scriptSig = []
        self.scriptSig_len = []
        self.nSequence = []
        self.value = []
        self.scriptPubKey = []
        self.scriptPubKey_len = []

        self.offset = 0
        self.hex = ""

    def deserialize(self):
        """ Displays all the information related to the transaction object, properly split and arranged.

        :param self: self
        :type self: TX
        :return: None.
        :rtype: None
        """

        print "version: " + self.version
        print "number of inputs: " + self.inputs + " (" + str(decode_varint(self.inputs)) + ")"
        for i in range(len(self.scriptSig)):
            print "input " + str(i)
            print "\t previous txid (little endian): " + self.prev_tx_id[i] + " (" + change_endianness(
                self.prev_tx_id[i]) + ")"
            print "\t previous tx output (little endian): " + self.prev_out_index[i] + " (" + str(
                int(change_endianness(self.prev_out_index[i]), 16)) + ")"
            print "\t input script (scriptSig) length: " + self.scriptSig_len[i] + " (" + str(
                int(self.scriptSig_len[i], 16)) + ")"
            print "\t input script (scriptSig): " + self.scriptSig[i].content
            print "\t decoded scriptSig: " + Script.deserialize(self.scriptSig[i].content)
            print "\t nSequence: " + self.nSequence[i]
        print "number of outputs: " + self.outputs + " (" + str(decode_varint(self.outputs)) + ")"
        for i in range(len(self.scriptPubKey)):
            print "output " + str(i)
            print "\t Satoshis to be spent (little endian): " + self.value[i] + " (" + str(
                int(change_endianness(self.value[i]), 16)) + ")"
            print "\t output script (scriptPubKey) length: " + self.scriptPubKey_len[i] + " (" + str(
                int(change_endianness(self.scriptPubKey_len[i]), 16)) + ")"
            print "\t output script (scriptPubKey): " + self.scriptPubKey[i].content
            print "\t decoded scriptPubKey: " + Script.deserialize(self.scriptPubKey[i].content)

        print "nLockTime: " + self.nLockTime

    def serialize(self):
        """ Serialize all the transaction fields arranged in the proper order, resulting in a hexadecimal string
        ready to be broadcast to the network.

        :param self: self
        :type self: TX
        :return: Serialized transaction representation (hexadecimal).
        :rtype: hex str
        """

        serialized_tx = self.version + self.inputs

        for i in range(decode_varint(self.inputs)):
            serialized_tx += self.prev_tx_id[i] + self.prev_out_index[i] + self.scriptSig_len[i] \
                             + self.scriptSig[i].content + self.nSequence[i]

        serialized_tx += self.outputs

        if decode_varint(self.outputs) != 0:
            for i in range(len(self.scriptPubKey)):
                serialized_tx += self.value[i] + self.scriptPubKey_len[i] + self.scriptPubKey[i].content

        serialized_tx += self.nLockTime

        return serialized_tx

    # ToDo: Add documentation to the rest of the TX class

    @classmethod
    def build_from_hex(cls, hex_tx):
        tx = cls()
        tx.hex = hex_tx

        tx.version = parse_element(tx, 4)
        tx.inputs = parse_varint(tx)

        for i in range(decode_varint(tx.inputs)):
            tx.prev_tx_id.append(parse_element(tx, 32))
            tx.prev_out_index.append(parse_element(tx, 4))
            tx.scriptSig_len.append(parse_varint(tx))
            iscript = InputScript.from_hex(parse_element(tx, decode_varint(tx.scriptSig_len[i])))
            tx.scriptSig.append(iscript)
            tx.nSequence.append(parse_element(tx, 4))

        tx.outputs = parse_varint(tx)

        for i in range(decode_varint(tx.outputs)):
            tx.value.append(parse_element(tx, 8))
            tx.scriptPubKey_len.append(parse_varint(tx))
            tx.scriptPubKey.append(OutputScript.from_hex(parse_element(tx, decode_varint(tx.scriptPubKey_len[i]))))

        tx.nLockTime = parse_element(tx, 4)

        if tx.offset != len(tx.hex):
            raise Exception("There is some error in the serialized transaction passed as input. Transaction can't"
                            "be build")
        else:
            tx.offset = 0

        return tx

    @classmethod
    def build_from_scripts(cls, prev_tx_id, prev_out_index, value, scriptSig, scriptPubKey, fees=None):
        tx = cls()

        if len(prev_tx_id) is not len(prev_out_index) or len(prev_tx_id) is not len(scriptSig):
            raise Exception("The number ofs UTXOs to spend must match with the number os ScriptSigs to set.")
        elif len(scriptSig) == 0 or len(scriptPubKey) == 0:
            raise Exception("Scripts can't be empty")
        # ToDo: add more strict checks
        else:
            tx.version = "01000000"  # 4-byte version number

            # INPUTS
            n_inputs = len(prev_tx_id)  # Number of inputs (varint).
            tx.inputs = encode_varint(n_inputs)
            for i in range(n_inputs):
                tx.prev_tx_id.append(change_endianness(prev_tx_id[i]))  # 32-byte hash of the previous transaction.
                tx.prev_out_index.append(change_endianness(int2bytes(prev_out_index[i], 4)))  # 4-byte output index

            # ScriptSig
            for i in range(n_inputs):
                tx.scriptSig_len.append(int2bytes(len(scriptSig[i].content) / 2, 1))  # Input script length (varint).
                tx.scriptSig.append(scriptSig[i])  # Input script.

                tx.nSequence.append("ffffffff")  # 4-byte sequence number

            # OUTPUTS
            n_outputs = len(scriptPubKey)  # Number of outputs (varint).
            tx.outputs = encode_varint(n_outputs)

            # ScriptPubKey
            for i in range(n_outputs):
                tx.value.append(change_endianness(int2bytes(value[i], 8)))  # 8-byte field (64 bit int) Satoshi value

                tx.scriptPubKey_len.append(encode_varint(
                    len(scriptPubKey[i].content) / 2))  # Output script length (varint).
                tx.scriptPubKey.append(scriptPubKey[i])  # Output script.

            tx.nLockTime = "00000000"  # 4-byte lock time field

            tx.hex = tx.serialize()

            # ToDo: add fees

        return tx

    @classmethod
    def build_from_io(cls, prev_tx_id, prev_out_index, value, outputs, fees=None, network='test'):
        ins = []
        outs = []

        if isinstance(prev_tx_id, str):
            prev_tx_id = [prev_tx_id]
        if isinstance(prev_out_index, int):
            prev_out_index = [prev_out_index]
        if isinstance(value, int):
            value = [value]
        if isinstance(outputs, str) or (isinstance(outputs, list) and isinstance(outputs[0], int)):
            outputs = [outputs]

        # ToDo: Deal with fees

        if len(prev_tx_id) != len(prev_out_index):
            raise Exception("Previous transaction id and index number of elements must match. " + str(len(prev_tx_id))
                            + "!= " + str(len(prev_out_index)))
        elif len(value) != len(outputs):
            raise Exception("Each output must have set a Satoshi amount. Use 0 if no value is going to be transferred.")

        for o in outputs:
            if isinstance(o, list) and o[0] in range(1, 15):
                pks = [is_public_key(pk) for pk in o[1:]]
                if all(pks):
                    oscript = OutputScript.P2MS(o[0], len(o) - 1, o[1:])
                else:
                    raise Exception("Bad output")
            elif is_public_key(o):
                oscript = OutputScript.P2PK(o)
            elif is_btc_addr(o):
                oscript = OutputScript.P2PKH(o)
            else:
                # ToDo: Handle P2SH outputs as an additional elif
                raise Exception("Bad output")

            outs.append(deepcopy(oscript))

        for i in range(len(prev_tx_id)):
            # Temporarily set IS content to 0, since data will be signed afterwards.
            iscript = InputScript()
            ins.append(iscript)

        tx = cls.build_from_scripts(prev_tx_id, prev_out_index, value, ins, outs)

        return tx

    def signature_form(self, index, hashflag=SIGHASH_ALL, network='test'):

        tx = deepcopy(self)
        for i in range(len(tx.scriptSig)):
            if i is index:
                # Since tx_id and out_index has been already encoded into the tx format, they should be parsed to
                # perform the query to the server API.
                tx_id = change_endianness(tx.prev_tx_id[i])
                out_index = int(change_endianness(self.prev_out_index[i]), 16)
                script, t = get_prev_ScriptPubKey(tx_id, out_index, network)
                # Once we get the previous UTXO script, the inputScript is temporarily set to it in order to sign
                # the transaction.
                tx.scriptSig[i] = InputScript.from_hex(script)
                tx.scriptSig[i].type = t
                tx.scriptSig_len[i] = int2bytes(len(tx.scriptSig[i].content) / 2, 1)
            elif tx.scriptSig[i].content != "":
                # All other scriptSig field are emptied and their length is set to 0.
                tx.scriptSig[i] = InputScript()
                tx.scriptSig_len[i] = int2bytes(len(tx.scriptSig[i].content) / 2, 1)

        if hashflag is SIGHASH_SINGLE:
            # ToDo: Deal with SIGHASH_SINGLE
            pass
        elif hashflag is SIGHASH_NONE:
            # Empty all the scriptPubKeys and set the length and the output counter to 0.
            tx.outputs = encode_varint(0)
            tx.scriptPubKey = OutputScript()
            tx.scriptPubKey_len = int2bytes(len(tx.scriptPubKey.content) / 2, 1)
        elif hashflag is SIGHASH_ANYONECANPAY:
            # ToDo: Deal with SIGHASH_ANYONECANPAY
            pass

        return tx

    def sign(self, sk, index, hashflag=SIGHASH_ALL):
        if isinstance(sk, list) and isinstance(index, int):  # In case a list for multisig is received as only input.
            sk = [sk]
        if isinstance(sk, SigningKey):
            sk = [sk]
        if isinstance(index, int):
            index = [index]

        for i in range(len(sk)):
            unsigned_tx = self.signature_form(index[i], hashflag)
            if isinstance(sk[i], list) and unsigned_tx.scriptSig[index[i]].type is "P2MS":
                sigs = []
                for k in sk[i]:
                    sigs.append(ecdsa_tx_sign(unsigned_tx.serialize(), k, hashflag))
                iscript = InputScript.P2MS(sigs)
            elif isinstance(sk[i], SigningKey) and unsigned_tx.scriptSig[index[i]].type is "P2PK":
                s = ecdsa_tx_sign(unsigned_tx.serialize(), sk[i], hashflag)
                iscript = InputScript.P2PK(s)
            elif isinstance(sk[i], SigningKey) and unsigned_tx.scriptSig[index[i]].type is "P2PKH":
                s = ecdsa_tx_sign(unsigned_tx.serialize(), sk[i], hashflag)
                pk = serialize_pk(sk[i].get_verifying_key())
                iscript = InputScript.P2PKH(s, pk)
            elif unsigned_tx.scriptSig[index[i]].type is "unknown":
                raise Exception("Unknown previous transaction output script type. Can't sign the transaction.")
            else:
                # ToDo: Handle P2SH outputs as an additional elif
                raise Exception("Can't sign input " + str(i) + " with the provided data.")

            self.scriptSig[i] = iscript
            self.scriptSig_len[i] = encode_varint(len(iscript.content) / 2)

        self.hex = self.serialize()
