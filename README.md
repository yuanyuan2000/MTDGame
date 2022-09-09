# MTDSimTime

Integrating the time domain into MTDSim based on my research thesis:

### Setup this project

1. Install conda: https://conda.io/projects/conda/en/latest/user-guide/install/index.html
2. Creating conda environment
   - conda env create -f environment.yml
3. Activating the environment
   - conda activate mtdsimtime
4. Updating the environment
   - conda env update --name mtdsimtime --file environment.yml --prune
5. Still developing.....

### Architecture
The system uses the 3-layer HARM model to represent the network. This is a representation of the network, with the lowest levels on the bottom and the highest levels on the top:

| layer           | Description                                                                                                                              |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Network         | Made up of all the Hosts, connected in an Attack Graph, with exposed and un-exposed hosts that attackers will attempt to compromise      |
| Host            | Made up of several services (internal and external) in an Attack Graph.  The host is compromised when an internal service is compromised |
| Services        | An attack tree of vulnerabilities. A service is compromised when  the sum of the vulnerabilities exploited impact is above 7             |
| Vulnerabilities | Generated with a set Attack Complexity and Impact                                                                                        |



### Setup the previous works only

switch to another branch (MTDSim / New-Attack-Method)
This was all run on Python 3.9.13 64 Bit. In the root directory in terminal, run the following commands in your virtual environment to setup the environment:

- Setup virtualenv
   - python -m pip install virtualenv venv
   - python -m virtualenv venv
- Activate environemnt
   - source venv/bin/activate
- Install dependencies
   - python setup.py install
   - pip install -r requirements.txt
- Run an example: The following is only an example of how the function can be made, reference the run.py file or use the –help command to understand the parameters.
   - For New-Attack-Method: python batchrun.py
   - For MTDSim: python -m mtdnetwork.run -m IPShuffle -n 50 -e 10 -s 5 -l 3 results.json
