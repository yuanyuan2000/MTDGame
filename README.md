# MTDGame

A research project to develop a web-based multiplayer game that facilitates the learning of MTD concepts and strategies for students. 

## Requirements

- [Docker](https://www.docker.com/)
- [Visual Studio Code](https://code.visualstudio.com/)

## Setup this project

1. Clone this repository to your computer, install docker desktop, open VS code and choose right branch
2. open Terminal in VS Code, build docker image for developing environment `sudo docker-compose up --build` if you are first time to start this project or last time install package during the development(it takes about 2-3 minutes); otherwise, you can run `sudo docker-compose up`
3. View MTDGame in the browser : `http://localhost:3000`
4. Stop development environment Crtl/Cmd+C, then `sudo docker-compose down`. Please remember to do that everytime.

## Install new packages

### The environment we use now

1. Open a new terminal in VS Code (Terminal > Split Terminal)
2. Access backend container `sudo docker exec -it backend bash` in a new terminal to install packages `pip install <packages name>` then update requirements.txt `pip freeze > requirements.txt`, then type `exit` to exit backend container.
3. Access frontend container `sudo docker exec -it frontend bash` to install packages `yard add <packages name>` then `package.json` and  `yarn.lock` will be updated automatically, then type `exit` to exit frontend container. 
(Please make sure to use only one package manager for the whole project to avoid possible problems, so don't use conda in backend or npm in frontend)

### If use the **environment.yml** for the backend
(The default version now is using the requirement.txt. So if you want to use the environment.yml, you need change the code in MTDGame/docker/Django/Django.Dockerfile. Just comment out all the current code and uncomment all the previously commented out code.)
1.  The `environment.yml` is in `MTDGame/backend`, which includes the environment we want, please switch to the `cd backend`
2.  Create a new conda environment and activate it in your local machine by `conda env create -f environment.yml` and `conda activate mtdgame`
3.  Install new packages `conda install new_package` or `pip install new_pip_package`
4.  Export the dependencies of the current environment to the `environment.yml` by `conda env export --no-builds > environment.yml`
5.  Deactive the conda environment `conda deactivate`
6.  Switch the folder to MTDGame `cd ..` then rebuild the docker image for developing environment `sudo docker-compose up --build`


## Previous work
### Progresses

1. set up new discrete event simulation structure:
    - get rid of the original `ActionManager` based structure
    - use [SimPy](https://simpy.readthedocs.io/en/latest/index.html) to manage the time simulation, event processing, interaction (interruption)
    - use [time generator](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/component/time_generator.py) to generate exponential/normal/uniform/weibull/poisson variate

2. set up new mtd action flow in [mtd_operation](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/operation/mtd_operation.py):
    - introduce resource occupation mechanism:
        - MTD fetch resource when it executes, release resource when it completes
        - each resource has a `capacity` parameter (default=1) represents the number of available resource in the network.
        - two types of resource: network / application
            - network: [completetopologyshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/completetopologyshuffle.py), [hosttoplogyshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/hosttopologyshuffle.py), [ipshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/ipshuffle.py)
            - application: [osdiversity](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/osdiversity.py), [portshuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/portshuffle.py), [servicediversity](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/servicediversity.py)
            - reserve: [usershuffle](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/mtd/usershuffle.py) (_todo_)
    - interrupt attack process:
        - network MTD operation: any attack action -> scan_host
        - application MTD operation: (scan_port, exploit_vuln, brute_force) -> scan_port
    -

3. Rework the attack profile to facilitate `SimPy` framework ([hacker](https://github.com/MoeBuTa/MTDSimTime/blob/New-Attack-Method/mtdnetwork/hacker.py) -> [adversary](https://github.com/MoeBuTa/MTDSimTime/blob/main/mtdnetwork/component/adversary.py))
    - scan_host: merged start network enum and set up host enum
    - enum_host: merged start host enum and process host enum
    - scan_port: merged port scan and check pass reuse 
    - exploit_vuln: merged find and exploit vulns
    - brute_force: merged start and process brute force
    - scan_neighbor: merged start and set up new neighbors
    

4. Implement snapshot mechanism to save the state of the network object and the adversary object. Restrictions with generator object issues:
    - cannot save and maintain generator object generated by SimPy when saving
    - **solution**: [snapshot saving](https://github.com/MoeBuTa/MTDSimTime/tree/main/mtdnetwork/snapshot) [operation](https://github.com/MoeBuTa/MTDSimTime/tree/main/mtdnetwork/operation)
      - extract mtd_operation object from network object to handle state saving for network object
      - extract attack_operation object from adversary object to handle state saving for adversary object
      - introduce SnapshotCheckpoint to save and load files based on simulation time.

5. Refactor [data collection and analysis](https://github.com/MoeBuTa/MTDSimTime/tree/main/mtdnetwork/statistic)

6. implement three [MTD Schemes](https://github.com/MoeBuTa/MTDSimTime/tree/main/mtdnetwork/component/mtd_scheme): simultaneously, randomly, alternatively.

7. implement evaluation metrics: Mean Time to Compromise, Attack Success Rate, MTD Execute Frequency.

### Setup the previous works only
Switch to previous work:
- [MTDSimTime](https://github.com/MoeBuTa/MTDSimTime)
- [MTDSim](https://github.com/Ccamm/MTDSim)
- [MTDSimTze](https://github.com/tzewenlee99/MTDSimTze)

MTDSimTime was run on the conda. You just need to follow the [README.md](https://github.com/MoeBuTa/MTDSimTime/blob/main/README.md) to config the environment.

MTDSim and MTDSimTze were all run on Python 3.9.13 64 Bit. In the root directory in terminal, run the following commands in your virtual environment to setup the environment:
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



## Todos / Future works
### Time related
 - assign mean/std/distribution of each time variable based on system properties, sensitivity analysis, empirical data (currently is randomly assigned)
 - more time based evaluation metrics

### MTD related
1. defense metrics (implement QOS)
2. reconfiguration limit
   - dynamic MTD
   - resource capacity (1 or more)
   - system state
3. AI


### Attack related
1. Attack metrics
2. multiple attackers



## System Architecture
The system uses the 3-layer HARM model to represent the network. This is a representation of the network, with the lowest levels on the bottom and the highest levels on the top:

| layer           | Description                                                                                                                              |
|-----------------|------------------------------------------------------------------------------------------------------------------------------------------|
| Network         | Made up of all the Hosts, connected in an Attack Graph, with exposed and un-exposed hosts that attackers will attempt to compromise      |
| Host            | Made up of several services (internal and external) in an Attack Graph.  The host is compromised when an internal service is compromised |
| Services        | An attack tree of vulnerabilities. A service is compromised when  the sum of the vulnerabilities exploited impact is above 7             |
| Vulnerabilities | Generated with a set Attack Complexity and Impact                                                                                        |

more info: [MTD parameter](https://github.com/MoeBuTa/MTDSimTime/blob/main/docs/MTD%20Parameters.pdf)





