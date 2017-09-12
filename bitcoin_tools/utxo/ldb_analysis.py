from bitcoin_tools.utils import load_conf_file
from utxo_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.plots import plot_from_file, plot_from_file_dict
from json import loads

# Load config file
cfg = load_conf_file()

# Parses transactions and utxos from the dumped data.
# transaction_dump("utxos.txt", "parsed_txs.txt")
# utxo_dump("utxos.txt", "parsed_utxos.txt")
# utxo_dump("utxos.txt", "parsed_non_std_utxos.txt", non_std_only=True)

# Generate plots from tx data (from parsed_txs.txt)
#plot_from_file("height", save_fig="tx_height")
#plot_from_file("num_utxos", xlabel="Number of utxos per tx", save_fig="tx_num_utxos")
#plot_from_file("num_utxos", xlabel="Number of utxos per tx", log_axis="x", save_fig="tx_num_utxos_logx")
#plot_from_file("total_len", xlabel="Total length (bytes)", save_fig="tx_total_len")
#plot_from_file("total_len", xlabel="Total length (bytes)",  log_axis="x", save_fig="tx_total_len_logx")
#plot_from_file("version", save_fig="tx_version")
#plot_from_file("total_value", log_axis="x", save_fig="tx_total_value_logx")

# Generate plots from utxo data (from parsed_utxo.txt)
#plot_from_file("tx_height", y="utxo", save_fig="utxo_tx_height")
#plot_from_file("amount", y="utxo", log_axis="x", save_fig="utxo_amount_logx")
#plot_from_file("index", y="utxo", save_fig="utxo_index")
#plot_from_file("index", y="utxo", log_axis="x", save_fig="utxo_index_logx")
#plot_from_file("out_type", y="utxo", save_fig="utxo_out_type")
#plot_from_file("out_type", y="utxo", log_axis="x", save_fig="utxo_out_type_logx")
#plot_from_file("utxo_data_len", y="utxo", save_fig="utxo_utxo_data_len")
#plot_from_file("utxo_data_len", y="utxo", log_axis="x", save_fig="utxo_utxo_data_len_logx")

# Generate plots for dust analysis (including percentage scale).
# plot_from_file_dict("fee_per_byte", "dust", fin="parsed_utxos.txt", save_fig="dust_utxos")

fin = open(cfg.data_path + 'dust.txt', 'r')
data = loads(fin.read())

plot_from_file_dict("fee_per_byte", "dust", data=data, save_fig="dust_utxos", legend=True)
plot_from_file_dict("fee_per_byte", "dust", data=data, percentage=True, save_fig="perc_dust_utxos")

plot_from_file_dict("fee_per_byte", "value", data=data, save_fig="dust_value")
plot_from_file_dict("fee_per_byte", "value", data=data, percentage=True, save_fig="perc_dust_value")

plot_from_file_dict("fee_per_byte", "data_len", data=data, save_fig="dust_data_len")
plot_from_file_dict("fee_per_byte", "data_len", data=data, percentage=True, save_fig="perc_dust_data_len")