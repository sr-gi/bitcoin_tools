from bitcoin_tools.analysis.leveldb.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.leveldb.utils import parse_ldb, accumulate_dust_lm
from bitcoin_tools.analysis.leveldb.plots import plot_from_file, plot_from_file_dict, plot_pie_chart_from_file, overview_from_file
from bitcoin_tools import CFG
from os import mkdir, path

# The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
# already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
# files.

# Set version and chainstate dir name
version = 0.15

# When using snapshots of the chainstate, we store it as 'chainstate/version
chainstate = 'chainstate/' + str(version)

# When not using a snapshot, we directly use the chainstate under btc_core_dir (actually that's its default value)
# chainstate = 'chainstate'

# Check if the directories for both data and figures exist, create them otherwise.
if not path.isdir(CFG.data_path + str(version)) and not path.isdir(CFG.figs_path + str(version)):
    mkdir(CFG.data_path + str(version))
    mkdir(CFG.figs_path + str(version))

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

# Non-standard utxos can be parsed separately by setting the flag.
utxo_dump(f_utxos, non_std_utxos, version=version, non_std_only=True)

# Print basic stats from data
overview_from_file(version)

# Generate plots from tx data (from f_parsed_txs)
plot_from_file("height", version=version, save_fig="tx_height")
plot_from_file("total_len", xlabel="Total length (bytes)", version=version, save_fig="tx_total_len")
plot_from_file("total_len", xlabel="Total length (bytes)", log_axis="x", version=version, save_fig="tx_total_len_logx")
plot_from_file("version", version=version, save_fig="tx_version")
plot_from_file("total_value", log_axis="x", version=version, save_fig="tx_total_value_logx")
plot_from_file("num_utxos", xlabel="Number of utxos per tx", version=version, save_fig="tx_num_utxos")
plot_from_file("num_utxos", xlabel="Number of utxos per tx", log_axis="x", version=version, save_fig="tx_num_utxos_logx")

plot_pie_chart_from_file("coinbase", y="tx", title="",
                         labels=['Coinbase', 'No-coinbasae'], groups=[[1], [0]],
                         colors=["#165873", "#428C5C"],
                         version=version, save_fig="tx_coinbase", font_size=20)

# Generate plots from utxo data (from f_parsed_utxos)
plot_from_file("tx_height", y="utxo", version=version, save_fig="utxo_tx_height")
plot_from_file("amount", y="utxo", log_axis="x", version=version, save_fig="utxo_amount_logx")
plot_from_file("index", y="utxo", version=version, save_fig="utxo_index")
plot_from_file("index", y="utxo", log_axis="x", version=version, save_fig="utxo_index_logx")
plot_from_file("out_type", y="utxo", version=version, save_fig="utxo_out_type")
plot_from_file("out_type", y="utxo", log_axis="x", version=version, save_fig="utxo_out_type_logx")
plot_from_file("utxo_data_len", y="utxo", version=version, save_fig="utxo_data_len")
plot_from_file("utxo_data_len", y="utxo", log_axis="x", version=version, save_fig="utxo_data_len_logx")
plot_from_file("index", y="utxo", version=version, save_fig="utxo_index")
plot_from_file("index", y="utxo", log_axis="x", version=version, save_fig="utxo_index_logx")

plot_pie_chart_from_file("out_type", y="utxo", title="",
                         labels=['C-even', 'C-odd', 'U-even', 'U-odd'], groups=[[2], [3], [4], [5]],
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"],
                         version=version, save_fig="utxo_pk_types", font_size=20)

plot_pie_chart_from_file("out_type", y="utxo", title="",
                         labels=['P2PKH', 'P2PK', 'P2SH', 'Other'], groups=[[0], [2, 3, 4, 5], [1]],
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"],
                         version=version, save_fig="utxo_types", font_size=20)

# Generate plots for dust analysis (including percentage scale).
# First, the dust accumulation file is generated (if requited).

accumulate_dust_lm(f_parsed_utxos, fout_name=f_dust)

# Finally, we can plot the data.
plot_from_file_dict("fee_per_byte", "dust", fin_name=f_dust, version=version, save_fig="dust_utxos")
plot_from_file_dict("fee_per_byte", "dust", fin_name=f_dust, percentage=True, version=version,
                    save_fig="perc_dust_utxos")

plot_from_file_dict("fee_per_byte", "value", fin_name=f_dust, version=version, save_fig="dust_value")
plot_from_file_dict("fee_per_byte", "value", fin_name=f_dust, percentage=True, version=version,
                    save_fig="perc_dust_value")

plot_from_file_dict("fee_per_byte", "data_len", fin_name=f_dust, version=version, save_fig="dust_data_len")
plot_from_file_dict("fee_per_byte", "data_len", fin_name=f_dust, percentage=True, version=version,
                    save_fig="perc_dust_data_len")
