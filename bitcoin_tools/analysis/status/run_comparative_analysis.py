from bitcoin_tools.analysis.status.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.status.utils import parse_ldb
from bitcoin_tools.analysis.status.plots import plots_from_file
from bitcoin_tools import CFG
from os import mkdir, path

# The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
# already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
# files.

# Set version and chainstate dir name
version = [0.14, 0.15]
str_version = "-".join([str(v) for v in version])

for v in version:
    # When using snapshots of the chainstate, we store it as 'chainstate/version
    chainstate = 'chainstate/' + str(version)

    # Check if the directory for data exists, create it otherwise.
    if not path.isdir(CFG.data_path + str(version)):
        mkdir(CFG.data_path + str(version))

    # Set the name of the output data files
    f_utxos = str(version) + "/utxos.json"
    f_parsed_utxos = str(version) + "/parsed_utxos.json"
    f_parsed_txs = str(version) + "/parsed_txs.json"
    f_dust = str(version) + "/dust.json"
    non_std_utxos = str(version) + "/parsed_non_std_utxos.json"

    # Parse all the data in the chainstate.
    parse_ldb(f_utxos, fin_name=chainstate, version=version)

    # Parses transactions and utxos from the dumped data.
    transaction_dump(f_utxos, f_parsed_txs, version=version)
    utxo_dump(f_utxos, f_parsed_utxos, version=version)


# Check if the directory for figures exist, create it otherwise.
if not path.isdir(CFG.figs_path + str(version)):
    mkdir(CFG.figs_path + str(version))


# Generate plots from tx and utxo data

plots_from_file(["total_len"]*2, y=["tx"]*2, xlabel="Total length (bytes)", log_axis="x", version=[0.14, 0.15],
                filtr=[lambda x: True]*2,
                save_fig="tx_total_len_logx_0.14-0.15")
plots_from_file(["register_len", "total_len"], y=["utxo", "tx"], xlabel="Register size (in bytes)",
                version=[0.15, 0.14], filtr=[lambda x: True] * 2, save_fig="tx_register_size_all")

plots_from_file(["total_len"]*2, y=["tx"]*2, xlabel="Total length (bytes)", log_axis="x", version=[0.14, 0.15],
                filtr=[lambda x: True]*2,
                legend=["v0.14", "v0.15"],
                save_fig="tx_total_len_logx_0.14-0.15")