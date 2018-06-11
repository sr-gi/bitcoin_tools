# Copy this file with your own configuration and save it as conf.py
# Hints are for Linux systems. The default home_dir for OS X is /Users/your_user_name and the default bitcoin_core_path
# is home_dir + /Library/Application Support/Bitcoin/

# General parameters
home_dir = None  # Home dir (e.g: "/home/your_user_name/").
bitcoin_tools_dir = home_dir + 'bitcoin_tools/'  # Bitcoin_tools data dir.
address_vault = bitcoin_tools_dir + "bitcoin_addresses/"  # Address vault .

#  STATUS parameters
default_coin = 'bitcoin'
chainstate_path = home_dir + ".bitcoin/chainstate"  # Path to the chainstate.
data_path = bitcoin_tools_dir + "data/"  # Data storage path (for IO).
figs_path = bitcoin_tools_dir + "figs/"  # Figure store dir, where images from analysis will be stored.
estimated_data_dir = bitcoin_tools_dir + 'estimation_data/'  # Data for non-profitability with estimations
