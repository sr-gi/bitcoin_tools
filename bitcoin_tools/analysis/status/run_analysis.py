from bitcoin_tools.analysis.plots import get_cdf
from bitcoin_tools.analysis.status.data_dump import transaction_dump, utxo_dump
from bitcoin_tools.analysis.status.utils import parse_ldb, aggregate_dust_np
from data_processing import get_samples, get_filtered_samples
from bitcoin_tools.analysis.status.plots import plot_pie_chart_from_samples, overview_from_file, plots_from_samples
from bitcoin_tools import CFG
from getopt import getopt
from sys import argv


def set_out_names(count_p2sh, non_std_only):
    """
    Set the name of the input / output files from the experiment depending on the given flags.
    :param count_p2sh: Whether P2SH should be taken into account.
    :type count_p2sh: bool
    :param non_std_only: Whether the experiment will be run only considering non standard outputs.
    :type non_std_only: bool
    :return: Four string representing the names of the utxo, parsed_txs, parsed_utxos and dust file names.
    :rtype: str, str, str, str
    """

    f_utxos = "/decoded_utxos.json"
    f_parsed_txs = "/parsed_txs.json"
    # In case of the parsed files we consider the parameters
    f_parsed_utxos = "/parsed_utxos"
    f_dust = "/dust"

    if non_std_only:
        f_parsed_utxos += "_nstd"
        f_dust += "_nstd"

    if count_p2sh:
        f_parsed_utxos += "_wp2sh"
        f_dust += "_wp2sh"

    f_parsed_utxos += ".json"
    f_dust += ".json"

    return f_utxos, f_parsed_txs, f_parsed_utxos, f_dust


def non_std_outs_analysis(samples):
    """
    Perform the non standard out analysis for a given set of samples.

    :param samples: List of samples that will form the chart.
    :type samples: list
    :return: None
    :rtype: None
    """

    # We can use get_unique_values() to obtain all values for the non_std_type attribute found in the analysed samples:
    # get_unique_values("non_std_type",  fin_name=f_parsed_utxos)

    # Once we know all the possible values, we can create a pie chart, assigning a piece of the pie to the main values
    # and grouping all the rest into an "Other" category. E.g., we create pieces for multisig 1-1, 1-2, 1-3, 2-2, 2-3
    # and 3-3, and put the rest into "Other".

    groups = [[u'multisig-1-3'], [u'multisig-1-2'], [u'multisig-1-1'], [u'multisig-3-3'], [u'multisig-2-2'],
              [u'multisig-2-3'], ["P2WSH"], ["P2WPKH"], [False, u'multisig-OP_NOTIF-OP_NOTIF',
                                  u'multisig-<2153484f55544f555420544f2023424954434f494e2d41535345545320202020202020202'
                                  u'0202020202020202020202020202020202020202020202020202020>-1']]
    labels = ['M. 1-3', 'M. 1-2', 'M. 1-1', 'M. 3-3', 'M. 2-2', 'M. 2-3', "P2WSH", "P2WPKH", 'Other']

    out_name = "utxo_non_std_type"

    plot_pie_chart_from_samples(samples=samples, save_fig=out_name, labels=labels, groups=groups, title="",
                                colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C", "#B1D781", "#FAD02F",
                                                   "#A69229", "#B69229", "#F69229"], labels_out=True)


