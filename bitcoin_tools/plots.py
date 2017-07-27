import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from json import loads, dumps
from bitcoin_tools.utils import load_conf_file
from bitcoin_tools.utxo_dump import accumulate_dust


label_size = 12
mpl.rcParams['xtick.labelsize'] = label_size
mpl.rcParams['ytick.labelsize'] = label_size
mpl.rcParams['legend.numpoints'] = 1

# Load config file
cfg = load_conf_file()


def get_counts(samples, normalize=False):
    """
    Counts the number of occurrences of each value in samples.

    :param samples: list with the samples
    :param normalize: boolean, indicates if counts have to be normalized
    :return: list of two lists: first list returns x values (unique values in samples), second list returns occurrence
    counts
    """

    xs, ys = np.unique(samples, return_counts=True)

    if normalize:
        total = sum(ys)
        ys = [float(y)/float(total) for y in ys]

    return [xs, ys]


def get_cdf(samples, normalize=False):
    """
    Compute the cumulative count over samples.

    :param samples: list with the samples
    :param normalize: boolean, indicates if counts have to be normalized
    :return: list of two lists: first list returns x values (unique values in samples), second list returns cumulative
    occurrence counts (number of samples with value <= xi).
    """

    [xs, ys] = get_counts(samples, normalize)
    ys = np.cumsum(ys)

    return [xs, ys]


def plot_distribution(xs, ys, title, xlabel, ylabel, log_axis=False, save_fig=False, legend=None, legend_loc=1,
                      font_size=20):
    """
    Plots a set of values (xs, ys) with matplotlib.

    :param xs: either a list with x values or a list of lists, representing different sample sets to be plotted in the
    same figure.
    :param ys: either a list with y values or a list of lists, representing different sample sets to be plotted in the
    same figure.
    :param title: String, plot title
    :param xlabel: String, label on the x axis
    :param ylabel: String, label on the y axis
    :param log_axis: String (accepted values are False, "x", "y" or "xy"), determines which axis are plotted using logarithmic scale
    :param save_fig: String, figure's filename or False (to show the interactive plot)
    :param legend: list of strings with legend entries or None (if no legend is needed)
    :param legend_loc: integer, indicates the location of the legend (if present)
    :param font_size: integer, title, xlabel and ylabel font size
    """

    plt.figure()
    ax = plt.subplot(111)

    # Plot data
    if not isinstance(xs[0], list):
        plt.plot(xs, ys)  # marker='o'
    else:
        for i in range(len(xs)):
            plt.plot(xs[i], ys[i], ' ', linestyle='solid')  # marker='o'

    # Plot title and xy labels
    plt.title(title, {'color': 'k', 'fontsize': font_size})
    plt.ylabel(ylabel, {'color': 'k', 'fontsize': font_size})
    plt.xlabel(xlabel, {'color': 'k', 'fontsize': font_size})

    # Change axis to log scale
    if log_axis == "y":
        plt.yscale('log')
    elif log_axis == "x":
        plt.xscale('log')
    elif log_axis == "xy":
        plt.loglog()

    # Include legend
    if legend:
        lgd = ax.legend(legend, loc=legend_loc)

    # Output result
    if save_fig:
        plt.savefig(cfg.figs_path + '/' + save_fig + '.pdf', format='pdf', dpi=600)
    else:
        plt.show()


