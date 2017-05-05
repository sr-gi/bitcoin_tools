from tx import TX
from utils.utils import decode_varint, parse_varint, parse_element
from script.script import InputScript, OutputScript


def decode_raw_tx(tx_hex):
    tx = TX()
    tx.hex = tx_hex

    scriptSig = InputScript()
    scriptPubKey = OutputScript()

    tx.version = parse_element(tx, 4)
    tx.inputs = parse_varint(tx)

    for i in range(decode_varint(tx.inputs)):
        tx.prev_tx_id.append(parse_element(tx, 32))
        tx.prev_out_index.append(parse_element(tx, 4))
        tx.scriptSig_len.append(parse_varint(tx))
        scriptSig.from_hex(parse_element(tx, decode_varint(tx.scriptSig_len[i])))
        tx.scriptSig.append(scriptSig)
        tx.nSequence.append(parse_element(tx, 4))

    tx.outputs = parse_varint(tx)

    for i in range(decode_varint(tx.outputs)):
        tx.value.append(parse_element(tx, 8))
        tx.scriptPubKey_len.append(parse_varint(tx))
        scriptPubKey.from_hex(parse_element(tx, decode_varint(tx.scriptPubKey_len[i])))
        tx.scriptPubKey.append(scriptPubKey)

    tx.nLockTime = parse_element(tx, 4)

#    assert tx.offset == len(tx.hex)

    tx.deserialize()






