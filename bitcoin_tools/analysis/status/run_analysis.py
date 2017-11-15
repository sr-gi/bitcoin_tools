from bitcoin_tools.analysis.status.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.status.utils import parse_ldb, accumulate_dust_lm
from bitcoin_tools.analysis.status.plots import plot_from_file_dict, plot_pie_chart_from_file, overview_from_file, \
    plots_from_file
from bitcoin_tools import CFG
from os import mkdir, path

# The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
# already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
# files.

# Set version and chainstate dir name
version = 0.15

# When using snapshots of the chainstate, we store it as 'chainstate/version
# chainstate = 'chainstate/' + str(version)

# When not using a snapshot, we directly use the chainstate under btc_core_dir (actually that's its default value)
chainstate = 'chainstate'

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

# In case we want to count P2SH
f_parsed_utxos_w_p2sh = str(version) + "/parsed_utxos_w_p2sh.json"
f_dust_w_p2sh = str(version) + "/dust_w_p2sh.json"

# Parse all the data in the chainstate.
parse_ldb(f_utxos, fin_name=chainstate, version=version)

# Parses transactions and utxos from the dumped data.
transaction_dump(f_utxos, f_parsed_txs, version=version)
utxo_dump(f_utxos, f_parsed_utxos, version=version)

# In case we want to count P2SH
# utxo_dump(f_utxos, f_parsed_utxos_w_p2sh, count_p2sh=True, version=version)

# Non-standard utxos can be parsed separately by setting the flag.
# utxo_dump(f_utxos, non_std_utxos, version=version, non_std_only=True)

# Print basic stats from data
overview_from_file(version)

# Generate plots from tx data (from f_parsed_txs)

plots_from_file("height", version=version, save_fig="tx_height")
plots_from_file("total_len", xlabel="Total length (bytes)", version=version, save_fig="tx_total_len")
plots_from_file("total_len", xlabel="Total length (bytes)", log_axis="x", version=version, save_fig="tx_total_len_logx")
plots_from_file("version", version=version, save_fig="tx_version")
plots_from_file("total_value", log_axis="x", version=version, save_fig="tx_total_value_logx")
plots_from_file("num_utxos", xlabel="Number of utxos per tx", version=version, save_fig="tx_num_utxos")
plots_from_file('num_utxos', xlabel="Number of utxos per tx", log_axis="x", version=version,
                save_fig="tx_num_utxos_logx")

plot_pie_chart_from_file("coinbase", y="tx", title="",
                         labels=['Coinbase', 'No-coinbasae'], groups=[[1], [0]],
                         colors=["#165873", "#428C5C"],
                         version=version, save_fig="tx_coinbase", font_size=20)

# Generate plots from utxo data (from f_parsed_utxos)

plots_from_file("tx_height", y="utxo", version=version, save_fig="utxo_tx_height")
plots_from_file("amount", y="utxo", log_axis="x", version=version, save_fig="utxo_amount_logx")
plots_from_file("index", y="utxo", version=version, save_fig="utxo_index")
plots_from_file("index", y="utxo", log_axis="x", version=version, save_fig="utxo_index_logx")
plots_from_file("out_type", y="utxo", version=version, save_fig="utxo_out_type")
plots_from_file("out_type", y="utxo", log_axis="x", version=version, save_fig="utxo_out_type_logx")
plots_from_file("utxo_data_len", y="utxo", version=version, save_fig="utxo_data_len")
plots_from_file("utxo_data_len", y="utxo", log_axis="x", version=version, save_fig="utxo_data_len_logx")
plots_from_file("index", y="utxo", version=version, save_fig="utxo_index")
plots_from_file("index", y="utxo", log_axis="x", version=version, save_fig="utxo_index_logx")

plot_pie_chart_from_file("out_type", y="utxo", title="",
                         labels=['C-even', 'C-odd', 'U-even', 'U-odd'], groups=[[2], [3], [4], [5]],
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"],
                         version=version, save_fig="utxo_pk_types", font_size=20)

