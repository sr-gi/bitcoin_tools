##############################
#     Tx building stage      #
##############################

from bitcoin.transaction import sign
from utils.bitcoin.tools import get_priv_key_hex

S_KEY = 'private/paysense.key'


def int2bytes(a, b):
    return ('%0'+str(2*b)+'x') % a


def toLittleEndian(x):
    # If there is a odd number of elements, we make it even by adding a 0
    if (len(x) % 2) == 1:
        x += "0"
    y = x.decode('hex')
    z = y[::-1]
    return z.encode('hex')


def doVerbose(version, inputs, prev_tx_id, prev_out_index, scriptSig_len, scriptSig, nSequence, outputs, value, scriptPubKey_len, scriptPubKey, nLockTime):
    print "version: " + version
    print "number of inputs: " + inputs
    for i in range(len(scriptSig)):
        print "input " + str(i)
        print "\t previous txid (little endian): " + prev_tx_id[i]
        print "\t previous tx output (little endian): " + prev_out_index[i]
        print "\t input script (scriptSig) length: " + scriptSig_len[i]
        print "\t input script (scriptSig): " + scriptSig[i]
    print "nSequence: " + nSequence
    for i in range(len(scriptPubKey)):
        print "output " + str(i)
        print "\t number of outputs: " + outputs[i]
        print "\t Satoshis to be spent (little endian): " + value[i]
        print "\t output script (scriptPubKey) length: " + scriptPubKey_len[i]
        print "\t output script (scriptPubKey): " + scriptPubKey[i]
    print "nLockTime: " + nLockTime


def build_tx(prev_tx_id, prev_out_index, value, scriptPubKey, scriptSig='0', verbose=0):

    # 4-byte version number (default: 01 little endian).
    version = "01000000"

    #############
    #   INPUTS  #
    #############

    # 1-byte number of inputs.
    n_inputs = len(prev_tx_id)
    inputs = int2bytes(n_inputs, 1)     # e.g "01"

    # Reference to the UTXO to redeem.

    # 32-byte hash of the previous transaction (little endian).
    for i in range(n_inputs):
        prev_tx_id[i] = toLittleEndian(prev_tx_id[i])  # e.g "c7495bd4c5102d7e40c231279eaf9877e825364847ddebc34911f5a0f0d79ea5"

        # 4-byte output index (little endian).
        prev_out_index[i] = toLittleEndian(int2bytes(prev_out_index[i], 4))  # e.g "00000000"

    # ScriptSig

    # The order in the tx is: scriptSig_len, scriptSig.
    # Temporary filled with "0" "0" for standard script transactions (Signature)

    scriptSig_len = []

    for i in range(n_inputs):
        if scriptSig[i] is '0':
            scriptSig_len.append("0")
        else:
            scriptSig_len[i] = int2bytes(len(scriptSig[i])/2, 1)

    # 4-byte sequence number (default:ffffffff).

    nSequence = "ffffffff"

    #############
    #  OUTPUTS  #
    #############

    # 1-byte number of outputs.
    n_outputs = len(scriptPubKey)
    outputs = int2bytes(n_outputs, 1)   # e.g "01"

    # 8-byte field (64 bit integer) representing the amount of Satoshis to be spent (little endian).
    # 0.00349815 (UTXO value) - 0.00005000 (fee) =  0.00344815 BTC = 344815 (Satoshi) = ef4250 (Little endian)

    scriptPubKey_len = []

    for i in range(n_outputs):

        value[i] = toLittleEndian(int2bytes(value[i], 8))  # e.g "ef42050000000000"

        # Output script and its length (bytes) (HEX)

        # e.g scriptPubKey = ["010301029488"]

        scriptPubKey_len.append(int2bytes(len(scriptPubKey[i])/2, 1))  # e.g "06"

    # scriptPubKey = "010301029488"

    # 4-byte lock time field (default: 0)

    nLockTime = "00000000"

    if verbose:
        doVerbose(version, inputs, prev_tx_id, prev_out_index, scriptSig_len, scriptSig, nSequence, outputs, value, scriptPubKey_len, scriptPubKey, nLockTime)

    raw_transaction = version + inputs

    for i in range(n_inputs):
        raw_transaction += prev_tx_id[i] + prev_out_index[i] + scriptSig_len[i] + scriptSig[i]

    raw_transaction += nSequence + outputs

    for i in range(n_outputs):
        raw_transaction += value[i] + scriptPubKey_len[i] + scriptPubKey[i]

    raw_transaction += nLockTime

    return raw_transaction

private_key_hex = get_priv_key_hex(S_KEY)

raw_tx = build_tx(['23a489224ff651426b7130176be2e7d50aa451d1ee823bc48a219619973f8bc9'], [1], [20000], ['031616160315151584'], verbose=1)
signed_tx = sign(raw_tx, 0, private_key_hex)

print signed_tx


