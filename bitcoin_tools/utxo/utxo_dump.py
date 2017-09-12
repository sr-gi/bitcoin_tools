from bitcoin_tools.utils import load_conf_file, decode_utxo, change_endianness
from json import loads, dumps
from math import ceil
from copy import deepcopy

# Load config file
cfg = load_conf_file()

# Fee per byte range
MIN_FEE_PER_BYTE = 30
MAX_FEE_PER_BYTE = 350
FEE_STEP = 10


def check_multisig(script):
    if int(script[:2], 16) in range(81, 96) and script[2:4] in ["21", "41"] and script[-2:] == "ae":
        return True
    else:
        return False


def get_min_input_size(out, height, count_p2sh=False):
    out_type = out["out_type"]
    script = out["data"]

    # Fixed size
    prev_tx_id = 32
    prev_out_index = 4
    nSequence = 4

    fixed_size = prev_tx_id + prev_out_index + nSequence

    # Variable size (depending on scripSig):
    # Public key size can be either 33 or 65 bytes, depending on whether the key is compressed or uncompressed. We wil
    # make them fall in one of the categories depending on the block height in which the transaction was included.
    #
    # Signatures size is contained between 71-73 bytes depending on the size of the S and R components of the signature.
    # Since we are looking for the minimum size, we will consider all signatures to be 71-byte long in order to define
    # a lower bound.

    if out_type is 0:
        # P2PKH
        # Bitcoin core starts using compressed pk in version (0.6.0, 30/03/12, around block height 173480)
        if height < 173480:
            # uncompressed keys
            scriptSig = 138  # PUSH sig (1 byte) + sig (71 bytes) + PUSH pk (1 byte) + uncompressed pk (65 bytes)
        else:
            # compressed keys
            scriptSig = 106  # PUSH sig (1 byte) + sig (71 bytes) + PUSH pk (1 byte) + compressed pk (33 bytes)
        scriptSig_len = 1
    elif out_type is 1:
        # P2SH
        # P2SH inputs can have arbitrary length. Defining the length of the original script by just knowing the hash
        # is infeasible. Two approaches can be followed in this case. The first one consists on considering P2SH
        # by defining the minimum length a script of such type could have. The other approach will be ignoring such
        # scripts when performing the dust calculation.
        if count_p2sh:
            # If P2SH UTXOs are considered, the minimum script that can be created has only 1 byte (OP_1 for example)
            scriptSig = 1
            scriptSig_len = 1
        else:
            # Otherwise, we will define the length as 0 and skip such scripts for dust calculation.
            scriptSig = -fixed_size
            scriptSig_len = 0
    elif out_type in [2, 3, 4, 5]:
        # P2PK
        # P2PK requires a signature and a push OP_CODE to push the signature into the stack. The format of the public
        # key (compressed or uncompressed) does not affect the length of the signature.
        scriptSig = 72  # PUSH sig (1 byte) + sig (71 bytes)
        scriptSig_len = 1
    else:
        # P2MS
        if check_multisig(script):
            # Multisig can be 15-15 at most.
            req_sigs = int(script[:2], 16) - 80  # OP_1 is hex 81
            scriptSig = 1 + (req_sigs * 72)  # OP_0 (1 byte) + 72 bytes per sig (PUSH sig (1 byte) + sig (71 bytes))
            scriptSig_len = int(ceil(scriptSig / float(256)))
        else:
            # All other types (non-standard outs)
            scriptSig = -fixed_size - 1  # Those scripts are marked with length -1 and skipped in dust calculation.
            scriptSig_len = 0

    var_size = scriptSig_len + scriptSig

    return fixed_size + var_size