def tx_based_analysis(tx_fin_name):
    """
    Performs a transaction based analysis from a given input file (resulting from a transaction dump of the chainstate)

    :param tx_fin_name: Input file path which contains the chainstate transaction dump.
    :type: str
    :return: None
    :rtype: None
    """

    x_attributes = ['height', 'total_len', 'total_value', 'num_utxos']

    xlabels = ['Height', 'Total length (bytes)', 'Total value', 'Number of UTXOs per tx']

    out_names = ["tx_height", ["tx_total_len", "tx_total_len_logx"], "tx_total_value_logx",
                 ["tx_num_utxos", "tx_num_utxos_logx"]]

    log_axis = [False, [False, 'x'], 'x', [False, 'x']]

    x_attr_pie = 'coinbase'
    xlabels_pie = [['Coinbase', 'No-coinbase']]
    out_names_pie = ['tx_coinbase']
    pie_groups = [[[1], [0]]]
    pie_colors = [["#165873", "#428C5C"]]

    samples = get_samples(x_attributes + [x_attr_pie],  fin_name=tx_fin_name)
    samples_pie = samples.pop(x_attr_pie)

    for attribute, label, log, out in zip(x_attributes, xlabels, log_axis, out_names):
        xs, ys = get_cdf(samples[attribute], normalize=True)
        plots_from_samples(xs=xs, ys=ys, xlabel=label, log_axis=log, save_fig=out, ylabel="Number of txs")

    for label, out, groups, colors in (zip(xlabels_pie, out_names_pie, pie_groups, pie_colors)):
        plot_pie_chart_from_samples(samples=samples_pie, save_fig=out, labels=label, title="", groups=groups,
                                    colors=colors, labels_out=True)


def utxo_based_analysis(utxo_fin_name):
    """
    Performs a utxo based analysis from a given input file (resulting from a utxo dump of the chainstate)

    :param utxo_fin_name: Input file path which contains the chainstate utxo dump.
    :type: str
    :return: None
    :rtype: None
    """

    x_attributes = ['tx_height', 'amount', 'index', 'out_type', 'utxo_data_len', 'register_len']

    xlabels = ['Tx. height', 'Amount', 'UTXO index', 'Out type', 'UTXO data length', 'Register length']

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
    samples = get_samples(x_attributes + [x_attribute_special], fin_name=utxo_fin_name)
    samples_special = samples.pop(x_attribute_special)

    for attribute, label, log, out in zip(x_attributes, xlabels, log_axis, out_names):
        xs, ys = get_cdf(samples[attribute], normalize=True)
        plots_from_samples(xs=xs, ys=ys, xlabel=label, log_axis=log, save_fig=out, ylabel="Number of UTXOs")

    for attribute, label, out, groups in (zip(x_attributes_pie, xlabels_pie, out_names_pie, pie_groups)):
        plot_pie_chart_from_samples(samples=samples[attribute], save_fig=out, labels=label, title="", groups=groups,
                                    colors=["#165873", "#428C5C", "#4EA64B", "#ADD96C"], labels_out=True)
    # Special case: non-standard
    non_std_outs_analysis(samples_special)


def dust_analysis(utxo_fin_name, f_dust, fltr=None):
    """
    Performs a dust analysis by aggregating al the dust of a utxo dump file.

    :param utxo_fin_name: Input file path which contains the chainstate utxo dump.
    :type: str
    :param f_dust: Output file name where the aggregated dust will be stored.
    :type f_dust: str
    :param fltr: Filter to be applied to the samples. None by default.
    :type fltr: function
    :return: None
    :rtype: None
    """

    # Generate plots for dust analysis (including percentage scale).
    # First, the dust accumulation file is generated
    data = aggregate_dust_np(utxo_fin_name, fout_name=f_dust, fltr=fltr)

    # # Or we can load it from a dust file if we have already created it
    # data = load(open(CFG.data_path + f_dust))

    dict_labels = [["dust_utxos", "np_utxos", "npest_utxos"],
                   ["dust_value", "np_value", "npest_value"],
                   ["dust_data_len", "np_data_len", "npest_data_len"]]
    outs = ["dust_utxos", "dust_value", "dust_data_len"]
    totals = ['total_utxos', 'total_value', 'total_data_len']
    ylabels = ["Number of UTXOs", "UTXOs Amount (satoshis)", "UTXOs Sizes (bytes)"]
    legend = ["Dust", "Non-profitable min.", "Non-profitable est."]

    for labels, out, total, ylabel in zip(dict_labels, outs, totals, ylabels):
        xs = [sorted(data[l].keys(), key=int) for l in labels]
        ys = [sorted(data[l].values(), key=int) for l in labels]

        plots_from_samples(xs=xs, ys=ys, save_fig=out, legend=legend, legend_loc=4, xlabel='Fee rate (sat./byte)',
                           ylabel=ylabel)

        # Get values in percentage
        ys_perc = []
        for y_samples in ys:
            y_perc = [y / float(data[total]) for y in y_samples]
            ys_perc.append(y_perc)

        plots_from_samples(xs=xs, ys=ys_perc, save_fig='perc_' + out, legend=legend, legend_loc=4,
                           xlabel='Fee rate (sat./byte)', ylabel=ylabel)


