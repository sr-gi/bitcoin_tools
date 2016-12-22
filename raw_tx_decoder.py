import struct

offset = 0


def toLittleEndian(x):
    # If there is a odd number of elements, we make it even by adding a 0
    if (len(x) % 2) == 1:
        x += "0"
    y = x.decode('hex')
    z = y[::-1]
    return z.encode('hex')


def decode_varint(data):
    global offset
    assert(len(data) > 0)
    size = int(data[:2], 16)
    assert(size <= 255)

    if size <= 252:
        storage_length = 1
        varint = data[:2]
        decoded_varint = int(varint, 16)
    else:
        if size == 253:  # 0xFD
            storage_length = 3
        elif size == 254:  # 0xFE
            storage_length = 5
        elif size == 255:  # 0xFF
            storage_length = 9

        varint = data[:storage_length*2]
        decoded_varint = int(toLittleEndian(varint[2:]), 16)
        
    offset += storage_length * 2

    return varint, decoded_varint


def int2bytes(a, b):
    return ('%0'+str(2*b)+'x') % a


def extract_element(tx, size):
    global offset
    element = tx[0:size*2]
    offset += size*2
    return element


def doVerbose(version, inputs, inputs_dec, prev_tx_id, prev_out_index, scriptSig_len, scriptSig, nSequence, outputs, outputs_dec, value, scriptPubKey_len, scriptPubKey, nLockTime):
    print "version: " + version
    print "number of inputs: " + inputs + " (" + str(inputs_dec) + ")"
    for i in range(len(scriptSig)):
        print "input " + str(i)
        print "\t previous txid (little endian): " + prev_tx_id[i] + " (" + toLittleEndian(prev_tx_id[i]) + ")"
        print "\t previous tx output (little endian): " + prev_out_index[i] + " (" + str(int(toLittleEndian(prev_out_index[i]), 16)) + ")"
        print "\t input script (scriptSig) length: " + scriptSig_len[i] + " (" + str(int(scriptSig_len[i], 16)) + ")"
        print "\t input script (scriptSig): " + scriptSig[i]
        print "\t nSequence: " + nSequence[i]
    print "number of outputs: " + outputs + " (" + str(outputs_dec) + ")"
    for i in range(len(scriptPubKey)):
        print "output " + str(i)
        print "\t Satoshis to be spent (little endian): " + value[i] + " (" + str(int(toLittleEndian(value[i]), 16)) + ")"
        print "\t output script (scriptPubKey) length: " + scriptPubKey_len[i] + " (" + str(int(toLittleEndian(scriptPubKey_len[i]), 16)) + ")"
        print "\t output script (scriptPubKey): " + scriptPubKey[i]
    print "nLockTime: " + nLockTime

f = open('raw_tx.txt', 'r')
tx = f.read()

prev_tx_id = []
prev_out_index = []
scriptSig_len = []
scriptSig = []
nSequence = []
value = []
scriptPubKey_len = []
scriptPubKey = []


version = extract_element(tx, 4)
inputs, inputs_dec = decode_varint(tx[offset:])

for i in range(inputs_dec):
    prev_tx_id.append(extract_element(tx[offset:], 32))
    prev_out_index.append(extract_element(tx[offset:], 4))
    l, l_dec = decode_varint(tx[offset:])
    scriptSig_len.append(l)
    scriptSig.append(extract_element(tx[offset:], l_dec))
    nSequence.append(extract_element(tx[offset:], 4))

outputs, outputs_dec = decode_varint(tx[offset:])

for i in range(outputs_dec):
    value.append(extract_element(tx[offset:], 8))
    l, l_dec = decode_varint(tx[offset:])
    scriptPubKey_len.append(l)
    scriptPubKey.append(extract_element(tx[offset:], l_dec))

nLockTime = extract_element(tx[offset:], 4)

assert offset == len(tx)

doVerbose(version, inputs, inputs_dec, prev_tx_id, prev_out_index, scriptSig_len, scriptSig, nSequence, outputs, outputs_dec, value, scriptPubKey_len, scriptPubKey, nLockTime)





