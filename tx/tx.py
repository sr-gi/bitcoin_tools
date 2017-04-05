from constants import MAX_SIG_LEN, PK_LEN, OP_PUSH_LEN, RECOMMENDED_MIN_TX_FEE
from utils.utils import change_endianness, decode_varint, encode_varint, int2bytes


class TX:
    """ Defines a class TX (transaction) that holds all the modifiable fields of a Bitcoin transaction, such as
    version, number of inputs, reference to previous transactions, input and output scripts, value, etc.
    """

    def __init__(self, version=None, inputs=None, prev_tx_id=None, prev_out_index=None, scriptSig_len=None,
                 scriptSig=None, nSequence=None, outputs=None, value=None, scriptPubKey_len=None,
                 scriptPubKey=None, nLockTime=None):
        if prev_tx_id is None:
            prev_tx_id = []
        self.version = version
        self.inputs = inputs
        self.outputs = outputs
        self.nLockTime = nLockTime

        if prev_tx_id is None:
            self.prev_tx_id = []
        else:
            self.prev_tx_id = prev_tx_id

        if prev_out_index is None:
            self.prev_out_index = []
        else:
            self.prev_out_index = prev_out_index

        if scriptSig is None:
            self.scriptSig = []
        else:
            self.scriptSig = scriptSig

        if scriptSig_len is None:
            self.scriptSig_len = []
        else:
            self.scriptSig_len = scriptSig_len

        if nSequence is None:
            self.nSequence = []
        else:
            self.nSequence = nSequence

        if value is None:
            self.value = []
        else:
            self.value = value

        if scriptPubKey is None:
            self.scriptPubKey = []
        else:
            self.scriptPubKey = scriptPubKey

        if scriptPubKey_len is None:
            self.scriptPubKey_len = []
        else:
            self.scriptPubKey_len = scriptPubKey_len

        self.hex = None
        self.offset = 0

    def print_elements(self):
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
            print "\t previous txid (little endian): " + self.prev_tx_id[i] + " (" + change_endianness(self.prev_tx_id[i]) + ")"
            print "\t previous tx output (little endian): " + self.prev_out_index[i] + " (" + str(
                int(change_endianness(self.prev_out_index[i]), 16)) + ")"
            print "\t input script (scriptSig) length: " + self.scriptSig_len[i] + " (" + str(
                int(self.scriptSig_len[i], 16)) + ")"
            print "\t input script (scriptSig): " + self.scriptSig[i]
            print "\t nSequence: " + self.nSequence[i]
        print "number of outputs: " + self.outputs + " (" + str(decode_varint(self.outputs)) + ")"
        for i in range(len(self.scriptPubKey)):
            print "output " + str(i)
            print "\t Satoshis to be spent (little endian): " + self.value[i] + " (" + str(
                int(change_endianness(self.value[i]), 16)) + ")"
            print "\t output script (scriptPubKey) length: " + self.scriptPubKey_len[i] + " (" + str(
                int(change_endianness(self.scriptPubKey_len[i]), 16)) + ")"
            print "\t output script (scriptPubKey): " + self.scriptPubKey[i]
        print "nLockTime: " + self.nLockTime

    def to_hex(self):
        """ Serialize all the transaction fields arranged in the proper order, resulting in a hexadecimal string
        ready to be broadcast to the network.

        :param self: self
        :type self: TX
        :return: Hexadecimal transaction representation.
        :rtype: hex str
        """

        self.hex = self.version + self.inputs

        for i in range(len(self.prev_tx_id)):
            self.hex += self.prev_tx_id[i] + self.prev_out_index[i] + self.scriptSig_len[i] \
                        + self.scriptSig[i] + self.nSequence[i]

        self.hex += self.outputs

        for i in range(len(self.scriptPubKey)):
            self.hex += self.value[i] + self.scriptPubKey_len[i] + self.scriptPubKey[i]

        self.hex += self.nLockTime

        return self.hex

    def add_fees(self, output=0, amount=None):
        """ Adds the chosen fees to the chosen output of the transaction.
       :param self: self
       :type self: TX
       :param output: The output where the fees will be charged. The first input will be chosen by default (output=0).
       :type output: int
       :param amount: The amount of fees to be charged. The minimum fees wil be charged by default (amount=None).
       :type amount: int.
       :return: The maximum size of the transaction.
       :rtype: int
       """

        # Minimum fees will be applied
        if amount is None:
            fees = self.get_p2pkh_tx_max_len() * RECOMMENDED_MIN_TX_FEE

        else:
            fees = amount

        # Get the bitcoin amount from the chosen output, cast it into integer and subtract the fees.
        amount = int(change_endianness(self.value[output]), 16) - fees
        # Fill all the missing bytes up to the value length(8 bytes) and get the value back to its LE representation.
        self.value[output] = change_endianness(int2bytes(amount, 8))
        # Update the hex representation of the transaction
        self.to_hex()

    def get_p2pkh_tx_max_len(self):
        """ Computes the maximum transaction length for a default Bitcoin transactions, that is, all the scriptSig
        values are P2PKH scripts. The method can be used approximate the final transaction length and in that way
        calculate the minimum transactions fees than can be applied to the transaction.
       :param self: self
       :type self: TX
       :return: The maximum size of the transaction.
       :rtype: int
       """

        # Max length is approximated by calculating the length of the non-signed transaction, and adding the maximum
        # length of a standard P2PKH sigScript, which corresponds to the length of two data pushes (2 * OP_PUSH_LEN)
        # plus the size of the signature (at most MAX_SIG_LEN) plus the length of a Bitcoin public key (PK_LEN).
        max_len = len(self.hex) / 2 + ((2 * OP_PUSH_LEN + MAX_SIG_LEN + PK_LEN) * int(self.inputs))
        # An additional byte for each input should be added to the max length representing the sigScript length
        # of each input. However, since we had previously added a byte to temporary fill both sigScript and
        # sigScript_len field (00) for each input, it will not be necessary.

        return max_len

    def build_p2pkh_std_tx(self, prev_tx_id, prev_out_index, value, scriptPubKey, scriptSig=None, fees=None):
        """ Builds a standard P2PKH transaction using default parameters such as version = 01000000 or
        nSequence = FFFFFFFF.

        :param self: self
        :type self: TX
        :param prev_tx_id: List of references to the previous transactions from where the current transaction will
        redeem some bitcoins.
        :type prev_tx_id: str list
        :param prev_out_index: List of references transaction output from where the funds will be redeemed.
        :type prev_out_index: int list
        :param value: List of value to be transferred to the desired destinations, in Satoshis (The difference between
        the total input value and the total output value will be charged as fee).
        :type value: int list
        :param scriptPubKey: List of scripts that will lock the outputs of the current transaction.
        :type scriptPubKey: hex str list
        :param scriptSig: List of scripts that will provide proof of fulfillment of the redeem conditions from the
        previous transactions (referenced by the prev_tx_id and prev_out_index).
        :type scriptSig: hex str list
        :return: None.
        :rtype: None
        """

        # 4-byte version number (default: 01 little endian).
        self.version = "01000000"

        #############
        #   INPUTS  #
        #############

        # Number of inputs (varint, between 1-9 bytes long).
        n_inputs = len(prev_tx_id)
        self.inputs = encode_varint(n_inputs)  # e.g "01"

        # Reference to the UTXO to redeem.

        # 32-byte hash of the previous transaction (little endian).
        for i in range(n_inputs):
            self.prev_tx_id.append(change_endianness(prev_tx_id[i]))
            # e.g "c7495bd4c5102d7e40c231279eaf9877e825364847ddebc34911f5a0f0d79ea5"

            # 4-byte output index (little endian).
            self.prev_out_index.append(change_endianness(int2bytes(prev_out_index[i], 4)))  # e.g "00000000"

        # ScriptSig

        # The order in the tx is: scriptSig_len, scriptSig.
        # Temporary filled with "0" "0" for standard script transactions (Signature)

        for i in range(n_inputs):
            if scriptSig is None:
                self.scriptSig_len.append("0")  # Input script length (varint, between 1-9 bytes long)
                self.scriptSig.append("0")

            else:
                self.scriptSig_len.append(int2bytes(len(scriptSig[i]) / 2, 1))

            # 4-byte sequence number (default:ffffffff).

            self.nSequence.append("ffffffff")

        #############
        #  OUTPUTS  #
        #############

        # Number of outputs (varint, between 1-9 bytes long).
        n_outputs = len(scriptPubKey)
        self.outputs = encode_varint(n_outputs)  # e.g "01"

        # 8-byte field (64 bit integer) representing the amount of Satoshis to be spent (little endian).
        # 0.00349815 (UTXO value) - 0.00005000 (fee) =  0.00344815 BTC = 344815 (Satoshi) = ef4250 (Little endian)

        for i in range(n_outputs):
            self.value.append(change_endianness(int2bytes(value[i], 8)))  # e.g "ef42050000000000"

            # Output script and its length (varint, between 1-9 bytes long)

            self.scriptPubKey_len.append(encode_varint(len(scriptPubKey[i]) / 2))  # e.g "06"
            self.scriptPubKey = scriptPubKey  # e.g "010301029488"

        # 4-byte lock time field (default: 0)

        self.nLockTime = "00000000"

        self.to_hex()

        # ToDO: Define a proper way of selecting the fees

        self.add_fees()








