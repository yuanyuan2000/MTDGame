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

    const handleNodeClick = (ip, nodeId) => {
        setCommand(`Select node ${nodeId}. IP: ${ip}`);
        selectedNodeId = nodeId;
    };

    const handleIPShufflingClick = async () => {
        if (selectedNodeId !== null) {
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
        } else {
            setCommand('No node selected.');
        }
    };

    const handleTopologicalShufflingClick = async () => {
        try {
            const response = await axios.post(prefix + "/api/network_data/topological_shuffling/", {
                nodeId: selectedNodeId,
            });
            if (response.data.is_shuffled) {
                setCommand('You have completely changed the topology.');
            } else {
                setCommand('Completely toplogical shuffling failed.');
            }
        } catch (error) {
            console.error('Error while posting ip_shuffling:', error);
        }
    };

    return (
        <div className="App"
            style={{
                backgroundColor: "#343434",
                width: "100%",
                height: "100vh",
            }}>
            <div className="main-container" style={{ width: "70%" }}>
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
                        bottom: "25%", // Set the desired distance from the bottom edge
                        zIndex: 1000, // Ensure the terminal is on top
                        width: "30%", // Set the desired width
                        height: "50%", // Set the desired height
                    }}
                >
                    <div
                        className="terminal-container"
                        style={{
                            backgroundColor: "#2d2d2d",
                            width: "100%",
                            height: "100%",
                        }}
                    >
                        <Terminal command={command} />
                    </div>
                    <div style={{ display: "flex", justifyContent: "center", marginTop: "-40px" }}>
                        <button onClick={handleIPShufflingClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>IP Shuffling</button>
                        <button onClick={handleTopologicalShufflingClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Topological Shuffling</button>
                        <button style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>OS Diversity</button>
                        <button style={{ width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Service Diversity</button>
                    </div>
                </div>
            </div>
        </div >
    );
}

export default Game;
