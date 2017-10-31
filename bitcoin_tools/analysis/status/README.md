## STATUS

**STATUS** (**ST**atistical **A**nalysis **T**ool for **U**txo **S**et) is an open source tool that provides an easy way to access, decode and analyze data from the Bitcoin's `utxo set`.

STATUS is coded in Python 2 and works for both the existing versions of Bitcoin Core's `utxo set`, that is, for the first defined format (versions 0.8 - 0.14) and for the recently defined one (version 0.15). 

STATUS reads from a LevelDB folder (usually located under `.bitcoin/chainstate`) and parse all the `utxo` entries into a `json` file. From the parsed file, STATUS allows you to perform two type of analysis, a `utxo` based one, and a `transaction` based one, by decoding all the information encoded in the `key:value` file (the exact decoding depends on the database version).

## UTXO based analysis

### Directly decoded data

This analysis provides, for every parsed `utxo`, the decoding of the data stored, that is: `transaction id` and `index` that uniquely identifies the `utxo`, the `value` of the output in Satoshi, the `block height` in which the transaction was included, whether the output is `coinbase` or not, the `scriptPubKey` that locks the output and the `script type`, and depending on the database version, the `transaction version`.

### Additional metadata

In addition, this analysis also provides, for every single entry, the `script length`, the fee rate at which the `utxo` becomes `dust`, and the fee rate at which the `utxo` becomes `non-profitable`.

### Non-standard UTXOs

STATUS allows you to run analysis against non-standard `utxos` only by running the analysis with `non_std_only` flag set.

## Transaction based analysis

Transaction based analysis aggregates data from different `utxo` that were created by the same `transaction`, providing information the following information about it:

The `number of unspent outputs`, the `total value` and the `total length` of those outputs as represented in the `utxo set`, the `block height` in which the transaction was created, whether the transaction is `coinbase` and, depending in the database version, the `transaction version`.

## Statistical analysis

With the raw generated data, and using `numpy` and `matplotlib` Python's libraries, STATUS allows you to run several statistical analyses, such as general data overview (containing the total number of `transactions` and `utxos`, and the average, median, and standard deviation of `utxo` per transaction, size per transactions, and size per `utxos`), and different plots for all the parsed data, including the `dust` and `non-profitable utxos`. 
