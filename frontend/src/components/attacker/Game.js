import React, { useEffect, useState } from "react";
import NetworkGraph from "./NetworkGraph";
import Terminal from "./Terminal";
import axios from "axios";

// Define a prefix for the API URL
var prefix = "http://localhost:8000";
// a global variable to store the selected node id
var selectedNodeId = null; 

function Game() {
    // isGameStarted is a game state variable, NetworkGraph is rendered when it is true
    const [isGameStarted, setIsGameStarted] = useState(false);
    // command is a terminal state variable, when it is changed the terminal is updated
    const [command, setCommand] = useState(null);
    // resource is the resource for the user
    const [resource, setResource] = useState(0);

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
            if (resource >= 40) {
                setResource(resource - 40);
                try {
                    const response = await axios.post(prefix + "/api/network_data/ip_shuffling/", {
                        nodeId: selectedNodeId,
                    });
                    if (response.data.is_shuffled) {
                        setCommand('You have changed the IP of this node.');
                    } else {
                        setCommand('IP shuffling failed. It may because: 1. Don\'t choose a valid node. 2. Don\'t have enough resource to do this MTD operation');
                    }
                } catch (error) {
                    console.error('Error while posting ip_shuffling:', error);
                }
            } else{
                setCommand('Insufficient resources (<40)');
            }
        } else {
            setCommand('No node selected.');
        }
    };

    const handleTopologicalShufflingClick = async () => {
        if (resource >= 100) {
            setResource(resource - 100);
            try {
                const response = await axios.post(prefix + "/api/network_data/topological_shuffling/", {
                    nodeId: selectedNodeId,
                });
                if (response.data.is_shuffled) {
                    setCommand('You have completely changed the topology.');
                } else {
                    setCommand('Toplogical shuffling failed. It may because: 1. Don\'t have enough resource to do this MTD operation');
                }
            } catch (error) {
                console.error('Error while posting topological_shuffling:', error);
            }
        } else{
            setCommand('Insufficient resources (<100)');
        }
    };

    const handleOSDiversityClick = async () => {
        if (resource >= 60) {
            setResource(resource - 60);
            try {
                const response = await axios.post(prefix + "/api/network_data/os_diversity/", {
                    nodeId: selectedNodeId,
                });
                if (response.data.is_sucessful) {
                    setCommand('You have finished the OS diversity for all nodes.');
                } else {
                    setCommand('OS diversity failed. It may because: 1. Don\'t have enough resource to do this MTD operation');
                }
            } catch (error) {
                console.error('Error while posting os_diversity:', error);
            }
        } else{
            setCommand('Insufficient resources (<60)');
        }
    };

    const handleServiceDiversityClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 30) {
                setResource(resource - 30);
                try {
                    const response = await axios.post(prefix + "/api/network_data/service_diversity/", {
                        nodeId: selectedNodeId,
                    });
                    if (response.data.is_sucessful) {
                        setCommand('You have change the service of the host on this node.');
                    } else {
                        setCommand('Service diversity failed. It may because: 1. Don\'t choose a valid node. 2. Don\'t have enough resource to do this MTD operation');
                    }
                } catch (error) {
                    console.error('Error while posting service_diversity:', error);
                }
            } else{
                setCommand('Insufficient resources (<30)');
            }
        } else {
            setCommand('No node selected.');
        }
    };

    const handleDetailsClick = async () => {
        if (selectedNodeId) {
            if (resource >= 15) {
                setResource(resource - 15);
                try {
                    const response = await axios.post(prefix + "/api/network_data/get_details/", {
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
                            }
                    } else {
                        setCommand("Error: Details not found.");
                    }
                } catch (error) {
                    console.error('Error while posting get_details:', error);
                }
            } else{
                setCommand('Insufficient resources (<15)');
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
                    {isGameStarted && (
                        <NetworkGraph prefix={prefix} handleNodeClick={handleNodeClick} />
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
                        <p>Resources: {resource}</p>
                        <progress value={resource} max="100" />
                    </div>
                </div>
            </div>
        </div >
    );
}

export default Game;
