from bitcoin_tools.utils import load_conf_file, decode_utxo, change_endianness
from json import loads, dumps
from math import ceil

# Load config file
cfg = load_conf_file()


def check_multisig(script):
    if int(script[:2], 16) in range(81, 96) and script[2:4] in ["21", "41"] and script[-2:] == "ae":
        return True
    else:
        return False


def get_min_input_size(out_type, script):
    # fixed size
    prev_tx_id = 32
    prev_out_index = 4
    nSequence = 4

    fixed_size = prev_tx_id + prev_out_index + nSequence

    # variable size (depending on scripSig)

    # Bitcoin core starts using compressed pk in version (0.6.0, 30/03/12, around block height 173480)

    if out_type is 0:
        # P2PKH
        scriptSig = 106  # PUSH sig (1 byte) + sig (71 bytes) + PUSH pk (1 byte) + compressed pk (33 bytes)
        scriptSig_len = 1
    elif out_type is 1:
        # P2SH
        scriptSig = -fixed_size  # How can we define the min size? (temporarily set total size to 0)
        scriptSig_len = 0
    elif out_type in [2, 3, 4, 5]:
        # P2PK
        scriptSig = 72  # PUSH sig (1 byte) + sig (71 bytes)
        scriptSig_len = 1
    else:
        # P2MS
        if check_multisig(script):
            req_sigs = int(script[:2], 16) - 80  # OP_1 is hex 81
            scriptSig = 1 + (req_sigs * 72)  # OP_0 (1 byte) + 72 bytes per sig (PUSH sig (1 byte) + sig (71 bytes))
            scriptSig_len = int(ceil(scriptSig / float(256)))
        else:
            # All other types (including non standard P2MS, OP_Return and non-standard outs)
            scriptSig = -fixed_size - 1  # idem but with -1
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
                          "min_input_size": get_min_input_size(out["out_type"], out["data"])}

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
    p2sh = 0
    unknown = 0

    unknown_value = 0
    p2sh_value = 0

    total_utxo = 0
    total_value = 0

    for fee_per_byte in range(30, 350, 10):
        dust.update({str(fee_per_byte): 0})
        value.update({str(fee_per_byte): 0})

    for line in fin:
        data = loads(line[:-1])
        if data["min_input_size"] is 0:
            p2sh += 1
            p2sh_value += data["amount"]
        elif data["min_input_size"] is -1:
            unknown += 1
            unknown_value += data["amount"]
        else:
            for fee_per_byte in range(30, 350, 10):
                if data["amount"] < data["min_input_size"] * fee_per_byte:
                    dust[str(fee_per_byte)] += 1
                    value[str(fee_per_byte)] += data["amount"]

        total_utxo += 1
        total_value += data["amount"]

    if verbose:
        fout_verbose = open(cfg.data_path + 'verbose_' + fout_name, 'w')
        fout_verbose.write("total utxos: " + str(total_utxo) + "\n")
        fout_verbose.write("total value: " + str(total_value) + "\n\n")

        fout_verbose.write("# P2SH: " + str(p2sh) + "\n")
        fout_verbose.write("% P2SH: " + str(float(p2sh) / total_utxo * 100) + "\n")
        fout_verbose.write("total value in P2SH: " + str(p2sh_value) + "\n")
        fout_verbose.write("% of P2SH value: " + str(float(p2sh_value) /
                                                     total_value * 100) + "\n\n")

        fout_verbose.write("# unknown type: " + str(unknown) + "\n")
        fout_verbose.write("% unknown type: " + str(float(unknown) / total_utxo * 100) + "\n")
        fout_verbose.write("total value in unknown type: " + str(unknown_value) + "\n")
        fout_verbose.write("% of unknown type value: " + str(float(unknown_value) /
                                                             total_value * 100) + "\n\n")

        for fee_per_byte in range(30, 350, 10):
            fout_verbose.write("fee_per_byte: " + str(fee_per_byte) + "\n")
            fout_verbose.write("# of dust: " + str(dust[str(fee_per_byte)]) + "\n")
            fout_verbose.write("% of dust" + str(0) if total_utxo is 0 else str(float(dust[str(fee_per_byte)]) /
                                                                             total_utxo * 100) + "\n")
            fout_verbose.write("total dust value (Satoshis): " + str(value[str(fee_per_byte)]) + "\n")
            fout_verbose.write("% of dust value: " + str(float(value[str(fee_per_byte)]) /
                                                         total_value * 100) + "\n\n")

        fout_verbose.close()

    fout.write(dumps({"dust": dust, "value": value, "total_utxos": total_utxo, "total_value": total_value}) + '\n')

    fin.close()
    fout.close()


def pick_multisig(fin_name, fout_name):
    # Input file
    fin = open(cfg.data_path + fin_name, 'r')
    # Output file

    fout_std = open(cfg.data_path + "std_" + fout_name, 'w')
    fout_non_std = open(cfg.data_path + "non_std_" + fout_name, 'w')

    for line in fin:
        data = loads(line[:-1])

        if check_multisig(data["data"]):
            fout_std.write(dumps(data) + "\n")
        elif data["data"][-2:] == "ae":
            fout_non_std.write(dumps(data) + "\n")

    fin.close()
    fout_std.close()
    fout_non_std.close()



# transaction_dump("utxos.txt", "parsed_txs.txt")
# utxo_dump("utxos.txt", "parsed_utxos.txt")
# dust_calculation("parsed_utxos.txt", "dust.txt", verbose=True)
# utxo_dump("utxos.txt", "parsed_non_std_utxos.txt", non_std_only=True)
pick_multisig("parsed_non_std_utxos.txt", "multisig_utxos.txt")
