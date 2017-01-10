from tools import decode_varint, parse_varint, parse_element
from tx import TX

tx = TX()
f = open("data/raw_tx.txt", 'r')
tx.hex = f.read()

tx.version = parse_element(tx, 4)
tx.inputs = parse_varint(tx)

for i in range(decode_varint(tx.inputs)):
    tx.prev_tx_id.append(parse_element(tx, 32))
    tx.prev_out_index.append(parse_element(tx, 4))
    tx.scriptSig_len.append(parse_varint(tx))
    tx.scriptSig.append(parse_element(tx, decode_varint(tx.scriptSig_len[i])))
    tx.nSequence.append(parse_element(tx, 4))

tx.outputs = parse_varint(tx)

for i in range(decode_varint(tx.outputs)):
    tx.value.append(parse_element(tx, 8))
    tx.scriptPubKey_len.append(parse_varint(tx))
    tx.scriptPubKey.append(parse_element(tx, decode_varint(tx.scriptPubKey_len[i])))

tx.nLockTime = parse_element(tx, 4)

assert tx.offset == len(tx.hex)

tx.print_elements()






