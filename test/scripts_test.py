from script.script import OutputScript, InputScript, Script
from wallet.wallet import hash_160
from binascii import b2a_hex

pk = "04a01f076082a713a82b47ace012934052bcf3359c964f1963d00def84a34e7b0345efeefe037f4b0a4e160cc40a7fac052523da88398630c07ef3c54b47aa6046"
signature = "3045022100df7b7e5cda14ddf91290e02ea10786e03eb11ee36ec02dd862fe9a326bbcb7fd02203f5b4496b667e6e281cc654a2da9e4f08660c620a1051337fa8965f727eb191901"
btc_addr = "mgwpBW3g4diqasfxzWDgSi5fBrsFKmNdva"
script = "OP_0 <" + signature + "> OP_1 <" + pk + "> <" + pk + "> OP_2 OP_CHECKMULTISIG"
script_hash = b2a_hex(hash_160(Script.serialize(script)))

sigs = [signature]
pks = [pk, pk]


print ("OUTPUT SCRIPTS")

o = OutputScript()
o.P2PK(pk)
print o.type, o.content

o.P2PKH(btc_addr)
print o.type, o.content

o.P2MS(1, 2, pks)
print o.type, o.content

o.P2SH(script_hash)
print o.type, o.content

print ("\nINPUT SCRIPTS")

i = InputScript()
i.P2PK(signature)
print i.type, i.content

i.P2PKH(signature, pk)
print i.type, i.content

i.P2MS(sigs)
print i.type, i.content

i.P2SH(script)
print i.type, i.content
