from bitcoin_tools import CFG
from bitcoin_tools.utils import change_endianness
from bitcoin_tools.analysis.leveldb import MIN_FEE_PER_BYTE, MAX_FEE_PER_BYTE, FEE_STEP
from bitcoin_tools.analysis.leveldb.utils import check_multisig, get_min_input_size, decode_utxo
from json import loads, dumps
from collections import OrderedDict
from os import remove
from subprocess import call


def transaction_dump(fin_name, fout_name, version=0.15):
    # Transaction dump

    if version < 0.15:

        # Input file
        fin = open(CFG.data_path + fin_name, 'r')
        # Output file
        fout = open(CFG.data_path + fout_name, 'w')

        for line in fin:
            data = loads(line[:-1])

            utxo = decode_utxo(data["value"], None, version)
            imprt = sum([out["amount"] for out in utxo.get("outs")])
            result = {"tx_id": change_endianness(data["key"][2:]),
                      "num_utxos": len(utxo.get("outs")),
                      "total_value": imprt,
                      "total_len": (len(data["key"]) + len(data["value"])) / 2,
                      "height": utxo["height"],
                      "coinbase": utxo["coinbase"],
                      "version": utxo["version"]}

            fout.write(dumps(result) + '\n')

        fout.close()
        fin.close()

    else:

        # Input file
        fin = open(CFG.data_path + fin_name, 'r')
        # Temp file (unsorted & unaggregated tx data)
        fout = open(CFG.data_path + "temp.json", 'w')

        # [1] Create temp file
        for line in fin:
            data = loads(line[:-1])

            utxo = decode_utxo(data["value"], data["key"], version)

            result = OrderedDict([
                ("tx_id", change_endianness(utxo.get('tx_id'))),
                ("num_utxos", 1),
                ("total_value", utxo.get('outs')[0].get('amount')),
                ("total_len", (len(data["key"]) + len(data["value"])) / 2),
                ("height", utxo["height"]),
                ("coinbase", utxo["coinbase"]),
                ("version", None)])

            fout.write(dumps(result) + '\n')

        fout.close()
        fin.close()

        # [2] Sort file
        call(["sort", CFG.data_path + "temp.json", "-o", CFG.data_path + "temp.json"])

        # [3] Aggregate tx data
        fin = open(CFG.data_path + "temp.json", 'r')
        fout = open(CFG.data_path + fout_name, 'w')

        line_1 = fin.readline()
        line_2 = fin.readline()
        line_1 = loads(line_1) if line_1 else None
        line_2 = loads(line_2) if line_2 else None

        while line_1:

            total_len = line_1["total_len"]
            total_value = line_1["total_value"]
            num_utxos = line_1["num_utxos"]
            while line_2 and (line_1["tx_id"] == line_2["tx_id"]):
                total_len += line_2["total_len"]
                total_value += line_2["total_value"]
                num_utxos += line_2["num_utxos"]
                line_2 = fin.readline()
                line_2 = loads(line_2) if line_2 else None

            result = OrderedDict([
                ("tx_id", line_1["tx_id"]),
                ("num_utxos", num_utxos),
                ("total_value", total_value),
                ("total_len", total_len),
                ("height", line_1["height"]),
                ("coinbase", line_1["coinbase"]),
                ("version", line_1["version"])])
            fout.write(dumps(result) + '\n')
            line_1 = line_2
            line_2 = fin.readline()
            line_2 = loads(line_2) if line_2 else None

        fin.close()
        fout.close()

        # remove(CFG.data_path + "temp.json")


def utxo_dump(fin_name, fout_name, version=0.15, count_p2sh=False, non_std_only=False):
    # UTXO dump

    # Input file
    fin = open(CFG.data_path + fin_name, 'r')
    # Output file
    fout = open(CFG.data_path + fout_name, 'w')

    # Standard UTXO types
    std_types = [0, 1, 2, 3, 4, 5]

    for line in fin:
        data = loads(line[:-1])
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
                # Initialize dust, lm and the fee_per_byte ratio.
                dust = 0
                lm = 0
                fee_per_byte = MIN_FEE_PER_BYTE
                # Check whether the utxo is dust/lm for the fee_per_byte range.
                while MAX_FEE_PER_BYTE > fee_per_byte and lm == 0:
                    # Set the dust and loss_making thresholds.
                    if dust is 0 and min_size * fee_per_byte > out["amount"] / 3:
                        dust = fee_per_byte
                    if lm is 0 and out["amount"] < min_size * fee_per_byte:
                        lm = fee_per_byte

                    # Increase the ratio
                    fee_per_byte += FEE_STEP

                # Builds the output dictionary
                result = {"tx_id": tx_id,
                          "tx_height": utxo["height"],
                          "utxo_data_len": len(out["data"]) / 2,
                          "dust": dust,
                          "loss_making": lm}

                # Index added at the end when updated the result with the out, since the index is not part of the
                # encoded data anymore (coin) but of the entry identifier (outpoint), we add it manually.
                if version >= 0.15:
                    result['index'] = utxo['index']

                # Updates the dictionary with the remaining data from out, and stores it in disk.
                result.update(out)
                fout.write(dumps(result) + '\n')

    fout.close()
