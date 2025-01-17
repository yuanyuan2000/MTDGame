import React, { useEffect, useState, useContext } from "react";
import NetworkGraph from "./NetworkGraph";
import Terminal from "./Terminal";
import axios from "axios";
import { useNavigate } from 'react-router-dom';
import { UrlPrefixContext } from '../../App';
import { useParams } from 'react-router-dom';

var selectedNodeId = null;
var RES_ADD_STEP = 7;
var RES_REFRESH_DURATION = 3500;
var RES_GET_DETAIL = 5;
var RES_IP_SHUFFLING = 15;
var RES_TOPO_SHUFFLING = 60;
var RES_OS_DIVERSITY = 45;
var RES_SERVICE_DIVERSITY = 15;

function Game() {
    const prefix = useContext(UrlPrefixContext);
    const { roomId } = useParams();
    // isGameStarted is a game state variable, NetworkGraph is rendered when it is true
    const [isGameStarted, setIsGameStarted] = useState(false);
    // command is a terminal state variable, when it is changed the terminal is updated
    const [command, setCommand] = useState(null);
    const [commandcolor, setCommandcolor] = useState(37);
    const [resource, setResource] = useState(0);
    const [networkData, setNetworkData] = useState(null);
    const [gameTime, setGameTime] = useState(0.0);
    const navigate = useNavigate();

    useEffect(() => {
        const startGame = async () => {
            try {
                const response = await axios.get(`${prefix}/api/start_game/?room_id=${roomId}`);
                console.log("/api/start_game response:", response.data.message);
                setIsGameStarted(true);
            } catch (error) {
                console.error("Error starting game:", error);
            }
        };
        startGame();
    }, [prefix, roomId]);

    useEffect(() => {
        // Fetch network data from the API
        const fetchNetworkData = async (prefix) => {
            const response = await axios.get(`${prefix}/api/defender/network_data/?room_id=${roomId}`);
            return response.data;
        };

        const fetchData = async () => {
            const networkData = await fetchNetworkData(prefix);
            setNetworkData(networkData);

            if (!networkData.is_running && networkData.winner) {
                if (networkData.winner === 'Attacker'){
                    alert(`Target node is compromised. You lose.`);
                    setTimeout(() => {
                        navigate('/');
                    }, 1000);
                } else if (networkData.winner === 'Defender'){
                    alert(`Time is up. You win!`);
                    setTimeout(() => {
                        navigate('/');
                    }, 1000);
                }
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
    }, [prefix, roomId, navigate]);

    useEffect(() => {
        if (networkData && typeof networkData.time_used === "number" && typeof networkData.total_time === "number") {
            setGameTime((networkData.total_time - networkData.time_used).toFixed(0));
        }
    }, [networkData]);

    useEffect(() => {
        const intervalId = setInterval(() => {
            setResource((prevResource) => Math.min(prevResource + RES_ADD_STEP, 100));
        }, RES_REFRESH_DURATION);
        return () => clearInterval(intervalId);
    }, []);

    const handleNodeClick = (node_info, nodeId) => {
        setCommand(` `);
        setTimeout(() => {
            setCommandcolor(33);
            setCommand(`Select node ${nodeId} (IP: ${node_info.ip})`);
        }, 30);
        selectedNodeId = nodeId;
    };

    const handleIPShufflingClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= RES_IP_SHUFFLING) {
                setResource(resource - RES_IP_SHUFFLING);
                try {
                    const response = await axios.post(prefix + "/api/defender/network_data/ip_shuffling/", {
                        roomId: roomId,
                        nodeId: selectedNodeId,
                    });
                    if (response.data.is_shuffled) {
                        setCommandcolor(37);
                        setCommand('You have changed the IP of this node. All attack progresses on this node are interrupt.');
                    } else {
                        setCommandcolor(31);
                        setCommand('IP shuffling failed. It may because this node is invalid.');
                    }
                } catch (error) {
                    console.error('Error while posting ip_shuffling:', error);
                }
            } else{
                setCommandcolor(31);
                setCommand(`Insufficient resources (< ${RES_IP_SHUFFLING})`);
            }
        } else {
            setCommandcolor(31);
            setCommand('No node selected.');
        }
    };

    const handleTopologicalShufflingClick = async () => {
        if (resource >= RES_TOPO_SHUFFLING) {
            setResource(resource - RES_TOPO_SHUFFLING);
            try {
                const response = await axios.post(prefix + "/api/defender/network_data/topological_shuffling/", {
                    roomId: roomId,
                    nodeId: selectedNodeId,
                });
                if (response.data.topo_shuffle_result === 1) {
                    setCommandcolor(37);
                    setCommand('You have completely changed the total topological network.');
                } else {
                    setCommandcolor(31);
                    setCommand('Sorry, there are only two chances to do full topological shuffling in a game.');
                    setResource((prevResource) => Math.min(prevResource + 60, 100));
                }
            } catch (error) {
                console.error('Error while posting topological_shuffling:', error);
            }
        } else{
            setCommandcolor(31);
            setCommand(`Insufficient resources (< ${RES_TOPO_SHUFFLING})`);
        }
    };

    const handleOSDiversityClick = async () => {
        if (resource >= RES_OS_DIVERSITY) {
            setResource(resource - RES_OS_DIVERSITY);
            try {
                const response = await axios.post(prefix + "/api/defender/network_data/os_diversity/", {
                    roomId: roomId,
                    nodeId: selectedNodeId,
                });
                setCommandcolor(37);
                setCommand(response.data.os_diversity_result.message);
            } catch (error) {
                console.error('Error while posting os_diversity:', error);
            }
        } else{
            setCommandcolor(31);
            setCommand(`Insufficient resources (< ${RES_OS_DIVERSITY})`);
        }
    };

    const handleServiceDiversityClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= RES_SERVICE_DIVERSITY) {
                setResource(resource - RES_SERVICE_DIVERSITY);
                try {
                    const response = await axios.post(prefix + "/api/defender/network_data/service_diversity/", {
                        roomId: roomId,
                        nodeId: selectedNodeId,
                    });
                    setCommandcolor(37);
                    setCommand(response.data.service_diversity_result.message);
                } catch (error) {
                    console.error('Error while posting service_diversity:', error);
                }
            } else{
                setCommandcolor(31);
                setCommand(`Insufficient resources (< ${RES_SERVICE_DIVERSITY})`);
            }
        } else {
            setCommandcolor(31);
            setCommand('No node selected.');
        }
    };

    const handleDetailsClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= RES_GET_DETAIL) {
                setResource(resource - RES_GET_DETAIL);
                try {
                    const response = await axios.post(prefix + "/api/defender/network_data/get_details/", {
                        roomId: roomId,
                        nodeId: selectedNodeId,
                    });
                    if (response.data.all_details) {
                        const details = response.data.all_details;
                        if (details.is_compromised) {
                            setCommandcolor(37);
                            setCommand(`Node ${selectedNodeId} has been compromised now:`);
                        }
                        else{
                            setCommandcolor(37);
                            setCommand(`Node ${selectedNodeId} is healthy now:`);
                        }
                        let services = Object.keys(details.service_info);
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
                            
                    } else {
                        setCommandcolor(31);
                        setCommand("Error: Details not found.");
                    }
                } catch (error) {
                    console.error('Error while posting get_details:', error);
                }
            } else{
                setCommandcolor(31);
                setCommand(`Insufficient resources (< ${RES_GET_DETAIL})`);
            }
        } else {
            setCommandcolor(31);
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
                        <NetworkGraph prefix={prefix} roomId={roomId} handleNodeClick={handleNodeClick} nodes={networkData.nodes} edges={networkData.edges} selectedNodeId={selectedNodeId} />
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
                        <Terminal command={command}  color={commandcolor}/>
                    </div>
                    <div style={{ display: "flex", justifyContent: "center", marginTop: "-40px" }}>
                        <button onClick={handleDetailsClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>Host Information</button>
                        <button onClick={handleIPShufflingClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>IP Shuffling</button>
                        <button onClick={handleTopologicalShufflingClick} style={{ marginRight: "10px", width: "120px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Full Topological Shuffling</button>
                        <button onClick={handleOSDiversityClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Full OS Diversity</button>
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
