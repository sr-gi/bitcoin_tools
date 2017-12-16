from bitcoin_tools.analysis.status.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.status.utils import parse_ldb, aggregate_dust_np, set_out_names, get_samples, \
    get_filtered_samples
from bitcoin_tools.analysis.status.plots import plot_dict_from_file, plot_pie_chart_from_samples, overview_from_file, \
    plots_from_samples
from bitcoin_tools import CFG
from os import mkdir, path
from getopt import getopt
from sys import argv


def non_std_outs_analysis(samples, version):
    # We can use get_unique_values() to obtain all values for the non_std_type attribute found in the analysed samples:
    # get_unique_values("non_std_type",  fin_name=f_parsed_utxos)

    # Once we know all the possible values, we can create a pie chart, assigning a piece of the pie to the main values
    # and grouping all the rest into an "Other" category. E.g., we create pieces for multisig 1-1, 1-2, 1-3, 2-2, 2-3
    # and 3-3, and put the rest into "Other".

    groups = [[u'multisig-1-3'], [u'multisig-1-2'], [u'multisig-1-1'], [u'multisig-3-3'], [u'multisig-2-2'],
              [u'multisig-2-3'], [False, u'multisig-OP_NOTIF-OP_NOTIF',
                                  u'multisig-<2153484f55544f555420544f2023424954434f494e2d41535345545320202020202020202'
                                  u'0202020202020202020202020202020202020202020202020202020>-1']]
    labels = ['M. 1-3', 'M. 1-2', 'M. 1-1', 'M. 3-3', 'M. 2-2', 'M. 2-3', 'Other']

    out_name = "utxo_non_std_type"

    # ToDo: Properly rearrange labels (the are colluding)
    plot_pie_chart_from_samples(samples=samples, save_fig=out_name, labels=labels, version=version, groups=groups,
                                title="",  colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C", "#B1D781", "#FAD02F",
                                                   "#F69229"])


def tx_based_analysis(tx_fin_name, version=0.15):
    x_attributes = ['height', 'total_len', 'version', 'total_value', 'num_utxos']

    xlabels = ['Height', 'Total length (bytes)', 'Version', 'Total value', 'Number of UTXOs per tx']

    out_names = ["tx_height", ["tx_total_len", "tx_total_len_logx"], 'tx_version', "tx_total_value_logx",
                 ["tx_num_utxos", "tx_num_utxos_logx"]]

    log_axis = [False, [False, 'x'], False, 'x', [False, 'x']]

    x_attr_pie = ['coinbase']
    xlabels_pie = [['Coinbase', 'No-coinbase']]
    out_names_pie = ['tx_coinbase']
    pie_groups = [[[1], [0]]]
    pie_colors = [["#165873", "#428C5C"]]

    # Version has been dropped of in version 0.15, so there is no need of parsing Null data for 0.15 onwards.
    if version >= 0.15:
        i = x_attributes.index('version')
        x_attributes.pop(i)
        xlabels.pop(i)
        out_names.pop(i)
        log_axis.pop(i)

    samples = get_samples(x_attributes + x_attr_pie,  fin_name=tx_fin_name)

    for attribute, label, log, out in zip(x_attributes, xlabels, log_axis, out_names):
        plots_from_samples(x_attribute=attribute, samples=samples[attribute], xlabel=label, log_axis=log, save_fig=out,
                           version=str(version), ylabel="Number of txs")

    for attribute, label, out, groups, colors in (zip(x_attr_pie, xlabels_pie, out_names_pie, pie_groups, pie_colors)):
        plot_pie_chart_from_samples(samples=samples[attribute], save_fig=out, labels=label,
                                    title="", version=version, groups=groups, colors=colors)


