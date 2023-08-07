import React, { useEffect, useState } from "react";
import NetworkGraph from "./NetworkGraph";
import Terminal from "./Terminal";
import axios from "axios";
import { useNavigate } from 'react-router-dom';

var prefix = "http://localhost:8000";
var selectedNodeId = null; 

function Game() {
    // isGameStarted is a game state variable, NetworkGraph is rendered when it is true
    const [isGameStarted, setIsGameStarted] = useState(false);
    // command is a terminal state variable, when it is changed the terminal is updated
    const [command, setCommand] = useState(null);
    const [resource, setResource] = useState(0);
    const [networkData, setNetworkData] = useState(null);
    const [gameTime, setGameTime] = useState(0.0);
    const navigate = useNavigate();

    useEffect(() => {
        const startGame = async () => {
            try {
                const response = await axios.get(prefix + "/api/start_game/");
                console.log("/api/start_game response:", response.data.message);
                setIsGameStarted(true);
            } catch (error) {
                console.error("Error starting game:", error);
            }
        };
        startGame();
    }, []);

    useEffect(() => {
        // Fetch network data from the API
        const fetchNetworkData = async (prefix) => {
            const response = await axios.get(prefix + '/api/attacker/network_data/');
            return response.data;
        };

        const fetchData = async () => {
            const networkData = await fetchNetworkData(prefix);
            setNetworkData(networkData);

            if (!networkData.is_running && networkData.winner) {
                alert(`Game over! The ${networkData.winner} win.`);
                navigate('/');
            }
        };

        let intervalId = null;
        const delay = 1000;
        const interval = 1000;
        const timeoutId = setTimeout(() => {
            fetchData();
            intervalId = setInterval(fetchData, interval);
        }, delay);
    
        return () => {
            clearTimeout(timeoutId);
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [navigate]);

    useEffect(() => {
        if (networkData && typeof networkData.time_used === "number" && typeof networkData.total_time === "number") {
            setGameTime((networkData.total_time - networkData.time_used).toFixed(1));
        }
    }, [networkData]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            setResource((prevResource) => Math.min(prevResource + 4, 100));
        }, 1000);
        return () => clearInterval(intervalId);
    }, []);

    const handleNodeClick = (node_info, nodeId) => {
        setCommand(`Select node ${nodeId} (IP: ${node_info.ip})`);
        selectedNodeId = nodeId;
    };

    const handleIPShufflingClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 20) {
                setResource(resource - 20);
                try {
                    const response = await axios.post(prefix + "/api/defender/network_data/ip_shuffling/", {
                        nodeId: selectedNodeId,
                    });
                    if (response.data.is_shuffled) {
                        setCommand('You have changed the IP of this node. All attack progresses on this node are interrupt.');
                    } else {
                        setCommand('IP shuffling failed. It may because: 1. Don\'t choose a valid node. 2. Don\'t have enough resource to do this MTD operation');
                    }
                } catch (error) {
                    console.error('Error while posting ip_shuffling:', error);
                }
            } else{
                setCommand('Insufficient resources (<20)');
            }
        } else {
            setCommand('No node selected.');
        }
    };

    const handleTopologicalShufflingClick = async () => {
        if (resource >= 50) {
            setResource(resource - 50);
            try {
                const response = await axios.post(prefix + "/api/defender/network_data/topological_shuffling/", {
                    nodeId: selectedNodeId,
                });
                if (response.data.is_shuffled) {
                    setCommand('You have completely changed the total topological network.');
                } else {
                    setCommand('Toplogical shuffling failed. It may because: 1. Don\'t have enough resource to do this MTD operation');
                }
            } catch (error) {
                console.error('Error while posting topological_shuffling:', error);
            }
        } else{
            setCommand('Insufficient resources (<50)');
        }
    };

    const handleOSDiversityClick = async () => {
        if (resource >= 30) {
            setResource(resource - 30);
            try {
                const response = await axios.post(prefix + "/api/defender/network_data/os_diversity/", {
                    nodeId: selectedNodeId,
                });
                if (response.data.is_sucessful) {
                    setCommand('You have finished the OS diversity for all nodes. Now they are more difficult for attacker to exploit vulnerabilities.');
                } else {
                    setCommand('OS diversity failed. It may because: 1. Don\'t have enough resource to do this MTD operation');
                }
            } catch (error) {
                console.error('Error while posting os_diversity:', error);
            }
        } else{
            setCommand('Insufficient resources (<30)');
        }
    };

    const handleServiceDiversityClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 10) {
                setResource(resource - 10);
                try {
                    const response = await axios.post(prefix + "/api/defender/network_data/service_diversity/", {
                        nodeId: selectedNodeId,
                    });
                    if (response.data.is_sucessful) {
                        setCommand('You have change the service of the host on this node. Now it is more difficult for attacker to exploit its vulnerabilities.');
                    } else {
                        setCommand('Service diversity failed. It may because: 1. Don\'t choose a valid node. 2. Don\'t have enough resource to do this MTD operation');
                    }
                } catch (error) {
                    console.error('Error while posting service_diversity:', error);
                }
            } else{
                setCommand('Insufficient resources (<10)');
            }
        } else {
            setCommand('No node selected.');
        }
    };

    const handleDetailsClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 5) {
                setResource(resource - 5);
                try {
                    const response = await axios.post(prefix + "/api/defender/network_data/get_details/", {
                        nodeId: selectedNodeId,
                    });
                    if (response.data.all_details) {
                        const details = response.data.all_details;
                        if (details.is_compromised) {
                            setCommand(`Node ${selectedNodeId} has been compromised.`);
                        }
                        else{
                            let services = Object.keys(details.service_info);
                            setCommand(`Node ${selectedNodeId} is healthy now:`);
                            setTimeout(() => {
                                setCommand(`OS Type: ${details.os_type}`);
                                setTimeout(() => {
                                    setCommand(`OS Version: ${details.os_version}`);
                                    setTimeout(() => {
                                        setCommand(`Diversity Score: ${details.diversity_score}`);
                                        setTimeout(() => {
                                            setCommand(`IP: ${details.ip}`);
                                            setTimeout(() => {
                                                setCommand(`Number of services: ${services.length}`);
                                                services.forEach((serviceName, index) => {
                                                setTimeout(() => {
                                                    setCommand(`- ${serviceName}`);
                                                    if (index === services.length - 1) {
                                                    setTimeout(() => {
                                                        setCommand(` `);  // Add a new line at the end
                                                    }, 30);
                                                    }
                                                }, (index + 4) * 30);  // Wait 30 ms for each service
                                                });
                                            }, 30);
                                        }, 30);
                                    }, 30);
                                }, 30);
                            }, 30);
                            }
                    } else {
                        setCommand("Error: Details not found.");
                    }
                } catch (error) {
                    console.error('Error while posting get_details:', error);
                }
            } else{
                setCommand('Insufficient resources (<5)');
            }
        } else {
            setCommand("No node selected.");
        }
    };

    return (
        <div className="App"
            style={{
                backgroundColor: "#343434",
                width: "100%",
                height: "100vh",
            }}>
            <div className="main-container" style={{ width: "65%" }}>
                <div
                    className="network-graph-container"
                    style={{ width: "100%", height: "70vh" }}
                >
                    {isGameStarted && networkData && (
                        <NetworkGraph prefix={prefix} handleNodeClick={handleNodeClick} nodes={networkData.nodes} edges={networkData.edges} visibleHosts={networkData.visible_hosts} />
                    )}
                </div>
                <div
                    className="terminal-wrapper"
                    style={{
                        position: "fixed",
                        right: 0, // Set the desired distance from the right edge
                        bottom: "15%", // Set the desired distance from the bottom edge
                        zIndex: 1000, // Ensure the terminal is on top
                        width: "35%", // Set the desired width
                        height: "80%", // Set the desired height
                    }}
                >
                    <p style={{ fontSize: "18px", color: "green" }}>Game time remaining: {gameTime} seconds</p>
                    <div
                        className="terminal-container"
                        style={{
                            backgroundColor: "#2d2d2d",
                            width: "100%",
                            height: "90%",
                            paddingBottom: "10px", 
                        }}
                    >
                        <Terminal command={command} />
                    </div>
                    <div style={{ display: "flex", justifyContent: "center", marginTop: "-40px" }}>
                        <button onClick={handleDetailsClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>Health Check</button>
                        <button onClick={handleIPShufflingClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>IP Shuffling</button>
                        <button onClick={handleTopologicalShufflingClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Topological Shuffling</button>
                        <button onClick={handleOSDiversityClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>OS Diversity</button>
                        <button onClick={handleServiceDiversityClick} style={{ width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Service Diversity</button>
                    </div>
                    <div>
                    <p style={{ fontSize: "18px", color: "blue" }}>Resources: {resource}</p>
                        <progress value={resource} max="100" />
                    </div>
                </div>
            </div>
        </div >
    );
}

export default Game;