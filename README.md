# MTDSimTime

Integrate time domain into MTDSim based on my research project.

## Setup this project

1. Installing [conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)
2. Creating conda environment
   - `conda env create -f environment.yml`
3. Activating the environment
   - `conda activate mtdsimtime`
4. Updating the environment
   - `conda env update --name mtdsimtime --file environment.yml --prune`
5. Running an example: 
   - `python run_sim.py`
   - Playing around in [simulation.ipynb](https://github.com/MoeBuTa/MTDSimTime/blob/main/simulation.ipynb)
6. Still developing.....


## Progresses

1. set up new discrete event simulation structure:
    - get rid of the original `ActionManager` based structure
    - use [SimPy](https://simpy.readthedocs.io/en/latest/index.html) to manage the time simulation, event processing, interaction (interruption)
    - use [time generator](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/event/time_generator.py) to generate exponential/normal/uniform/weibull/poisson variate

2. set up new mtd action flow in [mtd_event](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/event/mtd_event.py):
    - introduce resource occupation mechanism:
        - MTD fetch resource when it executes, release resource when it completes
        - each resource has a `capacity` parameter (default=1) represents the number of available resource in the network.
        - two types of resource: network / application
            - network: [completetopologyshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/completetopologyshuffle.py), [hosttoplogyshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/hosttopologyshuffle.py), [ipshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/ipshuffle.py)
            - application: [osdiversity](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/osdiversity.py), [portshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/portshuffle.py), [servicediversity](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/servicediversity.py)
            - unknown: [usershuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/usershuffle.py) (_todo_)
    - interrupt attack process:
        - network MTD operation: any attack action -> scan_host
        - application MTD operation: (scan_port, exploit_vuln, brute_force) -> scan_port
    -

3. rework the attack profile to facilitate `SimPy` framework ([hacker](https://github.com/MoeBuTa/MTDSimTime/blob/New-Attack-Method/mtdnetwork/hacker.py) -> [adversary](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/event/adversary.py))
    - scan_host: merged start network enum and set up host enum
    - enum_host: merged start host enum and process host enum
    - scan_port: merged port scan and check pass reuse 
    - exploit_vuln: merged find and exploit vulns
    - brute_force: merged start and process brute force
    - scan_neighbor: merged start and set up new neighbors

4. Initially implement MTD scheduling mechanism, aims to adaptively adjust MTD interval and deploying strategy, currently based on 2 factors:
    - Simulation timestamp - change mtd interval schedule
    - compromised ratio (compromised hosts / total hosts) - change mtd strategy schedule

6. refactoring and updating [data collection methods](https://github.com/MoeBuTa/MTDSimTime/tree/main/mtdnetwork/stats)

7. continuing fix existing known issues and bugs, clean up redundant code, and adjust code structures for further implementations


## Todos
### MTD related
1. MTD triggering strategy -> priority event queue ? (randomly select or base on resource type / priority)
2. MTD suspend / discard choice ?
3. Resource capacity? (1 or more)
4. Assign time mean / std / distribution type ? (MTD triggering interval, executing time of specific MTD)
5. Metrics
6. Interrupt attack by resource type of each MTD strategy or by individual MTD strategy? 
7. pause and resume the simulation and change the settings.

### Attack related
1. refactor time penalty variation caused by MTD interruption (currently it is constant)
2. Extract attack event statistics from record (Implement MTTC)
3. Assign time mean / std / distribution type (each attack action) ?
4. Metrics


## System Architecture
The system uses the 3-layer HARM model to represent the network. This is a representation of the network, with the lowest levels on the bottom and the highest levels on the top:

| layer           | Description                                                                                                                              |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Network         | Made up of all the Hosts, connected in an Attack Graph, with exposed and un-exposed hosts that attackers will attempt to compromise      |
| Host            | Made up of several services (internal and external) in an Attack Graph.  The host is compromised when an internal service is compromised |
| Services        | An attack tree of vulnerabilities. A service is compromised when  the sum of the vulnerabilities exploited impact is above 7             |
| Vulnerabilities | Generated with a set Attack Complexity and Impact                                                                                        |

more info: [MTD parameter](https://github.com/MoeBuTa/MTDSimTime/blob/main/docs/MTD%20Parameters.pdf)


## Setup the previous works only

switch to another branch (MTDSim / New-Attack-Method) or go directly to:

[MTDSim](https://github.com/Ccamm/MTDSim)

[MTDSimTze](https://github.com/tzewenlee99/MTDSimTze)



This was all run on Python 3.9.13 64 Bit. In the root directory in terminal, run the following commands in your virtual environment to setup the environment:

- Setup virtualenv
   - `python -m pip install virtualenv venv`
   - `python -m virtualenv venv`
- Activate environemnt
   - `source venv/bin/activate`
- Install dependencies
   - `python setup.py install`
   - `pip install -r requirements.txt`
- Run an example: The following is only an example of how the function can be made, reference the run.py file or use the –help command to understand the parameters.
   - For New-Attack-Method: 
     - `python batchrun.py`
   - For MTDSim: 
     - `python -m mtdnetwork.run -m IPShuffle -n 50 -e 10 -s 5 -l 3 results.json`


