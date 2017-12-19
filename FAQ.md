# Frequently Asked Questions (and Answers!)

### I just downloaded the code from GitHub, how can I make it work?

First, you must install all the dependencies, both system and Python ones. Refer to the [dependencies section](DEPENDENCIES.md) to check them.

### I've installed all the dependencies, but the code still doesn't work! What I'm doing wrong?

Have you checked the [INSTALL.md](INSTALL.md) file? You may need to add bitcoin_tools as a library by placing it in the proper directory or including it in the `PYTHONPATH`

### I've installed all the dependencies and I've done everything in the INSTALL.md file, why I am still not able to make it work?!

Once all dependencies are installed you should create a configuration file using `sample_conf.py` as an example. The purpose
of the configuration file is to define the paths of the directories that will be used for IO by the library, for example
where the public and private keys will be stored once a new pair are created, where the `chainstate` directory is located
when performing an `utxo set` analysis using `STATUS`, where the data files of the analysis or the charts will be stored,
etc. `sample_conf.py` contains come hints of what the folders should be for each case, but it will change depending on your OS.

### Is there any OS required to use the library?

Not really, it has been tested both in `OSX` and `Linux` (specially `arch`, `debian` and `ubuntu`). However, `leveldb` does
not work properly with `Windows` systems (at lest it doesn't at the time of writing this, Hi people from the future!), so if
you are planning to use `STATUS`, better avoid `Windows`. (If someone can make it work on it, PR are more than welcome!)


### I'm trying to use some code I found in the examples / Issues and it's not working. Why you do this to me?!

Have you checked that you are in the proper `git` branch? Sometimes the functionality or even the calls can change between
different branches. Some parts of the code could have been moved or renamed. Run `git branch` and `git checkout branch_name`
if you are not in the one you are supposed to be!

### I want to use your library to create some fancy app for \*\*insert the purpose here\*\*, can you do it for me?

Nope! I'm more than happy to help you with any kind of trouble you face when using the library, as well as to fix any
bug you may find. However, don't ask me to develop your application for you!

### Do I need a PhD to use the library?

Not really, the library is quite exhaustively commented to ease the process of using it, however, some knowledge of `Python`,
`Bitcoin` and `git` is required.

### I really like your library, is there anything I can do to thank you?

You can star the GitHub code.

### But I really really like it!

Well, I like beer, fell free to buy me one:

1srgihPwqtNkY3MWDNu6sxgCFcmp5Ne8n

### Was this FAQ really necessary?

Seems so :(

