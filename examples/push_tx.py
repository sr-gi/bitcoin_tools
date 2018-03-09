from bitcoinrpc.authproxy import AuthServiceProxy

#################################################
#  Sending a transation to the network with RPC #
#################################################

# ---------------------------------------------------------------------------------------------------------------------
# The following piece of code serves as an example of how to send a transaction created with any of the pieces of
# code of the other examples to the P2P network. The code assumes you have access to a Bitcoin node with RPC
# enabled. RPC authentication details have to be provided in the proper variables.
#
# Alternatively, you can also push the transaction to the network with a 3rd party service.
#
# Note that this code has an additional dependency: bitcoinrpc
# This dependency is not required by bitcoin_tools, since it is only used in this example, and most users
# will not need to use it.
# ---------------------------------------------------------------------------------------------------------------------


# Set RPC configuration
rpc_user = ""       # set roc user
rpc_password = ""   # set rpc password
rpc_server = ""     # set rpc server
rpc_port = 18332

# Test connection
rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" % (rpc_user, rpc_password, rpc_server, rpc_port))
get_info = rpc_connection.getinfo()
print get_info

# Send transaction
# raw_transaction = ...
# rpc_connection.sendrawtransaction(raw_transaction)
