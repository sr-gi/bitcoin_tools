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
        scriptSig_len = 0
    elif type in [2, 3, 4, 5]:
        # P2PK
        scriptSig = 73
    else:
        # All other types (including P2MS, OP_Return and non-standard outs)
        scriptSig = -fixed_size  # idem
        scriptSig_len = 0

    var_size = scriptSig_len + scriptSig

    return fixed_size + var_size

# Load config file
cfg = load_conf_file()

# Input file
fin = open(cfg.data_path + 'utxos.txt', 'r')

# # Transaction dump
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
                  "utxo_data_len": len(out["data"])/2,
                  "min_input_size": get_min_input_size(out["out_type"])}

        result.update(out)

        fout_utxo.write(dumps(result) + '\n')

fout_utxo.close()

# Dust calculation

fout_dust = open(cfg.data_path + 'dust.txt', 'w')
fout_dust_verbose = open(cfg.data_path + 'dust_verbose.txt', 'w')
fin = open(cfg.data_path + 'parsed_utxo.txt', 'r')

dust = {}
value = {}
unknown = 0
total = 0

for fee_per_byte in range(30, 350, 10):
    dust.update({str(fee_per_byte): 0})
    value.update({str(fee_per_byte): 0})

for line in fin:
    data = loads(line[:-1])
    if data["min_input_size"] is 0:
        unknown += 1
    else:
        for fee_per_byte in range(30, 350, 10):
            if data["amount"] < data["min_input_size"] * fee_per_byte:
                dust[str(fee_per_byte)] += 1
                value[str(fee_per_byte)] += data["amount"]

    total += 1

fout_dust_verbose.write("total utxos: " + str(total) + "\n")
fout_dust_verbose.write("# unknown type: " + str(unknown) + "\n")
fout_dust_verbose.write("% unknown type: " + str(float(unknown) / total * 100) + "\n\n")

for fee_per_byte in range(30, 350, 10):
    fout_dust_verbose.write("fee_per_byte: " + str(fee_per_byte) + "\n")
    fout_dust_verbose.write("# dust: " + str(dust[str(fee_per_byte)]) + "\n")
    fout_dust_verbose.write("% dust: " + str(0) if dust is 0 else str(float(dust[str(fee_per_byte)]) / total * 100) + "\n")
    fout_dust_verbose.write("total dust value (Satoshis): " + str(value[str(fee_per_byte)]) + "\n\n")

fout_dust.write(dumps({"dust": dust, "value": value}) + '\n')

fin.close()
fout_dust.close()
