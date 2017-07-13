from bitcoin_tools.utils import load_conf_file, decode_utxo, change_endianness
from json import loads, dumps

# Load config file
cfg = load_conf_file()

# Input file
fin = open(cfg.data_path + 'utxos.txt', 'r')

# Transaction dump
fout_tx = open(cfg.data_path + 'parsed_txs.txt', 'w')
for line in fin:
    data = loads(line[:-1])
    utxo = decode_utxo(data["value"])

    imprt = sum([out["amount"] for out in utxo.get("outs")])

    result = {"tx_id": change_endianness(data["key"][2:]),
              "num_utxos": len(utxo.get("outs")),
              "total_value": imprt,
              "total_len": (len(data["key"]) + len(data["value"]))/2,
              "height": utxo["height"],
              "coinbase": utxo["coinbase"],
              "version": utxo["version"]}

    fout_tx.write(dumps(result) + '\n')

fout_tx.close()

# UTXO dump
fout_utxo = open(cfg.data_path + 'parsed_utxo.txt', 'w')
for line in fin:
    data = loads(line[:-1])
    utxo = decode_utxo(data["value"])

    for out in utxo.get("outs"):

        result = {"tx_id": change_endianness(data["key"][2:]),
                  "tx_height": utxo["height"],
                  "utxo_data_len": len(out["data"])/2}

        result.update(out)

        fout_utxo.write(dumps(result) + '\n')

fout_utxo.close()
