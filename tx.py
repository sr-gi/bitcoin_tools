from tools import change_endianness, decode_varint


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
            self.hex += self.version + self.inputs

            for i in range(len(self.prev_tx_id)):
                self.hex += self.prev_tx_id[i] + self.prev_out_index[i] + self.scriptSig_len[i] \
                            + self.scriptSig[i] + self.nSequence[i]

            self.hex += self.outputs

            for i in range(len(self.scriptPubKey)):
                self.hex += self.value[i] + self.scriptPubKey_len[i] + self.scriptPubKey[i]

            self.hex += self.nLockTime

        return self.hex








