#!/bin/bash

# Install the build dependencies
sudo apt-get build-dep python-imaging

# Symlink the libraries:
if [ ! -f /usr/lib/libfreetype.so ];
then
    echo "/usr/lib/libfreetype.so not found! Created a symlink for it.";
    sudo ln -f -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/;
fi
if [ ! -f /usr/lib/libjpeg.so ];
then
    echo "/usr/lib/libjpeg.so not found! Created a symlink for it.";
    sudo ln -f -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
fi
if [ ! -f /usr/lib/libz.so ];
then
    echo "/usr/lib/libz.so not found! Created a symlink for it.";
    sudo ln -f -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/;
fi

pip install -r requirements.txt
