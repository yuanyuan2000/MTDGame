import os

os.system("Python -m mtdnetwork.run -tar 2 No-MTD-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m portshuffle PortShuffle-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m ipshuffle IPShuffle-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m osdiversity OSDiversity-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m servicediversity ServiceDiversity-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m usershuffle UserShuffle-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m hosttopologyshuffle HostTopologyShuffle-T2-results.json")
os.system("Python -m mtdnetwork.run -tar 2 -m completetopologyshuffle CompleteTopologyShuffle-T2-results.json")

os.system("Python -m mtdnetwork.run No-MTD-T3-results.json")
os.system("Python -m mtdnetwork.run -m portshuffle PortShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m ipshuffle IPShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m osdiversity OSDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m servicediversity ServiceDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m usershuffle UserShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m hosttopologyshuffle HostTopologyShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m completetopologyshuffle CompleteTopologyShuffle-T3-results.json")

os.system("Python -m mtdnetwork.run -tar 4 No-MTD-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m portshuffle PortShuffle-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m ipshuffle IPShuffle-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m osdiversity OSDiversity-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m servicediversity ServiceDiversity-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m usershuffle UserShuffle-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m hosttopologyshuffle HostTopologyShuffle-T4-results.json")
os.system("Python -m mtdnetwork.run -tar 4 -m completetopologyshuffle CompleteTopologyShuffle-T4-results.json")


os.system("Python -m mtdnetwork.run -m portshuffle,ipshuffle PortShuffle-IPShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m portshuffle,osdiversity PortShuffle-OSDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m portshuffle,servicediversity PortShuffle-ServiceDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m portshuffle,usershuffle PortShuffle-UserShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m portshuffle,hosttopologyshuffle PortShuffle-HostTopologyShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m portshuffle,completetopologyshuffle PortShuffle-CompleteTopologyShuffle-T3-results.json")

os.system("Python -m mtdnetwork.run -m ipshuffle,osdiversity IPShuffle-OSDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m ipshuffle,servicediversity IPShuffle-ServiceDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m ipshuffle,usershuffle IPShuffle-UserShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m ipshuffle,hosttopologyshuffle IPShuffle-HostTopologyShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m ipshuffle,completetopologyshuffle IPShuffle-CompleteTopologyShuffle-T3-results.json")

os.system("Python -m mtdnetwork.run -m osdiversity,servicediversity OSDiversity-ServiceDiversity-T3-results.json")
os.system("Python -m mtdnetwork.run -m osdiversity,usershuffle OSDiversity-UserShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m osdiversity,hosttopologyshuffle OSDiversity-HostTopologyShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m osdiversity,completetopologyshuffle OSDiversity-CompleteTopologyShuffle-T3-results.json")

os.system("Python -m mtdnetwork.run -m servicediversity,usershuffle ServiceDiversity-UserShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m servicediversity,hosttopologyshuffle ServiceDiversity-HostTopologyShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m servicediversity,completetopologyshuffle ServiceDiversity-CompleteTopologyShuffle-T3-results.json")

os.system("Python -m mtdnetwork.run -m usershuffle,hosttopologyshuffle UserShuffle-HostTopologyShuffle-T3-results.json")
os.system("Python -m mtdnetwork.run -m usershuffle,completetopologyshuffle UserShuffle-CompleteTopologyShuffle-T3-results.json")

os.system("Python -m mtdnetwork.run -m hosttopologyshuffle,completetopologyshuffle HostTopologyShuffle-CompleteTopologyShuffle-T3-results.json")



