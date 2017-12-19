from bitcoin_tools.analysis.status.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.status.utils import parse_ldb, set_out_names, get_samples
from bitcoin_tools.analysis.status.plots import plots_from_samples
from bitcoin_tools import CFG
from os import mkdir, path


def run_comparative_analysis_14_15():

    # Generate plots from tx and utxo data

    version_str = "0.14-0.15"

    # 0.14
    v = 0.14
    tx_fin_name_14 = str(v) + "/parsed_txs.json"
    utxo_fin_name_14  = str(v) + "/parsed_utxos_wp2sh.json"
    tx_attributes_14 = ['total_len']
    utxo_attributes_14 = ['utxo_data_len']

    tx_samples_14 = get_samples(tx_attributes_14, tx_fin_name_14)
    utxo_samples_14 = get_samples(utxo_attributes_14, utxo_fin_name_14)

    # 0.15
    v = 0.15
    tx_fin_name_15 = str(v) + "/parsed_txs.json"
    utxo_fin_name_15  = str(v) + "/parsed_utxos_wp2sh.json"
    tx_attributes_15 = ['total_len']
    utxo_attributes_15 = ['register_len', 'utxo_data_len']

    tx_samples_15 = get_samples(tx_attributes_15, tx_fin_name_15)
    utxo_samples_15 = get_samples(utxo_attributes_15, utxo_fin_name_15)

    # TODO: why is x_attribute used?

    # Compare transaction storage space:
    # - register length of v0.14 (tx -> total_len)
    # - sum of register lengths of utxos from that tx in v0.15 (tx -> total_len)
    plots_from_samples(samples=[tx_samples_14['total_len'], tx_samples_15['total_len']],
                       x_attribute=['total_len'], xlabel="Transaction len. (bytes)", log_axis="x",
                       version=version_str, comparative=True,
                       save_fig="tx_total_len_logx_0.14-0.15", legend = ["v0.14", "v0.15"])


    # Compare register lenghts of v0.14 (tx) vs v0.15 (utxo)
    # - transation total_len of v0.14
    # - utxo register_len of v0.15
    # x_attribute=['total_len', 'register_len']
    plots_from_samples(samples=[tx_samples_14['total_len'], utxo_samples_15['register_len']],
                       x_attribute=['aa'], xlabel="Register size (in bytes)", log_axis="x",
                       version=version_str, comparative=True,
                       save_fig="register_len_logx_0.14-0.15", legend=["v0.14", "v0.15"])


    # Compare utxo data storage space:
    # - utxo_data_len of v0.15
    # - utxo_data_len of v0.14 # TODO: check what have we stored exactly here! Does this make sense?
    plots_from_samples(samples=[utxo_samples_14['utxo_data_len'], utxo_samples_15['utxo_data_len']],
                       x_attribute=['aa'], xlabel="UTXO data len (in bytes)", log_axis="x",
                       version=version_str, comparative=True,
                       save_fig="utxo_data_len_logx_0.14-0.15", legend=["v0.14", "v0.15"])



def create_comparative_analysis_files(versions, count_p2sh, non_std_only):
    # The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
    # already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
    # files.

    # Set version and chainstate dir name
    str_version = "-".join([str(v) for v in versions])

    fins = dict()
    for v in versions:
        # When using snapshots of the chainstate, we store it as 'chainstate/version
        chainstate = 'chainstate/' + str(v)

        # When not using a snapshot, we directly use the chainstate under btc_core_dir
        # chainstate = 'chainstate'

        # Check if the directory for data exists, create it otherwise.
        if not path.isdir(CFG.data_path + str(v)):
            mkdir(CFG.data_path + str(v))

        # Set the name of the output data files
        f_utxos, f_parsed_txs, f_parsed_utxos, f_dust = set_out_names(v, count_p2sh, non_std_only)

        fins[str(v)] = [f_parsed_txs, f_parsed_utxos]
        # Parse all the data in the chainstate.
        parse_ldb(f_utxos, fin_name=chainstate, version=v)

        # Parses transactions and utxos from the dumped data.
        transaction_dump(f_utxos, f_parsed_txs, version=v)
        utxo_dump(f_utxos, f_parsed_utxos, version=v)

    # Check if the directory for figures exist, create it otherwise.
    if not path.isdir(CFG.figs_path + str_version):
        mkdir(CFG.figs_path + str_version)


if __name__ == '__main__':
    # Params
    non_std_only = False
    count_p2sh = True

    # Set version
    versions = [0.14, 0.15]

    create_comparative_analysis_files(versions, count_p2sh, non_std_only)

    run_comparative_analysis_14_15()
