from tools import decode_varint, parse_varint, parse_element
from tx import TX

tx = TX()
# tx.hex = "0100000001f4843b3c6b9f243075ff25a8dfba528315ccef25b27302a68cec2653d43b1564000000008b483045022100f4f442faba1c1acc7e21bc9cfd667915220174c1d411f0cc3594d0b09c477f2b0220365fa8c60dce4cdae969544c3e53e03e7b692fae1d2f13775073a7f1c1668824014104c87acf509bb7957ca833445e63bfa821422cae0266eb83064c226d7bfb75dcdc4340c1396bb2c177565c201bf83876969f0b9ebc9d382f8f5b7d3e7d27d4f889ffffffff01d007000000000000cc63761453def8f9491c649da664302bbaa7ba0a4277f07ead820147884700000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000000844700000022014baeee14bd64bd64e0c0c765c9acf89f2db1c5477f53dd2240f2a16dd7012b5020000000000000000000000000000000000000000000000000000000000000000000876703bc2e10b17514b34bbaac4e9606c9a8a6a720acaf3018c9bc77c9ac6800000000"
f = open("raw_tx.txt", 'r')
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






