from bitcoin_tools.utils import decode_utxo, change_endianness
from json import loads, dumps

# Input and output files
fin = open('./utxos.txt', 'r')
fout = open('./parsed_txs.txt', 'w')

types = [0, 1, 2, 3, 4, 5]
for line in fin:
    data = loads(line[:-1])
    utxo = decode_utxo(data["value"])

    for out in utxo.get("outs"):
        result = {"tx_id": change_endianness(data["key"][2:])}
        result.update(out)
        fout.write(dumps(result) + '\n')