def plot_from_file(x_attribute, y="tx", xlabel=False, log_axis=False, save_fig=False, legend=None,
                   legend_loc=1, font_size=20):
    """
    Generates plots from utxo/tx data extracted from utxo-dump.py

    :param x_attribute: string, attribute to plot (must be a key in the dictionary of the dumped data).
    :param y: string, either "tx" or "utxo"
    :param xlabel: String, label on the x axis
    :param log_axis: String (accepted values are False, "x", "y" or "xy"), determines which axis are plotted using
    logarithmic scale
    :param save_fig: String, figure's filename or False (to show the interactive plot)
    :param legend: list of strings with legend entries or None (if no legend is needed)
    :param legend_loc: integer, indicates the location of the legend (if present)
    :param font_size: integer, title, xlabel and ylabel font size
    :return:
    """

    if y == "tx":
        fin = open(cfg.data_path + 'parsed_txs.txt', 'r')
        ylabel = "Number of tx."
    elif y == "utxo":
        fin = open(cfg.data_path + 'parsed_utxo.txt', 'r')
        ylabel = "Number of UTXOs"
    else:
        raise ValueError('Unrecognized y value')

    samples = []
    for line in fin:
        data = loads(line[:-1])
        samples.append(data[x_attribute])

    fin.close()

    [xs, ys] = get_cdf(samples, normalize=True)
    title = ""
    if not xlabel:
        xlabel = x_attribute

    plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)


def plot_accumulate(data, total=False, xlabel=False, ylabel=False, log_axis=False, save_fig=False, legend=None,
                    legend_loc=1, font_size=20):

    xs = sorted(data.keys(), key=int)
    ys = sorted(data.values(), key=int)

    if total:
        ys = sorted({y / float(total) for y in ys})

    title = ""

    plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)


def plot_from_file_dict(x_attribute, y="dust", fin=None, data=None, percentage=None, xlabel=False,
                        log_axis=False, save_fig=False, legend=None, legend_loc=1, font_size=20):

    if fin and not data:
        # Accumulate the dust data from the provided file
        data = accumulate_dust(fin)

        # Backup the accumulated data to avoid recalculating it again if another plot is required.
        out = open(cfg.data_path + "dust.txt", 'w')
        out.write(dumps(data))
        out.close()

        # Recursively call the function with the accumulated data
        plot_from_file_dict(x_attribute, y, None, data, percentage, xlabel, log_axis, save_fig, legend, legend_loc,
                            font_size)
    else:
        # Decides the type of chart to be plot.
        if y == "dust":
            data_type = "dust_utxos"
            if not percentage:
                ylabel = "Number of dust UTXOs"
            else:
                ylabel = "Percentage of dust UTXOs"
                total = "total_utxos"
        elif y == "value":
            data_type = "dust_value"
            if not percentage:
                ylabel = "Total dust (Satoshis)"
            else:
                ylabel = "Percentage of dust value"
                total = "total_value"
        elif y == "data_len":
            data_type = "dust_data_len"
            if not percentage:
                ylabel = "Total size of dust UTXOs (bytes)"
            else:
                ylabel = "Percentage of dust size"
                total = "total_data_len"
        else:
            raise ValueError('Unrecognized y value')

        # Sort the data
        xs = sorted(data[data_type].keys(), key=int)
        ys = sorted(data[data_type].values(), key=int)

        title = ""
        if not xlabel:
            xlabel = x_attribute

        # If percentage is set, a chart with y axis as a percentage (dividing every single y value by the
        # corresponding total value) is created.
        if percentage:
            ys = [i / float(data[total]) * 100 for i in ys]

        # And finally plots the chart.
        plot_distribution(xs, ys, title, xlabel, ylabel, log_axis, save_fig, legend, legend_loc, font_size)

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
plot_from_file_dict("fee_per_byte", "dust", fin="parsed_utxos.txt", save_fig="dust_utxos")

fin = open(cfg.data_path + 'dust.txt', 'r')
data = loads(fin.read())

plot_from_file_dict("fee_per_byte", "dust", data=data, percentage=True, save_fig="perc_dust_utxos")

plot_from_file_dict("fee_per_byte", "value", data=data, percentage=True, save_fig="dust_value")
plot_from_file_dict("fee_per_byte", "value", data=data, save_fig="perc_dust_value")

plot_from_file_dict("fee_per_byte", "data_len", data=data, percentage=True, save_fig="dust_data_len")
plot_from_file_dict("fee_per_byte", "data_len", data=data, save_fig="perc_dust_data_len")
