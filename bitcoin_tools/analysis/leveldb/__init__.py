# Fee per byte range
MIN_FEE_PER_BYTE = 30
MAX_FEE_PER_BYTE = 350
FEE_STEP = 10

NSPECIALSCRIPTS = 6

try:
    import bitcoin_tools.conf as CFG
except ImportError:
    raise Exception("You don't have a configuration file. Make a copy of sample_conf.py")

entries = [CFG.btc_core_path, CFG.data_path, CFG.figs_path]

if None in entries:
    raise Exception("Your configuration file lacks some requited data.")
