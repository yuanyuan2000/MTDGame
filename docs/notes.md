## progress

1. set up new discrete event simulation structure:
   - get rid of the original `ActionManager` structure,
   - use `SimPy` to manage the time simulation, event processing, process interaction (interruption)
   - implement time generator to generate exponential/normal/uniform/weibull/poisson variate

2. set up new mtd action flow:
   - introduce resource occupation mechanism:
     - MTD fetch resource when it executes, release resource when it completes
     - each resource has a `capacity` parameter (default=1)
     - two resources: network / application
       - network: completetopologyshuffle, hosttoplogyshuffle, ipshuffle
       - application: osdiversity, portshuffle, servicediversity
       - unknown: usershuffle
   - interrupt attack process:
     - network: any -> scan_host
     - application: (scan_port, exploit_vuln, brute_force) -> scan_port
   - 
       
3. rework the attack profile to facilitate `SimPy` framework (hacker -> adversary)
   - scan_host: merged start network enum and set up host enum
   - enum_host: merged start host enum and process host enum
   - scan_port: merged port scan and check pass reuse
   - exploit_vuln: merged find and exploit vulns
   - brute_force: merged start and process brute force
   - scan_neighbor: merged start and set up new neighbors

5. refactoring and updating data collection and analysis methods
6. fixing existing known issues and bugs.
7. continuing clean up redundant code and adjust code structures for further implementations


## todo
### MTD related 
1. MTD triggering strategy -> priority event queue ? (randomly select or base on resource type / priority)
2. MTD suspend / discard choice ?
3. Resource capacity? (1 or more)
4. Assign time mean / std / distribution type ? (MTD triggering interval, executing time of specific MTD)
5. Metrics
6. Interrupted attack by resource type of MTD or by individual MTD? ()

### Attack related
1. refactor time penalty variation caused by MTD interruption (currently it is constant)
2. Extract attack event statistics from record (Implement MTTC)
3. Assign time mean / std / distribution type (each attack action) ?
4. Metrics
