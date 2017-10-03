from bitcoin_tools.core.keys import serialize_pk, load_keys
from bitcoin_tools.core.transaction import TX

# BUILD TRANSACTIONS

prev_tx_ids = ["f0315ffc38709d70ad5647e22048358dd3745f3ce3874223c80a7c92fab0c8ba",  # P2PK
               "7767a9eb2c8adda3ffce86c06689007a903b6f7e78dbc049ef0dbaf9eeebe075",  # P2PKH
               "adcd6d269d5e0713fa9650099e9ab54ebf845a0d95f3740b44361bdb287959a7"]  # P2MS
prev_out_index = [0, 0, 0]
btc_addrs = ["mgwpBW3g4diqasfxzWDgSi5fBrsFKmNdva", "mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy",
             "n4kDrXT6BuvgjjitGxLr4wepmeATWwvBJy"]
value = [1000, 2000, 3000]
pks = []
sks = []

# Just for testing
fee_multiplier = 240
fee = 235 * fee_multiplier
value = 6083510 - fee

for addr in btc_addrs:
    sk, pk = load_keys(addr)
    sks.append(sk)
    pks.append(pk)


for i in range(3):
    if i is 0:
        print "\n#############\n# FROM P2PK #\n#############"
        sk = sks[i]
    elif i is 1:
        print "##############\n# FROM P2PKH #\n##############"
        sk = sks[i]
    elif i is 2:
        print "#############\n# FROM P2MS #\n#############"
        sk = sks[:i]
    for j in range(3):
        if j is 0:
            print "\nTO: P2PK\n"
            dest = serialize_pk(pks[j])
        elif j is 1:
            print "\nTO: P2PKH\n"
            dest = btc_addrs[j]
        elif j is 2:
            print "\nTO: P2MS\n"
            dest = [2, serialize_pk(pks[0]), serialize_pk(pks[1])]

        tx = TX.build_from_io(prev_tx_ids[i], prev_out_index[i], value, dest)
        tx.sign(sk, 0)
        print tx.serialize()
        tx.display()

    print "\n---------------------------------------------------------------------------------------------\n"
