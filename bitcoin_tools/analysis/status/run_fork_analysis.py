from bitcoin_tools import CFG

import ujson
import pickle


def load_data(fin_name):
    """
    Returns a set of keys in a given UTXO set (specified by its decoded_utxos.json file)

    :param fin_name: path of the decoded_utxos.json file
    :return: a set with keys
    """
    keys = set()
    fin = open(CFG.data_path + fin_name, 'r')
    for line in fin:
        data = ujson.loads(line[:-1])
        keys.add(data["key"])
    fin.close()
    return keys


def count_before_fork(fin_name, fork_height=478558):
    """
    Counts how many UTXOs are there before and after a given height (in an UTXO set specified by its
    decoded_utxos.json file)

    :param fin_name: path of the decoded_utxos.json file
    :param fork_height: int, last block in common
    :return: tuple, count of outputs before and after the height
    """

    before, after = 0, 0
    fin = open(CFG.data_path + fin_name, 'r')
    for line in fin:
        data = ujson.loads(line[:-1])
        if data["value"]["height"] <= fork_height:
            before += 1
        else:
            after += 1
    fin.close()
    return before, after


if __name__ == '__main__':

    """
    Analyses two chainstates, belonging to a fork of the same coin:
    * Counts how many UTXOs they have in common
    * Counts how many UTXOs with height < fork_height exist in each set
    """

    decoded_utxo_files = ["0.15-20180206/decoded_utxos.json", "bu-0.15-20180206/decoded_utxos.json"]

    # Intersection
    keys_btc = load_data(decoded_utxo_files[0])
    keys_bu = load_data(decoded_utxo_files[1])
    # For btc vs bu on 2018-02-06: 41 GB mem
    set_int = keys_bu.intersection(keys_btc)
    # For btc vs bu on 2018-02-06: 42.6 GB
    print("There are {} UTXOs in common".format(len(set_int)))
    pickle.dump(set_int, open("bu_btc_keys_intersect.pickle", "wb"))

    # After/before fork
    before_btc, after_btc = count_before_fork(decoded_utxo_files[0])
    before_bu, after_bu = count_before_fork(decoded_utxo_files[1])

    print("Bitcoin UTXO set has {} UTXOs with height <= fork date (of a total of {})".
          format(before_btc, before_btc + after_btc))
    print("BitcoinCash UTXO set has {} UTXOs with height <= fork date  (of a total of {})".
          format(before_bu, before_bu + after_bu))
