from bitcoin_tools.utils import load_conf_file, decode_utxo, change_endianness
from json import loads, dumps


def get_min_input_size(type):
    # fixed size
    prev_tx_id = 32
    prev_out_index = 4
    nSequence = 4

    fixed_size = prev_tx_id + prev_out_index + nSequence

    # variable size (depending on scripSig)
    scriptSig_len = 1

    if type is 0:
        # P2PKH
        scriptSig = 71 + 33  # size of signature + public key (non-compressed)
    elif type is 1:
        #P2SH
        scriptSig = -fixed_size  # How can we define the min size? (temporarily set total size to 0)
    elif type in [2, 3, 4, 5]:
        # P2PK
        scriptSig = 73
    else:
        # All other types (including P2MS, OP_Return and non-standard outs)
        scriptSig = -fixed_size  # idem

    var_size = scriptSig_len + scriptSig

    return fixed_size + var_size

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

        min_size = get_min_input_size(out["out_type"])

        if min_size is 0:
            dust = "?"
        elif out["amount"] < min_size:
            dust = 1
        else:
            dust = 0

        result = {"tx_id": change_endianness(data["key"][2:]),
                  "tx_height": utxo["height"],
                  "utxo_data_len": len(out["data"])/2,
                  "dust": dust}

        result.update(out)

        fout_utxo.write(dumps(result) + '\n')

fout_utxo.close()