def utxo_based_analysis(tx_fin_name, version=0.15):
    x_attributes = ['tx_height', 'amount', 'index', 'out_type', 'utxo_data_len', 'register_len']

    xlabels = ['Tx. height', 'Amount', 'UTXO Index', 'Out type', 'UTXO data len.', 'Register len.']

    out_names = ["utxo_tx_height", "utxo_amount_logx", ["utxo_index", "utxo_index_logx"],
                 ["utxo_out_type", "utxo_out_type_logx"], ["utxo_data_len", "utxo_data_len_logx"],
                 ['utxo_register_len', 'utxo_register_len_logx']]

    log_axis = [False, 'x', [False, 'x'], [False, 'x'], [False, 'x'], [False, 'x']]

    x_attributes_pie = ['out_type', 'out_type']
    xlabels_pie = [['C-even', 'C-odd', 'U-even', 'U-odd'], ['P2PKH', 'P2PK', 'P2SH', 'Other']]
    out_names_pie = ["utxo_pk_types", "utxo_types"]
    pie_groups = [[[2], [3], [4], [5]], [[0], [2, 3, 4, 5], [1]]]

    x_attribute_special = 'non_std_type'

    # Since the attributes for the pie chart are already included in the normal chart, we won't pass them to the
    # sampling function.
    samples = get_samples(x_attributes + [x_attribute_special], fin_name=tx_fin_name)

    for attribute, label, log, out in zip(x_attributes, xlabels, log_axis, out_names):
        plots_from_samples(x_attribute=attribute, samples=samples[attribute], xlabel=label, log_axis=log, save_fig=out,
                           version=str(version), ylabel="Number of UTXOs")

    for attribute, label, out, groups in (zip(x_attributes_pie, xlabels_pie, out_names_pie, pie_groups)):
        plot_pie_chart_from_samples(samples=samples[attribute], save_fig=out, labels=label,
                                    title="", version=version, groups=groups, colors=["#165873", "#428C5C",
                                                                                      "#4EA64B", "#ADD96C"])
    # Special case: non-standard
    non_std_outs_analysis(samples[x_attribute_special], version)


def dust_analysis(utxo_fin_name, f_dust, version):
    # Generate plots for dust analysis (including percentage scale).
    # First, the dust accumulation file is generated
    aggregate_dust_np(utxo_fin_name, fout_name=f_dust)

    ys = ["dust", "value", "data_len"]
    outs = ["dust_utxos", "dust_value", "dust_data_len"]

    # Plot the aggregated data (with and without percentage axis).
    for y, out in zip(ys, outs):
        plot_dict_from_file(y, fin_name=f_dust, version=version, save_fig=out)
        plot_dict_from_file(y, fin_name=f_dust, percentage=True, version=version,
                            save_fig="perc_"+out)


def comparative_data_analysis(tx_fin_name, utxo_fin_name, version):

    # Generate plots with both transaction and utxo data (f_parsed_txs and f_parsed_utxos)
    tx_attributes = ['total_value', 'height']
    utxo_attributes = ['amount', 'tx_height']

    xlabels = ['Amount (Satoshi)', 'Height']
    out_names = ['tx_utxo_amount', 'tx_utxo_height']
    legends = [['Tx.', 'UTXO'], ['Tx.', 'UTXO']]
    legend_locations = [1, 2]

    tx_samples = get_samples(tx_attributes, tx_fin_name)
    utxo_samples = get_samples(utxo_attributes, utxo_fin_name)

    for tx_attr, utxo_attr, label, out, legend, leg_loc in zip(tx_attributes, utxo_attributes, xlabels, out_names,
                                                               legends, legend_locations):
        plots_from_samples(x_attribute=[tx_attr, utxo_attr], xlabel=label, save_fig=out, version=str(version),
                           samples=[tx_samples[tx_attr], utxo_samples[utxo_attr]], legend=legend, legend_loc=leg_loc,
                           y="Number of registers", comparative=True)


