from bitcoin_tools import CFG
from bitcoin_tools.utils import change_endianness
from bitcoin_tools.analysis.status import MIN_FEE_PER_BYTE, MAX_FEE_PER_BYTE, FEE_STEP
from bitcoin_tools.analysis.status.utils import check_multisig, get_min_input_size, decode_utxo, roundup_rate, \
    check_multisig_type
import ujson
from collections import OrderedDict
from subprocess import call

from os import remove


def transaction_dump(fin_name, fout_name, version=0.15):
    # ToDo: Profile this function
    # Transaction dump

    if version < 0.15:

        # Input file
        fin = open(CFG.data_path + fin_name, 'r')
        # Output file
        fout = open(CFG.data_path + fout_name, 'w')

        for line in fin:
            data = ujson.loads(line[:-1])

            utxo = decode_utxo(data["value"], None, version)
            imprt = sum([out["amount"] for out in utxo.get("outs")])
            result = {"tx_id": change_endianness(data["key"][2:]),
                      "num_utxos": len(utxo.get("outs")),
                      "total_value": imprt,
                      "total_len": (len(data["key"]) + len(data["value"])) / 2,
                      "height": utxo["height"],
                      "coinbase": utxo["coinbase"],
                      "version": utxo["version"]}

            fout.write(ujson.dumps(result) + '\n')

        fout.close()
        fin.close()

    else:

        # Input file
        fin = open(CFG.data_path + fin_name, 'r')
        # Temp file (unsorted & non-aggregated tx data)
        fout = open(CFG.data_path + "temp.json", 'w')

        # [1] Create temp file
        for line in fin:
            data = ujson.loads(line[:-1])

            utxo = decode_utxo(data["value"], data["key"], version)

            result = OrderedDict([
                ("tx_id", change_endianness(utxo.get('tx_id'))),
                ("num_utxos", 1),
                ("total_value", utxo.get('outs')[0].get('amount')),
                ("total_len", (len(data["key"]) + len(data["value"])) / 2),
                ("height", utxo["height"]),
                ("coinbase", utxo["coinbase"]),
                ("version", None)])

            fout.write(ujson.dumps(result) + '\n')

        fout.close()
        fin.close()

        # [2] Sort file
        call(["sort", CFG.data_path + "temp.json", "-o", CFG.data_path + "temp.json"])

        # [3] Aggregate tx data
        fin = open(CFG.data_path + "temp.json", 'r')
        fout = open(CFG.data_path + fout_name, 'w')

        line_1 = fin.readline()
        line_2 = fin.readline()
        line_1 = ujson.loads(line_1) if line_1 else None
        line_2 = ujson.loads(line_2) if line_2 else None

        while line_1:

            total_len = line_1["total_len"]
            total_value = line_1["total_value"]
            num_utxos = line_1["num_utxos"]
            while line_2 and (line_1["tx_id"] == line_2["tx_id"]):
                total_len += line_2["total_len"]
                total_value += line_2["total_value"]
                num_utxos += line_2["num_utxos"]
                line_2 = fin.readline()
                line_2 = ujson.loads(line_2) if line_2 else None

            result = OrderedDict([
                ("tx_id", line_1["tx_id"]),
                ("num_utxos", num_utxos),
                ("total_value", total_value),
                ("total_len", total_len),
                ("height", line_1["height"]),
                ("coinbase", line_1["coinbase"]),
                ("version", line_1["version"])])
            fout.write(ujson.dumps(result) + '\n')
            line_1 = line_2
            line_2 = fin.readline()
            line_2 = ujson.loads(line_2) if line_2 else None

        fin.close()
        fout.close()

        remove(CFG.data_path + "temp.json")


def utxo_dump(fin_name, fout_name, version=0.15, count_p2sh=False, non_std_only=False):
    # UTXO dump

    # Input file
    fin = open(CFG.data_path + fin_name, 'r')
    # Output file
    fout = open(CFG.data_path + fout_name, 'w')

    # Standard UTXO types
    std_types = [0, 1, 2, 3, 4, 5]

    for line in fin:
        data = ujson.loads(line[:-1])
        if version < 0.15:
            utxo = decode_utxo(data["value"], None, version)
            tx_id = change_endianness(data["key"][2:])
        else:
            utxo = decode_utxo(data["value"], data['key'], version)
            tx_id = change_endianness(utxo.get('tx_id'))
        for out in utxo.get("outs"):
            # Checks whether we are looking for every type of UTXO or just for non-standard ones.
            if not non_std_only or (non_std_only and out["out_type"] not in std_types
                                    and not check_multisig(out['data'])):

                # Calculates the dust threshold for every UTXO value and every fee per byte ratio between min and max.
                min_size = get_min_input_size(out, utxo["height"], count_p2sh)
                dust = 0
                lm = 0

                if min_size > 0:
                    raw_dust = out["amount"] / float(3 * min_size)
                    raw_lm = out["amount"] / float(min_size)

                    dust = roundup_rate(raw_dust, FEE_STEP)
                    lm = roundup_rate(raw_lm, FEE_STEP)

                # Adds multisig type info
                if out["out_type"] in [0, 1, 2, 3, 4, 5]:
                    non_std_type = "std"
                else:
                    non_std_type = check_multisig_type(out["data"])

                # Builds the output dictionary
                result = {"tx_id": tx_id,
                          "tx_height": utxo["height"],
                          "utxo_data_len": len(out["data"]) / 2,
                          "dust": dust,
                          "loss_making": lm,
                          "non_std_type": non_std_type}

                # Index added at the end when updated the result with the out, since the index is not part of the
                # encoded data anymore (coin) but of the entry identifier (outpoint), we add it manually.
                if version >= 0.15:
                    result['index'] = utxo['index']
                    result['register_len'] = len(data["value"]) / 2 + len(data["key"]) / 2

                # Updates the dictionary with the remaining data from out, and stores it in disk.
                result.update(out)
                fout.write(ujson.dumps(result) + '\n')

    fout.close()
