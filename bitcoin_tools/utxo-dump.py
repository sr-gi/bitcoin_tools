from bitcoin_tools.utils import decode_utxo, change_endianness
from json import loads, dumps
try:
    import bitcoin_tools.conf as cfg
except ImportError:
    raise Exception("You don't have a configuration file. Make a copy of sample_conf.py")

if cfg.btc_core_path is None or cfg.data_path is None:
    raise Exception("Your configuration file is not properly configured.")

# Input and output files
fin = open(cfg.data_path + 'utxos.txt', 'r')
fout = open(cfg.data_path + 'parsed_txs.txt', 'w')

types = [0, 1, 2, 3, 4, 5]
for line in fin:
    data = loads(line[:-1])
    utxo = decode_utxo(data["value"])

    for out in utxo.get("outs"):
        result = {"tx_id": change_endianness(data["key"][2:])}
        result.update(out)
        fout.write(dumps(result) + '\n')

