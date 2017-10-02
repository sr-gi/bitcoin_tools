try:
    import bitcoin_tools.conf as CFG
except ImportError:
    raise Exception("You don't have a configuration file. Make a copy of sample_conf.py")

if CFG.address_vault is None:
    raise Exception("Address vault not found in your config file.")
