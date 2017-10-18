from data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.leveldb.utils import parse_ldb, accumulate_dust_lm
from bitcoin_tools.analysis.leveldb.plots import plot_from_file, plot_from_file_dict, plot_pie_chart_from_file

# The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
# already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
# files.

f_utxos = "utxos.txt"
f_parsed_utxos = "parsed_utxos.txt"
f_parsed_txs = "parsed_txs.txt"
f_dust = "dust.txt"

# Parse all the data in the chainstate.
parse_ldb(f_utxos)

# Parses transactions and utxos from the dumped data.
transaction_dump(f_utxos, f_parsed_txs)
utxo_dump(f_utxos, f_parsed_utxos)

# Non-standard utxos can be parsed separately by setting the flag.
utxo_dump(f_utxos, "parsed_non_std_utxos.txt", non_std_only=True)

# Generate plots from tx data (from f_parsed_txs)
plot_from_file("height", save_fig="tx_height")
plot_from_file("num_utxos", xlabel="Number of utxos per tx", save_fig="tx_num_utxos")
plot_from_file("num_utxos", xlabel="Number of utxos per tx", log_axis="x", save_fig="tx_num_utxos_logx")
plot_from_file("total_len", xlabel="Total length (bytes)", save_fig="tx_total_len")
plot_from_file("total_len", xlabel="Total length (bytes)",  log_axis="x", save_fig="tx_total_len_logx")
plot_from_file("version", save_fig="tx_version")
plot_from_file("total_value", log_axis="x", save_fig="tx_total_value_logx")

# Generate plots from utxo data (from f_parsec_utxos)
plot_from_file("tx_height", y="utxo", save_fig="utxo_tx_height")
plot_from_file("amount", y="utxo", log_axis="x", save_fig="utxo_amount_logx")
plot_from_file("index", y="utxo", save_fig="utxo_index")
plot_from_file("index", y="utxo", log_axis="x", save_fig="utxo_index_logx")
plot_from_file("out_type", y="utxo", save_fig="utxo_out_type")
plot_from_file("out_type", y="utxo", log_axis="x", save_fig="utxo_out_type_logx")
plot_from_file("utxo_data_len", y="utxo", save_fig="utxo_utxo_data_len")
plot_from_file("utxo_data_len", y="utxo", log_axis="x", save_fig="utxo_utxo_data_len_logx")

plot_pie_chart_from_file("out_type", y="utxo", title="",
                         labels=['C-even', 'C-odd', 'U-even', 'U-odd'], groups=[[2], [3], [4], [5]],
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"],
                         save_fig="utxo_pk_types", font_size=20)

plot_pie_chart_from_file("out_type", y="utxo", title="",
                         labels=['P2PKH', 'P2PK', 'P2SH', 'Other'], groups=[[0], [2, 3, 4, 5], [1]],
                         colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"],
                         save_fig="utxo_types", font_size=20)

# Generate plots for dust analysis (including percentage scale).
# First, the dust accumulation file is generated (if requited).
accumulate_dust_lm(f_parsed_utxos, fout_name=f_dust)

# Finally, we can plot the data.
plot_from_file_dict("fee_per_byte", "dust", fin_name=f_dust, save_fig="dust_utxos")
plot_from_file_dict("fee_per_byte", "dust", fin_name=f_dust, percentage=True, save_fig="perc_dust_utxos")

plot_from_file_dict("fee_per_byte", "value", fin_name=f_dust, save_fig="dust_value")
plot_from_file_dict("fee_per_byte", "value", fin_name=f_dust, percentage=True, save_fig="perc_dust_value")

plot_from_file_dict("fee_per_byte", "data_len", fin_name=f_dust, save_fig="dust_data_len")
plot_from_file_dict("fee_per_byte", "data_len", fin_name=f_dust, percentage=True, save_fig="perc_dust_data_len")