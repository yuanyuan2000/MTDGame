#!/bin/bash

sudo apt update;
sudo apt install -y build-essential libssl-dev libffi-dev rustc python3.8 python3.8-dev;
sudo apt install -y python3-pip;
sudo python3.8 -m pip install --upgrade pip;
sudo python3.8 -m pip install setuptools setuptools-rust numpy Cython;
git clone https://github.com/Ccamm/MTDSim mtdsim;
cd mtdsim;
sudo python3.8 setup.py install;