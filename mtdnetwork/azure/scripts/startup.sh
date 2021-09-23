#!/bin/bash

sudo apt update;
sudo apt install -y python3.8 python3.8-dev;
python3.8 -m pip install pip;
python3.8 -m pip install setuptools setuptools-rust numpy;
git clone https://github.com/Ccamm/MTDSim mtdsim;
cd mtdsim;
sudo python3.8 setup.py install;