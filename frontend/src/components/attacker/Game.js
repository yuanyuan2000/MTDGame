import React, { useEffect, useState, useContext } from "react";
import NetworkGraph from "./NetworkGraph";
import Terminal from "./Terminal";
import axios from "axios";
import { useNavigate } from 'react-router-dom';
import { UrlPrefixContext } from '../../App';

var selectedNodeId = null; 
var RES_SCAN_HOST = 5;
var RES_SCAN_PORT = 10;
var RES_EXPLOIT_VULN = 40;
var RES_BRUTE_FORCE = 50;

function Game() {
    const prefix = useContext(UrlPrefixContext);
    // isGameStarted is a game state variable, NetworkGraph is rendered when it is true
    const [isGameStarted, setIsGameStarted] = useState(false);
    // command is a terminal state variable, when it is changed the terminal is updated
    const [command, setCommand] = useState(null);
    const [resource, setResource] = useState(0);
    const [networkData, setNetworkData] = useState(null);
    const [gameTime, setGameTime] = useState(0.0);
    const [displayedMessageIds, setDisplayedMessageIds] = useState([]);
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
    }, [prefix]);

    useEffect(() => {
        // Fetch network data from the API
        const fetchNetworkData = async (prefix) => {
            const response = await axios.get(prefix + '/api/attacker/network_data/');
            return response.data;
        };

        const displayMessages = (messages) => {
            const newMessages = messages.filter(msg => !displayedMessageIds.includes(msg.id));
            newMessages.forEach((message, index) => {
                setTimeout(() => {
                    setCommand(message.content);
                }, index * 30);
            });
            setDisplayedMessageIds(displayedMessageIds.concat(newMessages.map(msg => msg.id)));
        };

        const fetchData = async () => {
            const networkData = await fetchNetworkData(prefix);
            setNetworkData(networkData);

            if (networkData.new_message && networkData.new_message.length > 0) {
                displayMessages(networkData.new_message);
            }

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
    }, [prefix, navigate, displayedMessageIds]);

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

    const handleScanHostClick = async () => {
        if (resource >= RES_SCAN_HOST) {
            setResource(resource - RES_SCAN_HOST);
            try {
                const response = await axios.post(prefix + "/api/attacker/network_data/scan_host/", {
                    nodeId: selectedNodeId,
                });
                
                if (response.data.scan_host_list) {
                    let hosts = response.data.scan_host_list;
                    let hostsStr = hosts.join(', ');
                    setCommand(`You have scaned the network, now you can attack these nodes: ${hostsStr}`);
                }
            } catch (error) {
                console.error('Error in enum host:', error);
            }
        } else{
            setCommand(`Insufficient resources (< ${RES_SCAN_HOST})`);
        }
    };
    
    const handleScanPortClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= RES_SCAN_PORT) {
                setResource(resource - RES_SCAN_PORT);
                try {
                    const response = await axios.post(prefix + "/api/attacker/network_data/scan_port/", {
                        nodeId: selectedNodeId,
                    });
                    
                    let scanResult = response.data.scan_port_result;
                    
                    if (scanResult.user_reuse === -1) {
                        setCommand(scanResult.message);
                    } else {
                        if (scanResult.port_list !== null) {
                            // let portsStr = scanResult.port_list.join(', ');
                            setCommand(`${scanResult.message}`);
                        } else {
                            setCommand(scanResult.message);
                        }
                    }
                    
                } catch (error) {
                    console.error('Error', error);
                }
            } else {
                setCommand(`Insufficient resources (< ${RES_SCAN_PORT})`);
            }
        } else {
            setCommand('No node selected.');
        }
    };
    

    const handleExploitVulnClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= RES_EXPLOIT_VULN) {
                setResource(resource - RES_EXPLOIT_VULN);
                try {
                    const response = await axios.post(prefix + "/api/attacker/network_data/exploit_vuln/", {
                        nodeId: selectedNodeId,
                    });
                    console.log(response.data.exploit_vuln_result)
                    if (response.data.exploit_vuln_result === 1) {
                        setCommand("Attack failed, please try other methods or change the node.");
                    } else if (response.data.exploit_vuln_result === 0) {
                        setCommand("The node has been compromised.");
                    }
                } catch (error) {
                    console.error('Error', error);
                }
            } else{
                setCommand(`Insufficient resources (< ${RES_EXPLOIT_VULN})`);
            }
        } else {
            setCommand("No node selected.");
        }
    };
    
    const handleBruteForceClick = async () => {
        if (selectedNodeId !== null) {
            if (resource >= RES_BRUTE_FORCE) {
                setResource(resource - RES_BRUTE_FORCE);
                try {
                    const response = await axios.post(prefix + "/api/attacker/network_data/brute_force/", {
                        nodeId: selectedNodeId,
                    });
                    console.log(response.data.brute_force_result)
                    if (response.data.brute_force_result === 0) {
                        setCommand("Brute force compromising start...");
                    } else if (response.data.brute_force_result === -1) {
                        setCommand("The node can not be accessed now.");
                    }
                } catch (error) {
                    console.error('Error', error);
                }
            } else{
                setCommand(`Insufficient resources (< ${RES_BRUTE_FORCE})`);
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
                        <button onClick={handleScanHostClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>Scan Host</button>
                        <button onClick={handleScanPortClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100 }}>Scan Port</button>
                        <button onClick={handleExploitVulnClick} style={{ marginRight: "10px", width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Exploit Vuln</button>
                        <button onClick={handleBruteForceClick} style={{ width: "100px", height: "35px", backgroundColor: "#262626", color: "white", border: "none", borderRadius: "5px", cursor: "pointer", zIndex: 100  }}>Brute force</button>
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