def transaction_dump(fin_name, fout_name):
    # Transaction dump

    # Input file
    fin = open(cfg.data_path + fin_name, 'r')
    # Output file
    fout = open(cfg.data_path + fout_name, 'w')

    for line in fin:
        data = loads(line[:-1])
        utxo = decode_utxo(data["value"])

        imprt = sum([out["amount"] for out in utxo.get("outs")])

        result = {"tx_id": change_endianness(data["key"][2:]),
                  "num_utxos": len(utxo.get("outs")),
                  "total_value": imprt,
                  "total_len": (len(data["key"]) + len(data["value"])) / 2,
                  "height": utxo["height"],
                  "coinbase": utxo["coinbase"],
                  "version": utxo["version"]}

        fout.write(dumps(result) + '\n')

    fout.close()


def utxo_dump(fin_name, fout_name, count_p2sh=False, non_std_only=False):
    # UTXO dump

    # Input file
    fin = open(cfg.data_path + fin_name, 'r')
    # Output file
    fout = open(cfg.data_path + fout_name, 'w')

    # Standard UTXO types
    std_types = [0, 1, 2, 3, 4, 5]

    for line in fin:
        data = loads(line[:-1])
        utxo = decode_utxo(data["value"])

        for out in utxo.get("outs"):
            # Checks whether we are looking for every type of UTXO or just for non-standard ones.
            if not non_std_only or (non_std_only and out["out_type"] not in std_types):
                # Calculates the dust threshold for every UTXO value and every fee per byte ratio between min and max.
                min_size = get_min_input_size(out, utxo["height"], count_p2sh)
                # Initialize dust, lm and the fee_per_byte ratio.
                dust = 0
                lm = 0
                fee_per_byte = MIN_FEE_PER_BYTE
                # Check whether the utxo is dust/lm for the fee_per_byte range.
                while MAX_FEE_PER_BYTE > fee_per_byte and lm == 0:
                    # Set the dust and loss_making thresholds.
                    if dust is 0 and min_size * fee_per_byte > out["amount"] / 3:
                        dust = fee_per_byte
                    if lm is 0 and out["amount"] < min_size * fee_per_byte:
                        lm = fee_per_byte

                    # Increase the ratio
                    fee_per_byte += FEE_STEP

                # Builds the output dictionary
                result = {"tx_id": change_endianness(data["key"][2:]),
                          "tx_height": utxo["height"],
                          "utxo_data_len": len(out["data"]) / 2,
                          "dust": dust,
                          "loss_making": lm}

                # Updates the dictionary with the remaining data from out, and stores it in disk.
                result.update(out)
                fout.write(dumps(result) + '\n')

    fout.close()


def accumulate_dust(fin_name):
    # Dust calculation
    # Input file
    fin = open(cfg.data_path + fin_name, 'r')

    dust = {str(fee_per_byte): 0 for fee_per_byte in range(MIN_FEE_PER_BYTE, MAX_FEE_PER_BYTE, FEE_STEP)}
    value_dust = deepcopy(dust)
    data_len_dust = deepcopy(dust)

    lm = deepcopy(dust)
    value_lm = deepcopy(dust)
    data_len_lm = deepcopy(dust)

    total_utxo = 0
    total_value = 0
    total_data_len = 0

    for line in fin:
        data = loads(line[:-1])

        for fee_per_byte in range(MIN_FEE_PER_BYTE, MAX_FEE_PER_BYTE, FEE_STEP):
            if fee_per_byte >= data["dust"] != 0:
                dust[str(fee_per_byte)] += 1
                value_dust[str(fee_per_byte)] += data["amount"]
                data_len_dust[str(fee_per_byte)] += data["utxo_data_len"]
            if fee_per_byte >= data["loss_making"] != 0:
                lm[str(fee_per_byte)] += 1
                value_lm[str(fee_per_byte)] += data["amount"]
                data_len_lm[str(fee_per_byte)] += data["utxo_data_len"]

        total_utxo = total_utxo + 1
        total_value += data["amount"]
        total_data_len += data["utxo_data_len"]

    fin.close()

    return {"dust_utxos": dust, "dust_value": value_dust, "dust_data_len": data_len_dust,
            "lm_utxos": lm, "lm_value": value_lm, "lm_data_len": data_len_lm,
            "total_utxos": total_utxo, "total_value": total_value, "total_data_len": total_data_len}