plot_pie_chart_from_file("out_type", y="utxo", title="",
                         labels=['P2PKH', 'P2PK', 'P2SH', 'Other'], groups=[[0], [2, 3, 4, 5], [1]],
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"],
                         version=version, save_fig="utxo_types", font_size=20)

# We can use get_unique_values() to obtain all values for the non_std_type attribute found in the analysed samples:
# get_unique_values("non_std_type", y="utxo", version=0.15)
# Once we know all the possible values, we can create a pie chart, assigning a piece of the pie to the main values
# and grouping all the rest into an "Other" category. E.g., we create pieces for multisig 1-1, 1-2, 1-3, 2-2, 2-3
# and 3-3, and put the rest into "Other".
groups = [[u'multisig-1-3'], [u'multisig-1-2'], [u'multisig-1-1'], [u'multisig-3-3'], [u'multisig-2-2'],
          [u'multisig-2-3'],[False, u'multisig-OP_NOTIF-OP_NOTIF', u'multisig-<2153484f55544f555420544f2023424954434f494e2d415353455453202020202020202020202020202020202020202020202020202020202020202020202020>-1']]
labels = ['M. 1-3', 'M. 1-2', 'M. 1-1', 'M. 3-3', 'M. 2-2', 'M. 2-3', 'Other']

plot_pie_chart_from_file("non_std_type", y="utxo", title="",
                         labels=labels, groups=groups,
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C", "#B1D781", "#FAD02F", "#F69229"],
                         version=version, save_fig="utxo_non_std_type", font_size=20)

plots_from_file("register_len", y="utxo", version=version, save_fig="utxo_register_len")

# Generate plots with both transaction and utxo data (f_parsed_txs and f_parsed_utxos)

plots_from_file(["total_value", "amount"], y=["tx", "utxo"], xlabel="Amount (Satoshis)", version=[version]*2,
                filtr=[lambda x: True]*2,
                save_fig="tx_utxo_amount")

plots_from_file(["height", "tx_height"], y=["tx", "utxo"], xlabel="Height", version=[version]*2,
                filtr=[lambda x: True]*2,
                legend = ['Tx.', 'UTXO'], legend_loc=2,
                save_fig="tx_utxo_height")

plots_from_file(["total_value", "amount"], y=["tx", "utxo"], xlabel="Amount (Satoshis)", version=[version]*2,
                filtr=[lambda x: True]*2,
                save_fig="tx_utxo_amount")

# Generate plots with filters

plots_from_file("height", version=version, save_fig="tx_height_coinbase", filtr=lambda x: x["coinbase"])

plots_from_file(["tx_height"]*4, y=["utxo"]*4, xlabel="Tx. height", version=[version]*4, save_fig="tx_height_outtype",
                filtr=[lambda x: x["out_type"] == 0,
                       lambda x: x["out_type"] == 1,
                       lambda x: x["out_type"] in [2, 3, 4, 5],
                       lambda x: x["out_type"] not in range(0, 6)],
                legend=['P2PKH', 'P2SH', 'P2PK', 'Other'], legend_loc=2)


plots_from_file(["amount"] * 4, y=["utxo"] * 4, xlabel="Height", version=[version]*4,
                save_fig="tx_height_amount",
                filtr=[lambda x: x["amount"] < 10 ** 2,
                       lambda x: x["amount"] < 10 ** 4,
                       lambda x: x["amount"] < 10 ** 6,
                       lambda x: x["amount"] < 10 ** 8],
                legend=['$<10^2$', '$<10^4$', '$<10^6$', '$<10^8$'], legend_loc=2)

# P2SH SegWit
plots_from_file("tx_height", y="utxo", xlabel="Tx. height", version=version, save_fig="temp",
                filtr=lambda x: x["out_type"] == 1,
                legend=['P2SH'], legend_loc=2)

# Generate plots for dust analysis (including percentage scale).
# First, the dust accumulation file is generated (if requited).
# accumulate_dust_lm(f_parsed_utxos, fout_name=f_dust)

# If we want to count P2SH
accumulate_dust_lm(f_parsed_utxos_w_p2sh, fout_name=f_dust_w_p2sh)

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
