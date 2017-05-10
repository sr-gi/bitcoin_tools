from copy import deepcopy
from utils.utils import change_endianness, decode_varint, encode_varint, int2bytes, \
    is_public_key, is_btc_addr, parse_element, parse_varint
from script.script import InputScript, OutputScript, Script
from utils.utils import get_prev_ScriptPubKey
from pybitcointools import ecdsa_tx_sign
from ecdsa import SigningKey
from wallet.keys import serialize_pk, serialize_sk


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

        for i in range(len(self.prev_tx_id)):
            serialized_tx += self.prev_tx_id[i] + self.prev_out_index[i] + self.scriptSig_len[i] \
                             + self.scriptSig[i].content + self.nSequence[i]

        serialized_tx += self.outputs

        for i in range(len(self.scriptPubKey)):
            serialized_tx += self.value[i] + self.scriptPubKey_len[i] + self.scriptPubKey[i].content

        serialized_tx += self.nLockTime

        return serialized_tx

    def build_from_hex(self, hex_tx):

        self.hex = hex_tx

        scriptSig = InputScript()
        scriptPubKey = OutputScript()

        self.version = parse_element(self, 4)
        self.inputs = parse_varint(self)

        for i in range(decode_varint(self.inputs)):
            self.prev_tx_id.append(parse_element(self, 32))
            self.prev_out_index.append(parse_element(self, 4))
            self.scriptSig_len.append(parse_varint(self))
            scriptSig.from_hex(parse_element(self, decode_varint(self.scriptSig_len[i])))
            self.scriptSig.append(scriptSig)
            self.nSequence.append(parse_element(self, 4))

        self.outputs = parse_varint(self)

        for i in range(decode_varint(self.outputs)):
            self.value.append(parse_element(self, 8))
            self.scriptPubKey_len.append(parse_varint(self))
            scriptPubKey.from_hex(parse_element(self, decode_varint(self.scriptPubKey_len[i])))
            self.scriptPubKey.append(scriptPubKey)

        self.nLockTime = parse_element(self, 4)

        if self.offset != len(self.hex):
            raise Exception("There is some error in the serialized transaction passed as input. Transaction can't"
                            "be build")
        else:
            self.offset = 0

    def build_from_scripts(self, prev_tx_id, prev_out_index, value, scriptSig, scriptPubKey, fees=None):
        if len(prev_tx_id) is not len(prev_out_index) or len(prev_tx_id) is not len(scriptSig):
            raise Exception("The number ofs UTXOs to spend must match with the number os ScriptSigs to set.")
        elif len(scriptSig) == 0 or len(scriptPubKey) == 0:
            raise Exception("Scripts can't be empty")
        # ToDo: add more strict checks
        else:
            self.version = "01000000"  # 4-byte version number

            # INPUTS
            n_inputs = len(prev_tx_id)  # Number of inputs (varint).
            self.inputs = encode_varint(n_inputs)
            for i in range(n_inputs):
                self.prev_tx_id.append(change_endianness(prev_tx_id[i]))  # 32-byte hash of the previous transaction.
                self.prev_out_index.append(change_endianness(int2bytes(prev_out_index[i], 4)))  # 4-byte output index

            # ScriptSig
            for i in range(n_inputs):
                self.scriptSig_len.append(int2bytes(len(scriptSig[i].content) / 2, 1))  # Input script length (varint).
                self.scriptSig.append(scriptSig[i])  # Input script.

                self.nSequence.append("ffffffff")  # 4-byte sequence number

            # OUTPUTS
            n_outputs = len(scriptPubKey)  # Number of outputs (varint).
            self.outputs = encode_varint(n_outputs)

            # ScriptPubKey
            for i in range(n_outputs):
                self.value.append(change_endianness(int2bytes(value[i], 8)))  # 8-byte field (64 bit int) Satoshi value

                self.scriptPubKey_len.append(encode_varint(
                    len(scriptPubKey[i].content) / 2))  # Output script length (varint).
                self.scriptPubKey.append(scriptPubKey[i])  # Output script.

            self.nLockTime = "00000000"  # 4-byte lock time field

            self.hex = self.serialize()

            # ToDo: add fees

    def build_from_io(self, prev_tx_id, prev_out_index, value, outputs, fees=None, network='test'):
        scriptSig = InputScript()
        scriptPubKey = OutputScript()
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
                    scriptPubKey.P2MS(o[0], len(o) - 1, o[1:])
            elif is_public_key(o):
                scriptPubKey.P2PK(o)
            elif is_btc_addr(o):
                scriptPubKey.P2PKH(o)
            else:
                # ToDo: Handle P2SH outputs as an additional elif
                raise Exception("Bad output")

            outs.append(deepcopy(scriptPubKey))

        for i in range(len(prev_tx_id)):
            script, t = get_prev_ScriptPubKey(prev_tx_id[i], prev_out_index[i], network)
            scriptSig.from_hex(script)
            scriptSig.type = t
            ins.append(scriptSig)

        self.build_from_scripts(prev_tx_id, prev_out_index, value, ins, outs)

    def sign(self, sk, index):
        if isinstance(sk, list) and isinstance(index, int):  # In case a list for multisig is received as only input.
            sk = [sk]
        if isinstance(sk, SigningKey):
            sk = [sk]
        if isinstance(index, int):
            index = [index]

        unsigned_tx = self.serialize()
        scriptSig = InputScript()

        for i in range(len(sk)):
            if isinstance(sk[i], list) and self.scriptSig[index[i]].type is "P2MS":
                sigs = []
                for k in sk[i]:
                    sigs.append(ecdsa_tx_sign(unsigned_tx, serialize_sk(k)))
                scriptSig.P2MS(sigs)
            elif self.scriptSig[index[i]].type is "P2PK":
                s = ecdsa_tx_sign(unsigned_tx, serialize_sk(sk[i]))
                scriptSig.P2PK(s)
            elif self.scriptSig[index[i]].type is "P2PKH":
                s = ecdsa_tx_sign(unsigned_tx, serialize_sk(sk[i]))
                pk = serialize_pk(sk[i].get_verifying_key())
                scriptSig.P2PKH(s, pk)
            elif self.scriptSig[index[i]].type is "unknown":
                raise Exception("Unknown previous transaction output script type. Can't sign the transaction.")
            else:
                # ToDo: Handle P2SH outputs as an additional elif
                raise Exception("Can't sign input " + str(i) + " with the provided data.")

            self.scriptSig[i] = scriptSig
            self.scriptSig_len[i] = encode_varint(len(scriptSig.content) / 2)

        self.hex = self.serialize()


    #     def add_fees(self, output=0, amount=None):
    #         """ Adds the chosen fees to the chosen output of the transaction.
    #        :param self: self
    #        :type self: TX
    #        :param output: The output where the fees will be charged. The first input will be chosen by default (output=0).
    #        :type output: int
    #        :param amount: The amount of fees to be charged. The minimum fees wfrom bitcoin.core.script import CScript
    # from binascii import a2b_hexil be charged by default (amount=None).
    #        :type amount: int.
    #        :return: The maximum size of the transaction.
    #        :rtype: int
    #        """
    #
    #         # Minimum fees will be applied
    #         if amount is None:
    #             fees = self.get_p2pkh_tx_max_len() * RECOMMENDED_MIN_TX_FEE
    #
    #         else:
    #             fees = amount
    #
    #         # Get the bitcoin amount from the chosen output, cast it into integer and subtract the fees.
    #         amount = int(change_endianness(self.value[output]), 16) - fees
    #         # Fill all the missing bytes up to the value length(8 bytes) and get the value back to its LE representation.
    #         self.value[output] = change_endianness(int2bytes(amount, 8))
    #         # Update the hex representation of the transaction
    #         self.to_hex()
    #
    #     def get_p2pkh_tx_max_len(self):
    #         """ Computes the maximum transaction length for a default Bitcoin transactions, that is, all the scriptSig
    #         values are P2PKH scripts. The method can be used approximate the final transaction length and in that way
    #         calculate the minimum transactions fees than can be applied to the transaction.
    #        :param self: self
    #        :type self: TX
    #        :return: The maximum size of the transaction.
    #        :rtype: int
    #        """
    #
    #         # Max length is approximated by calculating the length of the non-signed transaction, and adding the maximum
    #         # length of a standard P2PKH sigScript, which corresponds to the length of two data pushes (2 * OP_PUSH_LEN)
    #         # plus the size of the signature (at most MAX_SIG_LEN) plus the length of a Bitcoin public key (PK_LEN).
    #         max_len = len(self.hex) / 2 + ((2 * OP_PUSH_LEN + MAX_SIG_LEN + PK_LEN) * int(self.inputs))
    #         # An additional byte for each input should be added to the max length representing the sigScript length
    #         # of each input. However, since we had previously added a byte to temporary fill both sigScript and
    #         # sigScript_len field (00) for each input, it will not be necessary.
    #
    #         return max_len
    #
    # def build_p2pkh_std_tx(self, prev_tx_id, prev_out_index, value, scriptPubKey, scriptSig=None, fees=None):
    #     """ Builds a standard P2PKH transaction using default parameters such as version = 01000000 or
    #     nSequence = FFFFFFFF.
    #
    #     :param self: self
    #     :type self: TX
    #     :param prev_tx_id: List of references to the previous transactions from where the current transaction will
    #     redeem some bitcoins.
    #     :type prev_tx_id: str list
    #     :param prev_out_index: List of references transaction output from where the funds will be redeemed.
    #     :type prev_out_index: int list
    #     :param value: List of value to be transferred to the desired destinations, in Satoshis (The difference between
    #     the total input value and the total output value will be charged as fee).
    #     :type value: int list
    #     :param scriptPubKey: List of scripts that will lock the outputs of the current transaction.
    #     :type scriptPubKey: hex str list
    #     :param scriptSig: List of scripts that will provide proof of fulfillment of the redeem conditions from the
    #     previous transactions (referenced by the prev_tx_id and prev_out_index).
    #     :type scriptSig: hex str list
    #     :return: None.
    #     :rtype: None
    #     """
    #
    #     # 4-byte version number (default: 01 little endian).
    #     self.version = "01000000"
    #
    #     #############
    #     #   INPUTS  #
    #     #############
    #
    #     # Number of inputs (varint, between 1-9 bytes long).
    #     n_inputs = len(prev_tx_id)
    #     self.inputs = encode_varint(n_inputs)  # e.g "01"
    #
    #     # Reference to the UTXO to redeem.
    #
    #     # 32-byte hash of the previous transaction (little endian).
    #     for i in range(n_inputs):
    #         self.prev_tx_id.append(change_endianness(prev_tx_id[i]))
    #         # e.g "c7495bd4c5102d7e40c231279eaf9877e825364847ddebc34911f5a0f0d79ea5"
    #
    #         # 4-byte output index (little endian).
    #         self.prev_out_index.append(change_endianness(int2bytes(prev_out_index[i], 4)))  # e.g "00000000"
    #
    #     # ScriptSig
    #
    #     # The order in the tx is: scriptSig_len, scriptSig.
    #     # Temporary filled with "0" "0" for standard script transactions (Signature)
    #
    #     for i in range(n_inputs):
    #         if scriptSig is None:
    #             self.scriptSig_len.append("0")  # Input script length (varint, between 1-9 bytes long)
    #             self.scriptSig.append("0")
    #
    #         else:
    #             self.scriptSig_len.append(int2bytes(len(scriptSig[i]) / 2, 1))
    #             self.scriptSig.append(scriptSig[i])
    #
    #         # 4-byte sequence number (default:ffffffff).
    #
    #         self.nSequence.append("ffffffff")
    #
    #     #############
    #     #  OUTPUTS  #
    #     #############
    #
    #     # Number of outputs (varint, between 1-9 bytes long).
    #     n_outputs = len(scriptPubKey)
    #     self.outputs = encode_varint(n_outputs)  # e.g "01"
    #
    #     # 8-byte field (64 bit integer) representing the amount of Satoshis to be spent (little endian).
    #     # 0.00349815 (UTXO value) - 0.00005000 (fee) =  0.00344815 BTC = 344815 (Satoshi) = ef4250 (Little endian)
    #
    #     for i in range(n_outputs):
    #         self.value.append(change_endianness(int2bytes(value[i], 8)))  # e.g "ef42050000000000"
    #
    #         # Output script and its length (varint, between 1-9 bytes long)
    #
    #         self.scriptPubKey_len.append(encode_varint(len(scriptPubKey[i]) / 2))  # e.g "06"
    #         self.scriptPubKey = scriptPubKey  # e.g "010301029488"
    #
    #     # 4-byte lock time field (default: 0)
    #
    #     self.nLockTime = "00000000"
