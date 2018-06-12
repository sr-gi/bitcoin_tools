from bitcoin_tools import CFG
from bitcoin_tools.analysis.status import FEE_STEP
from bitcoin_tools.analysis.status.utils import check_multisig, get_min_input_size, roundup_rate, check_multisig_type, \
    get_est_input_size, load_estimation_data, check_native_segwit
import ujson
from collections import OrderedDict


def transaction_dump(fin_name, fout_name):
    # Transaction dump

    # Input file
    fin = open(CFG.data_path + fin_name, 'r')
    # Output file
    fout = open(CFG.data_path + fout_name, 'w')

    for line in fin:
        data = ujson.loads(line[:-1])

        utxo = data['value']
        total_value = sum([out["amount"] for out in utxo.get("outs")])
        result = {"tx_id": data["key"],
                  "num_utxos": len(utxo.get("outs")),
                  "total_value": total_value,
                  "total_len": data["len"],
                  "height": utxo["height"],
                  "coinbase": utxo["coinbase"],
                  "version": utxo["version"]}

        fout.write(ujson.dumps(result) + '\n')

    fout.close()
    fin.close()


def utxo_dump(fin_name, fout_name, coin, count_p2sh=False, non_std_only=False, ordered_dict=False):
    # UTXO dump

    # Input file
    fin = open(CFG.data_path + fin_name, 'r')
    # Output file
    fout = open(CFG.data_path + fout_name, 'w')

    # Standard UTXO types
    std_types = [0, 1, 2, 3, 4, 5]

    p2pkh_pksize, p2sh_scriptsize, nonstd_scriptsize, p2wsh_scriptsize = load_estimation_data(coin)

    for line in fin:
        data = ujson.loads(line[:-1])
        utxo = data['value']
        tx_id = data["key"]

        for out in utxo.get("outs"):
            # Checks whether we are looking for every type of UTXO or just for non-standard ones.
            if not non_std_only or (non_std_only and out["out_type"] not in std_types
                                    and not check_multisig(out['data'])):

                # Calculates the dust threshold for every UTXO value and every fee per byte ratio between min and max.
                min_size = get_min_input_size(out, utxo["height"], count_p2sh, coin)

                # https://github.com/bitcoin/bitcoin/blob/5961b23898ee7c0af2626c46d5d70e80136578d3/src/policy/policy.cpp#L20-L33
                # A UTXO is considered dust if the fees that should be payed to spend it are greater or equal to
                # 1/3 of its value for Bitcoin Core up to version 0.14.
                raw_dust = out["amount"] / float(3 * min_size)

                raw_np = out["amount"] / float(min_size)
                raw_np_est = out["amount"] / float(get_est_input_size(out, utxo["height"], p2pkh_pksize,
                                                                      p2sh_scriptsize, nonstd_scriptsize,
                                                                      p2wsh_scriptsize))

                if out["amount"] != 0 and raw_dust == 0:
                    print 'dust', out["amount"], raw_dust

                dust = roundup_rate(raw_dust, FEE_STEP)
                np = roundup_rate(raw_np, FEE_STEP)
                np_est = roundup_rate(raw_np_est, FEE_STEP)

                # Adds multisig type info
                if out["out_type"] in [0, 1, 2, 3, 4, 5]:
                    non_std_type = "std"
                else:
                    multisig = check_multisig_type(out["data"])
                    segwit = check_native_segwit(out["data"])
                    if multisig:
                        non_std_type = multisig
                    elif segwit[0]:
                        non_std_type = segwit[1]
                    else:
                        non_std_type = False

                # Builds the output dictionary
                if ordered_dict:
                    # Slower, but ensures that the order of keys is preserved (useful for ordering purposes)
                    result = OrderedDict()
                    result["key"] = data["key"]
                    result["tx_id"] = tx_id
                    result["tx_height"] = utxo["height"]
                    result["utxo_data_len"] = len(out["data"]) / 2
                    result["dust"] = dust
                    result["non_profitable"] = np
                    result["non_profitable_est"] = np_est
                    result["non_std_type"] = non_std_type

                else:
                    result = {"tx_id": tx_id,
                              "tx_height": utxo["height"],
                              "utxo_data_len": len(out["data"]) / 2,
                              "dust": dust,
                              "non_profitable": np,
                              "non_profitable_est": np_est,
                              "non_std_type": non_std_type}

                    # Additional data used to explain dust figures (describes the size taken into account by each metric
                    # when computing dust/unprofitability). It is not used in most of the cases, and generates overhead
                    # in both size and time of execution, so ity is not added by default. Uncomment if necessary.

                    # result["dust_size"] = out_size + in_size
                    # result["min_size"] = min_size
                    # result["est_size"] = get_est_input_size(out, utxo["height"], p2pkh_pksize, p2sh_scriptsize,
                    #                                         nonstd_scriptsize, p2wsh_scriptsize)}

                # Updates the dictionary with the remaining data from out, and stores it in disk.
                result.update(out)
                fout.write(ujson.dumps(result) + '\n')

    fin.close()
    fout.close()
