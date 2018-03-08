import os
import matplotlib as mpl
if not "DISPLAY" in os.environ.keys():
    mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from bitcoin_tools import CFG

label_size = 11
mpl.rcParams['xtick.labelsize'] = label_size
mpl.rcParams['ytick.labelsize'] = label_size
mpl.rcParams['legend.numpoints'] = 1


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


def plot_distribution(xs, ys, title, xlabel, ylabel, log_axis=None, save_fig=False, legend=None, legend_loc=1,
                      font_size=20, y_sup_lim=None):
    """
    Plots a set of values (xs, ys) with matplotlib.

    :param xs: either a list with x values or a list of lists, representing different sample sets to be plotted in the
    same figure.
    :param ys: either a list with y values or a list of lists, representing different sample sets to be plotted in the
    same figure.
    :param title: String, plot title
    :param xlabel: String, label on the x axis
    :param ylabel: String, label on the y axis
    :param log_axis: String (accepted values are False, "x", "y" or "xy"), determines which axis are plotted using
    logarithmic scale
    :param save_fig: String, figure's filename or False (to show the interactive plot)
    :param legend: list of strings with legend entries or None (if no legend is needed)
    :param legend_loc: integer, indicates the location of the legend (if present)
    :param font_size: integer, title, xlabel and ylabel font size
    :param y_sup_lim: float, y axis superior limit (if None or not present, use default matplotlib value)
    :return: None
    :type: None
    """

    plt.figure()
    ax = plt.subplot(111)

    # Plot data
    if not (isinstance(xs[0], list) or isinstance(xs[0], np.ndarray)):
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

    # Force y limit
    if y_sup_lim:
        ymin, ymax = plt.ylim()
        plt.ylim(ymin, y_sup_lim)

    # Output result
    if save_fig:
        plt.savefig(CFG.figs_path + save_fig + '.pdf', format='pdf', dpi=600)
        plt.close()
    else:
        plt.show()


def plot_pie(values, labels, title, colors, save_fig=False, font_size=20, labels_out=False):
    """
    Plots a set of values in a pie chart with matplotlib.

    :param values: list of values to plot.
    :param values: list of numbers
    :param labels: List of labels (one label for each piece of the pie)
    :type labels: str list
    :param title: String, plot title
    :type title: String
    :param colors: List of colors (one color for each piece of the pie)
    :type colors: str lit
    :param save_fig: String, figure's filename or False (to show the interactive plot)
    :param font_size: integer, title, xlabel and ylabel font size
    """

    plt.figure()
    ax = plt.subplot(111)

    if labels_out:
        # Plots percentages and labels as legend (in a separate box)
        ax.pie(values, colors=colors,
                                autopct='%1.1f%%', startangle=90, pctdistance=1.3, wedgeprops={'linewidth': 0})
        s = float(np.sum(values))
        perc = [v/s*100 for v in values]
        plt.legend(loc="best", labels=['%s, %1.1f %%' % (l, s) for l, s in zip(labels, perc)], fontsize="x-small")
    else:
        # Plot percentages in the pie and labels around the pie
        ax.pie(values, labels=labels, colors=colors,
               autopct='%1.1f%%', startangle=90, labeldistance=1.1, wedgeprops={'linewidth': 0})

    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')

    plt.title(title, {'color': 'k', 'fontsize': font_size})

    # Output result
    if save_fig:
        plt.savefig(CFG.figs_path + save_fig + '.pdf', format='pdf', dpi=600)
    else:
        plt.show()
