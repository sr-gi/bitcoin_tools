# Fee per byte range
MIN_FEE_PER_BYTE = 0
MAX_FEE_PER_BYTE = 350
FEE_STEP = 1

NSPECIALSCRIPTS = 6

try:
    import bitcoin_tools.conf as CFG
except ImportError:
    raise Exception("You don't have a configuration file. Make a copy of sample_conf.py")

try:
    entries = [CFG.chainstate_path, CFG.data_path, CFG.figs_path, CFG.default_coin]

    # If any attribute is not set, raise exception.
    if None in entries:
        raise Exception("Your configuration file lacks some requited data. Check sample_conf.py")

# If any attribute is not found, also raise exception.
except AttributeError:
    raise Exception("Your configuration file lacks some requited data. Check sample_conf.py")
