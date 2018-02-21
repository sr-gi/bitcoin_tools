from bitcoin_tools import CFG
from bitcoin_tools.analysis.plots import plot_distribution, get_cdf, plot_pie
from json import loads
from collections import Counter
import numpy as np
from bitcoin_tools.analysis.status.utils import get_samples


def plots_from_samples(samples, x_attribute, ylabel="Number of txs", xlabel=None, log_axis=None, version=0.15,
                       comparative=False, save_fig=False, legend=None, legend_loc=1, font_size=20):
    """
    Generates plots from utxo/tx samples extracted from utxo_dump.

    :param samples: Samples to be printed (from get_samples)
    :type: list
    :param x_attribute: Attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str or list
    :param ylabel: Label for the y axis of the chart
    :type ylabel: str or list
    :param xlabel: Label on the x axis
    :type xlabel: str
    :param log_axis: Determines which axis are plotted using (accepted values are False, "x", "y" or "xy").
    logarithmic scale
    :type log_axis: str or list
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: str or list
    :param comparative: Whether we are running a comparative analysis.
    :type comparative: bool
    :param save_fig: Figure's filename or False (to show the interactive plot)
    :type save_fig: str or list
    :param legend: List of strings with legend entries or None (if no legend is needed)
    :type legend: str list
    :param legend_loc: Indicates the location of the legend (if present)
    :type legend_loc: int
    :param font_size: Title, xlabel and ylabel font size
    :type font_size: int
    :return: None
    :rtype: None
    """

    if not (isinstance(x_attribute, list) or isinstance(x_attribute, np.ndarray)):
        x_attribute = [x_attribute]

    # In comparative analysis samples are passed as list of lists of samples.
    if not comparative:
        samples = [samples]

    title = ""
    if not xlabel:
        xlabel = x_attribute

    xs, ys = [], []
    for i in range(len(x_attribute)):
        for s in samples:
            [xc, yc] = get_cdf(s, normalize=True)
            xs.append(xc)
            ys.append(yc)

    if isinstance(log_axis, list) and isinstance(save_fig, list):
        # If both the normal axis and the logx axis charts want to be displayed, we can take advantage of the same
        # parsing to speed up the process.
        for lx, sf in zip(log_axis, save_fig):
            sf = str(version) + '/' + sf
            plot_distribution(xs, ys, title, xlabel, ylabel, lx, sf, legend, legend_loc, font_size)
    else:
        # Otherwise we just print one chart.
        save_fig = str(version) + '/' + save_fig
        plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)


def plot_pie_chart_from_samples(samples, title="", labels=None, groups=None, colors=None, version=0.15, save_fig=False,
                                font_size=20, labels_out=False):
    """
    Generates pie charts from UTXO/tx data extracted from utxo_dump.

    :param samples: Samples to be printed (from get_samples)
    :type: list
    :param title: Title of the chart.
    :type title: str
    :param labels: List of labels (one label for each piece of the pie)
    :type labels: str list
    :param groups: List of group keys (one list for each piece of the pie).
    :type groups: list of lists
    :param colors: List of colors (one color for each piece of the pie)
    :type colors: str lit
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float
    :param save_fig: Figure's filename or False (to show the interactive plot)
    :type save_fig: str
    :param font_size: Title, xlabel and ylabel font size
    :type font_size: int
    :return: None
    :rtype: None
    """

    # Adds the folder in which the data will be stored
    save_fig = str(version) + '/' + save_fig

    # Count occurrences
    ctr = Counter(samples)

    # Sum occurrences that belong to the same pie group
    values = []
    for group in groups:
        group_value = 0
        for v in group:
            if v in ctr.keys():
                group_value += ctr[v]
        values.append(group_value)

    # Should we have an "others" section?
    if len(labels) == len(groups) + 1:
        # We assume the last group is "others"
        current_sum = sum(values)
        values.append(len(samples) - current_sum)

    plot_pie(values, labels, title, colors, save_fig=save_fig, font_size=font_size, labels_out=labels_out)


