# Dependencies

The library has the abovementioned dependencies (which can be satisfied by using `pip install -r requirements.txt`):

##### Key management and address creation

`ecdsa 
base58 `

##### Keys export (WIF)
`qrcode
Pillow`

##### Script creation
`python-bitcoinlib`

##### Data analysis
`plyvel
matplotlib
numpy
ujson`

Note that some additional system packages may also be needed. For instance, for Debian/Ubuntu based systems, `python-tk` 
and `libleveldb-dev` must be installed:

`sudo apt-get install python-tk libleveldb-dev`