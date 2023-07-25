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

    const handleEnumHostClick = async () => {
        if (resource >= 15) {
            setResource(resource - 15);
            try {
                const response = await axios.post(prefix + "/api/attacker/network_data/enum_host/", {
                    nodeId: selectedNodeId,
                });
                console.log(response.data.enum_host_list)
            } catch (error) {
                console.error('Error in enum host:', error);
            }
        } else{
            setCommand('Insufficient resources (<15)');
        }
    };

    const handleScanPortClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 30) {
                setResource(resource - 30);
                try {
                    const response = await axios.post(prefix + "/api/attacker/network_data/scan_port/", {
                        nodeId: selectedNodeId,
                    });
                    console.log(response.data.scan_port_result)
                } catch (error) {
                    console.error('Error', error);
                }
            } else{
                setCommand('Insufficient resources (<30)');
            }
        } else {
            setCommand('No node selected.');
        }
    };

    const handleExploitVulnClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 30) {
                setResource(resource - 30);
                try {
                    const response = await axios.post(prefix + "/api/attacker/network_data/exploit_vuln/", {
                        nodeId: selectedNodeId,
                    });
                    console.log(response.data.exploit_vuln_result)
                } catch (error) {
                    console.error('Error', error);
                }
            } else{
                setCommand('Insufficient resources (<30)');
            }
        } else {
            setCommand("No node selected.");
        }
    };

    const handleBruteForceClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= 40) {
                setResource(resource - 40);
                try {
                    const response = await axios.post(prefix + "/api/attacker/network_data/brute_force/", {
                        nodeId: selectedNodeId,
                    });
                    console.log(response.data.brute_force_result)
                } catch (error) {
                    console.error('Error', error);
                }
            } else{
                setCommand('Insufficient resources (<40)');
            }
        } else {
            setCommand('No node selected.');
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
                        <button onClick={handleEnumHostClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>Enum Host</button>
                        <button onClick={handleScanPortClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>Scan Port</button>
                        <button onClick={handleExploitVulnClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Exploit Vuln</button>
                        {/* <button onClick={handleOSDiversityClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>OS Diversity</button> */}
                        <button onClick={handleBruteForceClick} style={{ width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Brute force</button>
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