def plot_dict_from_file(y="dust", fin_name=None, percentage=False, xlabel=None, log_axis=None,
                        version=0.15, save_fig=False, legend=None, legend_loc=1, font_size=20):
    """
    Loads data from a given file (stored in a dictionary) and plots it in a chart. dust.json is a perfect example of
    the loaded format.

    :param y: Either "tx" or "utxo"
    :type y: str
    :param fin_name: Name of the file containing the data to be plotted.
    :type fin_name: str
    :param percentage: Whether the data is plot as percentage or not.
    :type percentage: bool
    :param xlabel: Label on the x axis
    :type xlabel: str
    :param log_axis: Determines which axis are plotted using (accepted values are False, "x", "y" or "xy").
    logarithmic scale
    :type log_axis: str
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float
    :param save_fig: Figure's filename or False (to show the interactive plot)
    :type save_fig: str
    :param legend: List of strings with legend entries or None (if no legend is needed)
    :type legend: str list
    :param legend_loc: Indicates the location of the legend (if present)
    :type legend_loc: int
    :param font_size: Title, xlabel and ylabel font size
    :type font_size: int
    :return: None
    :rtype: None
    """

    fin = open(CFG.data_path + fin_name, 'r')
    data = loads(fin.read())
    fin.close()

    # Decides the type of chart to be plot.
    if y == "dust":
        data_type = ["dust_utxos", "np_utxos"]
        if not percentage:
            ylabel = "Number of UTXOs"
        else:
            ylabel = "Percentage of UTXOs"
            total = "total_utxos"
    elif y == "value":
        data_type = ["dust_value", "np_value"]
        if not percentage:
            ylabel = "Value (Satoshi)"
        else:
            ylabel = "Percentage of total value"
            total = "total_value"
    elif y == "data_len":
        data_type = ["dust_data_len", "np_data_len"]
        if not percentage:
            ylabel = "UTXOs' size (bytes)"
        else:
            ylabel = "Percentage of total UTXOs' size"
            total = "total_data_len"
    else:
        raise ValueError('Unrecognized y value')

    # Adds the folder in which the data will be stored
    save_fig = str(version) + '/' + save_fig

    xs = []
    ys = []
    # Sort the data
    for i in data_type:
        xs.append(sorted(data[i].keys(), key=int))
        ys.append(sorted(data[i].values(), key=int))

    title = ""
    if not xlabel:
        xlabel = "fee_per_byte"

    # If percentage is set, a chart with y axis as a percentage (dividing every single y value by the
    # corresponding total value) is created.
    if percentage:
        for i in range(len(ys)):
            if isinstance(ys[i], list):
                ys[i] = [j / float(data[total]) * 100 for j in ys[i]]
            elif isinstance(ys[i], int):
                ys[i] = ys[i] / float(data[total]) * 100

    # And finally plots the chart.
    plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)


def overview_from_file(tx_fin_name, utxo_fin_name, version=0.15):
    """
    Prints a summary of basic stats.

    :param tx_fin_name: Parsed UTXO input file from which data is loaded.
    :type tx_fin_name: str
    :param utxo_fin_name: Parsed transactions input file from which data is loaded.
    :type utxo_fin_name: str
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float
    :return: None
    :rtype: None
    """

    samples = get_samples(['num_utxos', 'total_len', 'height'], fin_name=tx_fin_name)

    print "\t Max height: ", str(max(samples['height']))
    print "\t Num. of tx: ", str(len(samples['num_utxos']))
    print "\t Num. of UTXOs: ", str(sum(samples['num_utxos']))
    print "\t Avg. num. of UTXOs per tx: ", str(np.mean(samples['num_utxos']))
    print "\t Std. num. of UTXOs per tx: ", str(np.std(samples['num_utxos']))
    print "\t Median num. of UTXOs per tx: ", str(np.median(samples['num_utxos']))

    len_attribute = "total_len"

    print "\t Size of the (serialized) UTXO set: ", str(np.sum(samples[len_attribute]))

    if version >= 0.15:
        samples = get_samples("register_len", fin_name=utxo_fin_name)
        len_attribute = "register_len"

    print "\t Avg. size per register: ", str(np.mean(samples[len_attribute]))
    print "\t Std. size per register: ", str(np.std(samples[len_attribute]))
    print "\t Median size per register: ", str(np.median(samples[len_attribute]))
