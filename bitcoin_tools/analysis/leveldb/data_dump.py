from bitcoin_tools import CFG
from bitcoin_tools.utils import change_endianness
from json import loads, dumps
from bitcoin_tools.analysis.leveldb import MIN_FEE_PER_BYTE, MAX_FEE_PER_BYTE, FEE_STEP
from bitcoin_tools.analysis.leveldb.utils import check_multisig, get_min_input_size, decode_utxo


def transaction_dump(fin_name, fout_name):
    # Transaction dump

    # Input file
    fin = open(CFG.data_path + fin_name, 'r')
    # Output file
    fout = open(CFG.data_path + fout_name, 'w')

    for line in fin:
        data = loads(line[:-1])
        utxo = decode_utxo(data["value"])

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


def utxo_dump(fin_name, fout_name, count_p2sh=False, non_std_only=False):
    # UTXO dump

    # Input file
    fin = open(CFG.data_path + fin_name, 'r')
    # Output file
    fout = open(CFG.data_path + fout_name, 'w')

    # Standard UTXO types
    std_types = [0, 1, 2, 3, 4, 5]

    for line in fin:
        data = loads(line[:-1])
        utxo = decode_utxo(data["value"])

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
                result = {"tx_id": change_endianness(data["key"][2:]),
                          "tx_height": utxo["height"],
                          "utxo_data_len": len(out["data"]) / 2,
                          "dust": dust,
                          "loss_making": lm}

                # Updates the dictionary with the remaining data from out, and stores it in disk.
                result.update(out)
                fout.write(dumps(result) + '\n')

    fout.close()
