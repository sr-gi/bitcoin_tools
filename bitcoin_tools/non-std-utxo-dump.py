from bitcoin_tools.utils import decode_utxo, change_endianness
from json import loads, dumps

# Input and output files
fin = open('./utxos.txt', 'r')
fout = open('./non-std.txt', 'w+')

types = [0, 1, 2, 3, 4, 5]
for line in fin:
    data = loads(line[:-1])
    utxo = decode_utxo(data["value"])

    for out in utxo.get("outs"):
        if out.get("out_type") in types:
            s = out.get("data")[:4]
            result = {"tx_id": change_endianness(data["key"][2:])}
            result.update(out)
            fout.write(dumps(result) + '\n')

