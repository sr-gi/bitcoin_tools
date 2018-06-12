from bitcoin_tools.analysis.plots import plot_distribution, plot_pie
from collections import Counter
import numpy as np
from bitcoin_tools.analysis.status.data_processing import get_samples


def plots_from_samples(xs, ys, ylabel="Number of txs", xlabel=None, log_axis=None, save_fig=False, legend=None,
                       legend_loc=1, font_size=20):
    """
    Generates plots from utxo/tx samples extracted from utxo_dump.

    :param xs: X-axis samples to be printed (from get_samples)
    :type xs: list
    :param ys: Y-axis samples to be printed (from get_samples)
    :type ys: list
    :param ylabel: Label for the y axis of the chart
    :type ylabel: str or list
    :param xlabel: Label on the x axis
    :type xlabel: str
    :param log_axis: Determines which axis are plotted using (accepted values are False, "x", "y" or "xy").
    logarithmic scale
    :type log_axis: str or list
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

    title = ""

    if isinstance(log_axis, list) and isinstance(save_fig, list):
        # If both the normal axis and the logx axis charts want to be displayed, we can take advantage of the same
        # parsing to speed up the process.
        for lx, sf in zip(log_axis, save_fig):
            plot_distribution(xs, ys, title, xlabel, ylabel, lx, sf, legend, legend_loc, font_size)
    else:
        # Otherwise we just print one chart.
        plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)


def plot_pie_chart_from_samples(samples, title="", labels=None, groups=None, colors=None, save_fig=False, font_size=20,
                                labels_out=False):
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
    :param save_fig: Figure's filename or False (to show the interactive plot)
    :type save_fig: str
    :param font_size: Title, xlabel and ylabel font size
    :type font_size: int
    :param labels_out: Whether the labels are placed inside the pie or not.
    :type labels_out: bool
    :return: None
    :rtype: None
    """

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


def overview_from_file(tx_fin_name, utxo_fin_name):
    """
    Prints a summary of basic stats.

    :param tx_fin_name: Parsed UTXO input file from which data is loaded.
    :type tx_fin_name: str
    :param utxo_fin_name: Parsed transactions input file from which data is loaded.
    :type utxo_fin_name: str
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

    samples = get_samples("register_len", fin_name=utxo_fin_name)
    len_attribute = "register_len"

    print "\t Avg. size per register: ", str(np.mean(samples[len_attribute]))
    print "\t Std. size per register: ", str(np.std(samples[len_attribute]))
    print "\t Median size per register: ", str(np.median(samples[len_attribute]))