def utxo_based_analysis_with_filters(utxo_fin_name, version=0.15):
    x_attribute = 'tx_height'
    xlabel = 'Block height'
    out_names = ['utxo_height_out_type', 'utxo_height_amount', 'segwit_upper_bound']

    filters = [lambda x: x["out_type"] == 0,
               lambda x: x["out_type"] == 1,
               lambda x: x["out_type"] in [2, 3, 4, 5],
               lambda x: x["out_type"] not in range(0, 6),
               lambda x: x["amount"] < 10 ** 2,
               lambda x: x["amount"] < 10 ** 4,
               lambda x: x["amount"] < 10 ** 6,
               lambda x: x["amount"] < 10 ** 8,
               lambda x: x["out_type"] == 1]

    legends = [['P2PKH', 'P2SH', 'P2PK', 'Other'], ['$<10^2$', '$<10^4$', '$<10^6$', '$<10^8$'], ['P2SH']]
    comparative = [True, True, False]
    legend_loc = 2
    offset = 0

    samples = get_filtered_samples(x_attribute, fin_name=utxo_fin_name, filtr=filters)

    for out, flt, legend, comp in zip(out_names, filters, legends, comparative):
        plots_from_samples(x_attribute=[x_attribute] * len(legend), samples=samples[offset:offset + len(legend)],
                           xlabel=xlabel, save_fig=out, legend=legend, legend_loc=legend_loc, version=str(version),
                           comparative=comp, ylabel="Number of UTXOs")
        offset += len(legend)


def tx_based_analysis_with_filters(tx_fin_name, version=0.15):
    x_attributes = 'height'
    xlabels = ['Height']
    out_names = ['tx_height_coinbase']
    filters = [lambda x: x["coinbase"]]

    samples = get_filtered_samples(x_attributes, fin_name=tx_fin_name, filtr=filters)

    for attribute, label, out in zip(x_attributes, xlabels, out_names):
        plots_from_samples(x_attribute=attribute, samples=samples, xlabel=label, save_fig=out, version=str(version),
                           y="Number of txs")


def run_experiment(version, chainstate, count_p2sh, non_std_only):
    # The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
    # already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
    # files.

    # Check if the directories for both data and figures exist, create them otherwise.
    if not path.isdir(CFG.data_path + str(version)) and not path.isdir(CFG.figs_path + str(version)):
        mkdir(CFG.data_path + str(version))
        mkdir(CFG.figs_path + str(version))

    # Set the name of the output data files
    f_utxos, f_parsed_txs, f_parsed_utxos, f_dust = set_out_names(version, count_p2sh, non_std_only)

    # Parse all the data in the chainstate.
    print "Parsing the chainstate."
    parse_ldb(f_utxos, fin_name=chainstate, version=version)

    # Parses transactions and utxos from the dumped data.
    print "Adding meta-data for transactions and UTXOs."
    transaction_dump(f_utxos, f_parsed_txs, version=version)
    utxo_dump(f_utxos, f_parsed_utxos, count_p2sh=count_p2sh, non_std_only=non_std_only, version=version)

    # Print basic stats from data
    print "Running overview analysis."
    overview_from_file(f_parsed_txs, f_parsed_utxos)

    # Generate plots from tx data (from f_parsed_txs)
    print "Running transaction based analysis."
    tx_based_analysis(f_parsed_txs)

    # Generate plots from utxo data (from f_parsed_utxos)
    print "Running UTXO based analysis."
    utxo_based_analysis(f_parsed_utxos)

    # Aggregates dust and generates plots it.
    print "Running dust analysis."
    dust_analysis(f_parsed_utxos, f_dust, version)

    # Comparative data analysis (transactions and UTXOs)
    print "Running comparative data analysis."
    comparative_data_analysis(f_parsed_txs, f_parsed_utxos, version)

    # Generate plots with filters
    print "Running analysis with filters."
    utxo_based_analysis_with_filters(f_parsed_utxos, version)
    tx_based_analysis_with_filters(f_parsed_txs, version)


if __name__ == '__main__':

    if len(argv) > 1:
        # Get params from call
        _, args = getopt(argv, ['count_p2sh', 'non_std'])
        count_p2sh = True if '--count_p2sh' in args else False
        non_std_only = True if '--non_std' in args else False
    else:
        # Default params
        non_std_only = False
        count_p2sh = True

    # Set version and chainstate dir name
    version = 0.15

    # When using snapshots of the chainstate, we store it as 'chainstate/version
    # chainstate = 'chainstate/' + str(version)

    # When not using a snapshot, we directly use the chainstate under btc_core_dir (actually that's its default value)
    chainstate = 'chainstate'

    run_experiment(version, chainstate, count_p2sh, non_std_only)