def dust_analysis_all_fees(utxo_fin_name):
    """
    Performs a dust analysis for all fee rates, that is, up until all samples are considered dust (plot shows cdf up
    until 1).

    :param utxo_fin_name: Input file path which contains the chainstate utxo dump.
    :type: str
    :return: None
    :rtype: None
    """

    x_attributes = [["dust", "non_profitable", "non_profitable_est"]]
    xlabels = ['Dust/non_prof_min/non_prof_est value']
    out_names = ["dust_utxos_all"]
    legends = [["Dust", "Non-profitable min.", "Non-profitable est."]]
    log_axis = ['x']

    for attribute, label, log, out, legend in zip(x_attributes, xlabels, log_axis, out_names, legends):
        samples = get_samples(attribute, fin_name=utxo_fin_name)
        xs = []
        ys = []
        for a in attribute:
            x, y = get_cdf(samples[a], normalize=True)
            xs.append(x)
            ys.append(y)

        plots_from_samples(xs=xs, ys=ys, xlabel=label, log_axis=log, save_fig=out, ylabel="Number of UTXOs",
                           legend=legend, legend_loc=4)


def utxo_based_analysis_with_filters(utxo_fin_name):
    """
    Performs an utxo data analysis using different filters, to obtain for examples the amount of SegWit outputs.

    :param utxo_fin_name: Input file path which contains the chainstate utxo dump.
    :type: str
    :return: None
    :rtype: None
    """

    x_attribute = 'tx_height'
    xlabel = 'Block height'
    out_names = ['utxo_height_out_type', 'utxo_height_amount', 'segwit_upper_bound', 'utxo_height_1_satoshi']

    filters = [lambda x: x["out_type"] == 0,
               lambda x: x["out_type"] == 1,
               lambda x: x["out_type"] in [2, 3, 4, 5],
               lambda x: x["non_std_type"] == "P2WPKH",
               lambda x: x["non_std_type"] == "P2WSH",
               lambda x: x["non_std_type"] is not False and "multisig" in x["non_std_type"],
               lambda x: x["non_std_type"] is False,
               lambda x: x["amount"] == 1,
               lambda x: 1 < x["amount"] <= 10 ** 1,
               lambda x: 10 < x["amount"] <= 10 ** 2,
               lambda x: 10 ** 2 < x["amount"] <= 10 ** 4,
               lambda x: 10 ** 4 < x["amount"] <= 10 ** 6,
               lambda x: 10 ** 6 < x["amount"] <= 10 ** 8,
               lambda x: x["amount"] > 10**8,
               lambda x: x["out_type"] == 1,
               lambda x: x["amount"] == 1]

    legends = [['P2PKH', 'P2SH', 'P2PK', 'P2WPKH', 'P2WSH', 'Multisig', 'Other'],
               ['$=1$', '$1 < x \leq 10$', '$10 < x \leq 10^2$', '$10^2 < x \leq 10^4$', '$10^4 < x \leq 10^6$',
                '$10^6 < x \leq 10^8$', '$10^8 < x$'], ['P2SH'], ['Amount = 1']]
    comparative = [True, True, False, False]
    legend_loc = 2

    samples = get_filtered_samples(x_attribute, fin_name=utxo_fin_name, filtr=filters)

    for out, legend, comp in zip(out_names, legends, comparative):
        xs = []
        ys = []
        for _ in range(len(legend)):
            x, y = get_cdf(samples.pop(0), normalize=True)
            xs.append(x)
            ys.append(y)

        plots_from_samples(xs=xs, ys=ys, xlabel=xlabel, save_fig=out, legend=legend, legend_loc=legend_loc,
                           ylabel="Number of UTXOs")


