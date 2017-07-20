from bitcoin_tools.utils import load_conf_file, decode_utxo, change_endianness
from json import loads, dumps

# Load config file
cfg = load_conf_file()


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


def transaction_dump(fin_name, fout_name):
    # Transaction dump

    # Input file
    fin = open(cfg.data_path + fin_name, 'r')
    # Output file
    fout = open(cfg.data_path + fout_name, 'w')

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

        fout.write(dumps(result) + '\n')

    fout.close()


def utxo_dump(fin_name, fout_name, non_std_only=False):
    # UTXO dump

    # Input file
    fin = open(cfg.data_path + fin_name, 'r')
    # Output file
    fout = open(cfg.data_path + fout_name, 'w')

    std_types = [0, 1, 2, 3, 4, 5]

    for line in fin:
        data = loads(line[:-1])
        utxo = decode_utxo(data["value"])

        for out in utxo.get("outs"):
            if not non_std_only or (non_std_only and out["out_type"] not in std_types):
                result = {"tx_id": change_endianness(data["key"][2:]),
                          "tx_height": utxo["height"],
                          "utxo_data_len": len(out["data"])/2,
                          "min_input_size": get_min_input_size(out["out_type"])}

                result.update(out)
                fout.write(dumps(result) + '\n')

    fout.close()


def dust_calculation(fin_name, fout_name, verbose=False):
    # Dust calculation

    # Input file
    fin = open(cfg.data_path + fin_name, 'r')
    # Output file
    fout = open(cfg.data_path + fout_name, 'w')

    dust = {}
    value = {}
    unknown = 0

    total_utxo = 0
    total_value = 0

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

        total_utxo += 1
        total_value += data["amount"]

    if verbose:
        fout_verbose = open(cfg.data_path + fout_name + '_verbose.txt', 'w')
        fout_verbose.write("total utxos: " + str(total_utxo) + "\n")
        fout_verbose.write("# unknown type: " + str(unknown) + "\n")
        fout_verbose.write("% unknown type: " + str(float(unknown) / total_utxo * 100) + "\n\n")

        for fee_per_byte in range(30, 350, 10):
            fout_verbose.write("fee_per_byte: " + str(fee_per_byte) + "\n")
            fout_verbose.write("# dust: " + str(dust[str(fee_per_byte)]) + "\n")
            fout_verbose.write("% dust: " + str(0) if total_utxo is 0 else str(float(dust[str(fee_per_byte)]) /
                                                                               total_utxo * 100) + "\n")
            fout_verbose.write("total dust value (Satoshis): " + str(value[str(fee_per_byte)]) + "\n")
            fout_verbose.write("% of dust value (Satoshis): " + str(float(value[str(fee_per_byte)]) /
                                                                    total_value * 100) + "\n\n")

        fout_verbose.close()

    fout.write(dumps({"dust": dust, "value": value, "total_utxos": total_utxo, "total_value": total_value}) + '\n')

    fin.close()
    fout.close()


# transaction_dump("utxos.txt", "parsed_txs.txt")
# utxo_dump("utxos.txt", "parsed_utxos.txt")
# dust_calculation("parsed_utxo.txt", "dust.txt")
utxo_dump("utxos.txt", "parsed_non_std_utxos.txt", non_std_only=True)
