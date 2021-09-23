#!/bin/bash

sudo apt update;
sudo apt install -y python3.8 python3.8-dev;
git clone https://github.com/Ccamm/MTDSim mtdsim;
cd mtdsim;
sudo python3.8 setup.py install;