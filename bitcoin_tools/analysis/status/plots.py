from bitcoin_tools import CFG
from bitcoin_tools.analysis.plots import plot_distribution, get_cdf, plot_pie
from json import loads

from collections import Counter
import numpy as np


def plots_from_file(x_attribute, y=["tx"], xlabel=False, log_axis=False, version=[0.15], save_fig=False, legend=None,
                    legend_loc=1, font_size=20, filtr=[lambda x: True]):
    """
    Generates plots from utxo/tx data extracted from utxo_dump.

    :param x_attribute: Attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str or list
    :param y: Either "tx" or "utxo"
    :type y: str or list
    :param xlabel: Label on the x axis
    :type xlabel: str
    :param log_axis: Determines which axis are plotted using (accepted values are False, "x", "y" or "xy").
    logarithmic scale
    :type log_axis: str
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float or list
    :param save_fig: Figure's filename or False (to show the interactive plot)
    :type save_fig: str
    :param legend: List of strings with legend entries or None (if no legend is needed)
    :type legend: str list
    :param legend_loc: Indicates the location of the legend (if present)
    :type legend_loc: int
    :param font_size: Title, xlabel and ylabel font size
    :type font_size: int
    :param filtr: Function to filter samples (returns a boolean value for a given sample)
    :type filtr: function or list of functions
    :return: None
    :rtype: None
    """

    if not (isinstance(x_attribute, list) or isinstance(x_attribute, np.ndarray)):
        x_attribute = [x_attribute]

    if not (isinstance(y, list) or isinstance(y, np.ndarray)):
        y = [y]

    if not (isinstance(version, list) or isinstance(version, np.ndarray)):
        version = [version]

    if not (isinstance(filtr, list) or isinstance(filtr, np.ndarray)):
        filtr = [filtr]

    assert len(x_attribute) == len(y) == len(version) == len(filtr), \
        "There is a mismatch on the list length of some of the parameters"

    if y[0] == "tx":
        ylabel = "Number of tx."
    elif y[0] == "utxo":
        ylabel = "Number of UTXOs"

    title = ""
    if not xlabel:
        xlabel = x_attribute

    xs, ys = [], []
    for i in range(len(x_attribute)):
        samples = get_samples(x_attribute[i], y=y[i], version=version[i], filtr=filtr[i])
        [xc, yc] = get_cdf(samples, normalize=True)
        xs.append(xc)
        ys.append(yc)

    # Adds the folder in which the data will be stored (if multiple versions are involved, store it
    # in the first one folder)
    save_fig = str(version[0]) + '/' + save_fig

    plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)
    
    
def plot_from_file_dict(x_attribute, y="dust", fin_name=None, percentage=False, xlabel=False,
                        log_axis=False, version=0.15, save_fig=False, legend=None, legend_loc=1, font_size=20):
    """
    Generate plots from files in which the loaded data is a dictionary, such as dust.json.

    :param x_attribute: Attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str
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

    # Decides the type of chart to be plot.
    if y == "dust":
        data_type = ["dust_utxos", "lm_utxos"]
        if not percentage:
            ylabel = "Number of utxos"
        else:
            ylabel = "Percentage of utxos"
            total = "total_utxos"
    elif y == "value":
        data_type = ["dust_value", "lm_value"]
        if not percentage:
            ylabel = "Value (Satoshi)"
        else:
            ylabel = "Percentage of total value"
            total = "total_value"
    elif y == "data_len":
        data_type = ["dust_data_len", "lm_data_len"]
        if not percentage:
            ylabel = "Utxos' size (bytes)"
        else:
            ylabel = "Percentage of total utxos' size"
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
        xlabel = x_attribute

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


def plot_pie_chart_from_file(x_attribute, y="tx", title="", labels=[], groups=[], colors=[], version=0.15,
                             save_fig=False, font_size=20):
    """
    Generates pie charts from UTXO/tx data extracted from utxo_dump.

    :param x_attribute: Attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str
    :param title: Title of the chart.
    :type title: str
    :param y: Either "tx" or "utxo"
    :type y: str
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

    if y == "tx":
        fin = open(CFG.data_path + str(version) + '/' + 'parsed_txs.json', 'r')
    elif y == "utxo":
        fin = open(CFG.data_path + str(version) + '/' + 'parsed_utxos.json', 'r')
    else:
        raise ValueError('Unrecognized y value')

    samples = []
    for line in fin:
        data = loads(line[:-1])
        samples.append(data[x_attribute])

    fin.close()

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
        values.append(len(samples)-current_sum)

    plot_pie(values, labels, title, colors, save_fig=save_fig, font_size=font_size)


def overview_from_file(version=0.15):
    """
    Prints a summary of basic stats.

    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float
    :return: None
    :rtype: None
    """

    samples = get_samples("num_utxos", y="tx", version=version)

    print "Num. of tx: ", str(len(samples))
    print "Num. of UTXOs: ", str(sum(samples))
    print "Avg. num. of UTXOs per tx: ", str(np.mean(samples))
    print "Std. num. of UTXOs per tx: ", str(np.std(samples))
    print "Median num. of UTXOs per tx: ", str(np.median(samples))

    samples = get_samples("total_len", y="tx", version=version)

    print "Size of the (serialized) UTXO set: ", str(np.sum(samples))
    print "Avg. size per tx: ", str(np.mean(samples))
    print "Std. size per tx: ", str(np.std(samples))
    print "Median size per tx: ", str(np.median(samples))

    samples = get_samples("utxo_data_len", y="utxo", version=version)

    print "Avg. size per utxo: ", str(np.mean(samples))
    print "Std. size per utxo: ", str(np.std(samples))
    print "Median size per utxo: ", str(np.median(samples))


def get_samples(x_attribute, y="tx", version=0.15, filtr=lambda x: True):
    """
    Reads data from .json files and creates a list with the attribute of interest values.

    :param x_attribute: Attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str
    :param y: Either "tx" or "utxo"
    :type y: str
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float
    :param filtr: Function to filter samples (returns a boolean value for a given sample)
    :type filtr: function
    :return:
    """

    if y == "tx":
        fin = open(CFG.data_path + str(version) + '/' + 'parsed_txs.json', 'r')
    elif y == "utxo":
        fin = open(CFG.data_path + str(version) + '/' + 'parsed_utxos.json', 'r')
    else:
        raise ValueError('Unrecognized y value')

    samples = []
    for line in fin:
        data = loads(line[:-1])
        if filtr(data):
            samples.append(data[x_attribute])

    fin.close()

    return samples
    

def get_unique_values(x_attribute, y="tx", version=0.15):
    """
    Reads data from a .json file and returns all values found in x_attribute.

    :param x_attribute: Attribute to analyse.
    :type x_attribute: str
    :param y: Either "tx" or "utxo"
    :type y: str
    :param version: Bitcoin core version, used to decide the folder in which to store the data.
    :type version: float
    :return: list of unique x_attribute values
    """

    samples = get_samples(x_attribute, y=y, version=version)

    return list(set(samples))
