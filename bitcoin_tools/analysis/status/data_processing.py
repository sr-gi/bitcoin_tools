from bitcoin_tools.analysis.status import *
import ujson


def get_samples(x_attribute, fin_name):
    """
    Reads data from .json files and creates a list with the attribute of interest values.

    :param x_attribute: Attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str or list
    :param fin_name: Input file from which data is loaded.
    :type fin_name: str
    :return: A dictionary with x_attribute as keys and a list of the requested samples as values.
    :rtype: dict
    """

    fin = open(CFG.data_path + fin_name, 'r')
    samples = dict()

    if not isinstance(x_attribute, list):
        x_attribute = [x_attribute]

    # Create one list per each attribute requested
    for attribute in x_attribute:
        samples[attribute] = []

    for line in fin:
        data = ujson.loads(line[:-1])

        for attribute in samples:
            samples[attribute].append(data[attribute])

    fin.close()

    return samples


def get_filtered_samples(x_attribute, fin_name, filtr):
    """
    Reads data from .json files and creates a list with the attribute of interest values.

    :param x_attribute: A single attribute to plot (must be a key in the dictionary of the dumped data).
    :type x_attribute: str
    :param fin_name: Input file from which data is loaded.
    :type fin_name: str
    :param filtr: Function to filter samples (returns a boolean value for a given sample)
    :type filtr: function or list of functions
    :return: A list of the requested samples filtered using all the given filters.
    :rtype: list
    """

    fin = open(CFG.data_path + fin_name, 'r')

    if not isinstance(filtr, list):
        filtr = [filtr]

    # Defines the empty list of samples
    samples = []

    # For each filter in filters (if there is more than one), creates an empty list inside samples. I this way, a same
    # attribute can be filtered using multiple filters but just reading once from disk.
    if len(filtr) != 1:
        for _ in filtr:
            samples.append([])

    # Read file
    for line in fin:
        data = ujson.loads(line[:-1])

        # For each filter, we filter the data and add the filtered result in the proper list.
        for i, f in enumerate(filtr):
            if filter_sample(data, f):
                # We append the sample to samples Depending on the number of filters (list / list of lists).
                if len(filtr) > 1:
                    samples[i].append(data[x_attribute])
                else:
                    samples.append(data[x_attribute])
    fin.close()

    return samples


def filter_sample(sample, filtr):
    """
    Applies a given filter to a sample, returning the sample if the filter is passed, or None otherwise.

    :param sample: Samples to be filtered.
    :type sample: dict
    :param filtr: Function to filter samples (returns a boolean value for a given sample)
    :type filtr: function
    :return: The filtered sample.
    :rtype: dict or None
    """

    filtered_sample = None
    if filtr(sample):
        filtered_sample = sample

    return filtered_sample


def get_unique_values(x_attribute, fin_name):
    """
    Reads data from a .json file and returns all values found in x_attribute.

    :param x_attribute: Attribute to analyse.
    :type x_attribute: str
    :param fin_name: Input file from which data is loaded.
    :type fin_name: str
    :return: list of unique x_attribute values
    """

    samples = get_samples(x_attribute, fin_name=fin_name)

    return list(set(samples))