def tx_based_analysis_with_filters(tx_fin_name):
    """
    Performs a transaction data analysis using different filters, to obtain for example the amount of coinbase
    transactions.

    :param tx_fin_name: Input file path which contains the chainstate transaction dump.
    :type: str
    :return: None
    :rtype: None
    """

    x_attributes = 'height'
    xlabels = ['Height']
    out_names = ['tx_height_coinbase']
    filters = [lambda x: x["coinbase"]]

    samples = get_filtered_samples(x_attributes, fin_name=tx_fin_name, filtr=filters)
    xs, ys = get_cdf(samples, normalize=True)

    for label, out in zip(xlabels, out_names):
        plots_from_samples(xs=xs, ys=ys, xlabel=label, save_fig=out, ylabel="Number of txs")


def run_experiment(coin, chainstate, count_p2sh, non_std_only):
    """
    Runs the whole experiment. You may comment the parts of it you are not interested in to save time.

    :param coin: Coin to be used in the experiment (bitcoin, litecoin, bitcoin cash, ...)
    :type coin: str
    :param chainstate: Chainstate path.
    :type chainstate: str
    :param count_p2sh: Whether P2SH outputs are included in the experiment or not.
    :type count_p2sh: bool
    :param non_std_only: Whether the experiment is performed only counting non standard outputs.
    :type non_std_only:bool
    :return:
    """

    # The following analysis reads/writes from/to large data files. Some of the steps can be ignored if those files have
    # already been created (if more updated data is not requited). Otherwise lot of time will be put in re-parsing large
    # files.

    # Set the name of the output data files
    f_utxos, f_parsed_txs, f_parsed_utxos, f_dust = set_out_names(count_p2sh, non_std_only)

    # Parse all the data in the chainstate.
    print "Parsing the chainstate."
    parse_ldb(f_utxos, fin_name=chainstate)

    # Parses transactions and utxos from the dumped data.
    print "Adding meta-data for transactions and UTXOs."
    transaction_dump(f_utxos, f_parsed_txs)
    utxo_dump(f_utxos, f_parsed_utxos, coin, count_p2sh=count_p2sh, non_std_only=non_std_only)

    # Print basic stats from data
    print "Running overview analysis."
    overview_from_file(f_parsed_txs, f_parsed_utxos)

    # Generate plots from tx data (from f_parsed_txs)
    print "Running transaction based analysis."
    tx_based_analysis(f_parsed_txs)

    # Generate plots from utxo data (from f_parsed_utxos)
    print "Running UTXO based analysis."
    utxo_based_analysis(f_parsed_utxos)

    # # Aggregates dust and generates plots.
    print "Running dust analysis."
    dust_analysis(f_parsed_utxos, f_dust)
    dust_analysis_all_fees(f_parsed_utxos)

    # Generate plots with filters
    print "Running analysis with filters."
    utxo_based_analysis_with_filters(f_parsed_utxos)
    tx_based_analysis_with_filters(f_parsed_txs)


if __name__ == '__main__':

    # Default params
    non_std_only = False
    count_p2sh = True
    coin = CFG.default_coin

    opts, _ = getopt(argv[1:], 'c:pn', ['coin=', 'count_p2sh', 'non_std'])

    for opt, arg in opts:
        if opt in ['c', '--coin']:
            coin = arg
        elif opt in ['-p', '--count_p2sh']:
            count_p2sh = True
        elif opt in ['n', '--non_std_only']:
            non_std_only = True

    # When not using a snapshot, we directly use the chainstate under btc_core_dir (actually that's its default value)
    chainstate = CFG.chainstate_path

    # When using snapshots of the chainstate, specify the path to the chainstate snapshot
    # chainstate = path_to_snapshot

    run_experiment(coin, chainstate, count_p2sh, non_std_only)
