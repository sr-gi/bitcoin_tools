from tools import change_endianness, decode_varint, encode_varint, int2bytes


class TX:

    def __init__(self, version=None, inputs=None, prev_tx_id=None, prev_out_index=None, scriptSig_len=None, scriptSig=None,
                 nSequence=None, outputs=None, value=None, scriptPubKey_len=None, scriptPubKey=None, nLockTime=None):
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
        if self.hex is None:
            self.hex = self.version + self.inputs

            for i in range(len(self.prev_tx_id)):
                self.hex += self.prev_tx_id[i] + self.prev_out_index[i] + self.scriptSig_len[i] \
                            + self.scriptSig[i] + self.nSequence[i]

            self.hex += self.outputs

            for i in range(len(self.scriptPubKey)):
                self.hex += self.value[i] + self.scriptPubKey_len[i] + self.scriptPubKey[i]

            self.hex += self.nLockTime

        return self.hex

    def build_default_tx(self, prev_tx_id, prev_out_index, value, scriptPubKey, scriptSig=None):

        # 4-byte version number (default: 01 little endian).
        self.version = "01000000"

        #############
        #   INPUTS  #
        #############

        # 1-byte number of inputs.
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
                self.scriptSig.append("0")
                self.scriptSig_len.append("0")

            else:
                self.scriptSig_len.append(int2bytes(len(scriptSig[i]) / 2, 1))

            # 4-byte sequence number (default:ffffffff).

            self.nSequence.append("ffffffff")

        #############
        #  OUTPUTS  #
        #############

        # 1-byte number of outputs.
        n_outputs = len(scriptPubKey)
        self.outputs = encode_varint(n_outputs)  # e.g "01"

        # 8-byte field (64 bit integer) representing the amount of Satoshis to be spent (little endian).
        # 0.00349815 (UTXO value) - 0.00005000 (fee) =  0.00344815 BTC = 344815 (Satoshi) = ef4250 (Little endian)

        for i in range(n_outputs):
            self.value.append(change_endianness(int2bytes(value[i], 8)))  # e.g "ef42050000000000"

            # Output script and its length (bytes) (HEX)

            # e.g scriptPubKey = ["010301029488"]

            self.scriptPubKey_len.append(encode_varint(len(scriptPubKey[i]) / 2))  # e.g "06"
            self.scriptPubKey = scriptPubKey  # e.g scriptPubKey = "010301029488"

        # 4-byte lock time field (default: 0)

        self.nLockTime = "00000000"

        self.to_hex()








