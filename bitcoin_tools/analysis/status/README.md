# STATUS

**STATUS** (**ST**atistical **A**nalysis **T**ool for **U**txo **S**et) is an open source tool that provides an easy way to access, decode and analyze data from the Bitcoin's `utxo set`. The accompanying working paper further explains its design, application, and presents results of a recently performed analysis: [https://eprint.iacr.org/2017/1095.pdf](https://eprint.iacr.org/2017/1095.pdf)


STATUS is coded in Python 2 and works for both the existing versions of Bitcoin Core's `utxo set`, that is, the first defined format (versions 0.8 - 0.14) and the recently defined one (version 0.15).

STATUS works, from now on, with 0.15 format. For 0.8-0.14 version refer to `ldb_0.14` branch.

STATUS reads from a LevelDB folder (usually located under `.bitcoin/chainstate`) and parses all the `utxo` entries into a `json` file. From the parsed file, STATUS allows you to perform two type of analysis, a `utxo` based one, and a `transaction` based one, by decoding all the parsed information from the chainstate.

## UTXO based analysis

### Directly decoded data

This analysis provides, for every parsed `utxo`, the decoding of the stored data, that is: `transaction id` and `index` that uniquely identifies the `utxo`, the `value` of the output in Satoshi, the `block height` in which the transaction was included, whether the output is `coinbase` or not, the `scriptPubKey` that locks the output, the `script type`, and depending on the database version, the `transaction version`.

### Additional metadata

In addition, this analysis also provides, for every single entry, the `script length`, the fee rate at which the `utxo` becomes `dust`, and the fee rate at which the `utxo` becomes `non-profitable`.

### Non-standard UTXOs

STATUS allows you to run analysis against non-standard `utxos` only by running the analysis with `non_std_only` flag set.

## Transaction based analysis

Transaction based analysis aggregates data from different `utxo` that were created by the same `transaction`, providing the following information about it:

The `number of unspent outputs`, the `total value` and the `total length` of those outputs as represented in the `utxo set`, the `block height` in which the transaction was created, whether the transaction is `coinbase` or not and again, the `transaction version` (depending on the database version).

## Statistical analysis

With th generated raw data, and using `numpy` and `matplotlib` Python's libraries, STATUS allows you to run several statistical analyses, such as general data overview (containing the total number of `transactions` and `utxos`, and the average, median, and standard deviation of `utxo` per transaction, size per transactions, and size per `utxos`), and different plots for all the parsed data, including the `dust` and `non-profitable utxos`. 
