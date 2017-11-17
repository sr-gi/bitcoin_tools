from bitcoin_tools.analysis.status.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.status.utils import parse_ldb, set_out_names
from bitcoin_tools.analysis.status.plots import plots_from_file
from bitcoin_tools import CFG
from os import mkdir, path


def run_comparative_analysis(versions, count_p2sh, non_std_only):
    # The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
    # already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
    # files.

    # Set version and chainstate dir name
    str_version = "-".join([str(v) for v in versions])

    fins = dict()
    for v in versions:
        # When using snapshots of the chainstate, we store it as 'chainstate/version
        # chainstate = 'chainstate/' + str(v)

        # When not using a snapshot, we directly use the chainstate under btc_core_dir
        chainstate = 'chainstate'

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

    # Generate plots from tx and utxo data

    plots_from_file(["total_len"]*2, y=["tx"]*2, xlabel="Total length (bytes)", log_axis="x", version=str_version,
                    filtr=[lambda x: True]*2,
                    fin_name=[fins['0.14'][0], fins['0.15'][0]], save_fig="tx_total_len_logx_0.14-0.15")

    plots_from_file(["register_len", "total_len"], y=["utxo", "tx"], xlabel="Register size (in bytes)",
                    version=str_version, filtr=[lambda x: True] * 2, fin_name=[fins['0.14'][0], fins['0.15'][1]],
                    save_fig="tx_register_size_all")

    plots_from_file(["total_len"]*2, y=["utxos"]*2, xlabel="Total length (bytes)", log_axis="x", version=str_version,
                    filtr=[lambda x: True]*2,
                    legend=["v0.14", "v0.15"],
                    fin_name=[fins['0.14'][1], fins['0.15'][1]], save_fig="utxo_total_len_logx_0.14-0.15")


if __name__ == '__main__':
    # Params
    non_std_only = False
    count_p2sh = True

    # Set version
    versions = [0.14, 0.15]

    run_comparative_analysis(versions, count_p2sh, non_std_only)
