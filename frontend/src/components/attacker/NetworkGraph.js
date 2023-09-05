import React, { useState, useEffect } from 'react';
import { DataSet, Network } from 'vis-network/standalone/esm/vis-network';
import axios from 'axios';

// Convert named CSS color to RGB
function colorToRGB(colorName) {
    const div = document.createElement('div');
    div.style.color = colorName;
    document.body.appendChild(div);
    
    const computedStyle = window.getComputedStyle(div);
    const computedColor = computedStyle.color;
  
    document.body.removeChild(div);
    return computedColor;
}
  
// Convert RGB to RGBA with new opacity
function rgbToRGBA(rgb, opacity) {
    return rgb.replace('rgb', 'rgba').replace(')', `, ${opacity})`);
}

// Given a nodeId and a set of edges, returns all edges connected to that node.
function getConnectedEdges(nodeId, allEdges) {
    return allEdges.get({
        filter: edge => edge.from === nodeId || edge.to === nodeId
    });
}

const NetworkGraph = (props) => {
    const { prefix , roomId, handleNodeClick, nodes: initialNodes, edges: initialEdges, visible_nodes: visibleNodes, visible_edges: visibleEdges, selectedNodeId } = props;
    const [nodes, setNodes] = useState(new DataSet(initialNodes));
    const [edges, setEdges] = useState(new DataSet(initialEdges));
    const [network, setNetwork] = useState(null);
    
    useEffect(() => {
        const newNodes = new DataSet(initialNodes);
        const newEdges = new DataSet(initialEdges);
    
        setNodes(newNodes);
        setEdges(newEdges);

        newNodes.forEach((node) => {
            if (visibleNodes.includes(node.id)) {
              newNodes.update({ id: node.id, hidden: false });
            } else {
              newNodes.update({ id: node.id, hidden: true });
            }
            if (node.id === selectedNodeId) {
              // Convert the named CSS color to RGB
              const rgbColor = colorToRGB(node.color.background);
              // Convert the RGB color to RGBA with the desired opacity
              const rgbaColor = rgbToRGBA(rgbColor, 0.9);
              newNodes.update({
                id: node.id,
                color: {
                  background: rgbaColor,
                  // Add these to change the border color and thickness for selected node
                  border: '#FFFFFF', // Red border for selected node
                },
                borderWidth: 1.3, // Thickness for selected node's border
              });

              // Identify edges connected to the selected node
              const connectedEdges = getConnectedEdges(node.id, newEdges);
  
              // Change the color of these edges
              connectedEdges.forEach(edge => {
                newEdges.update({
                  id: edge.id,
                  color: {
                    color: '#D2E5FF',       // Default blue-ish color
                    highlight: '#D2E5FF',  // Highlight color when selected
                    hover: '#D2E5FF'       // Color when hovered over
                  }
                });
              });
            }
          });
          

        newEdges.forEach((edge) => {
            if (visibleEdges.includes(edge.id)) {
                newEdges.update({ id: edge.id, hidden: false });
            } else {
                newEdges.update({ id: edge.id, hidden: true });
            }
        });
    }, [initialNodes, initialEdges, visibleNodes, visibleEdges, selectedNodeId]);
    
    // Create the network graph
    useEffect(() => {
        // Create a new network graph only if it doesn't exist
        if (network === null) {
            const container = document.getElementById('network-graph');
            const data = {
                nodes: nodes,
                edges: edges,
            };
            // Customize the graph's appearance with options
            const options = {
                layout: {
                    improvedLayout: false,
                    hierarchical: {
                        enabled: false,
                    },
                },
                nodes: {
                    borderWidth: 1,
                    borderWidthSelected: 2,
                    chosen: true,
                    color: {
                        border: '#2B7CE9',
                        background: '#97C2FC',
                        highlight: {
                            border: '#2B7CE9',
                            background: '#D2E5FF'
                        },
                        hover: {
                            border: '#2B7CE9',
                            background: '#D2E5FF'
                        }
                    },
                    // opacity: 1,
                    fixed: {
                        x: true,
                        y: true
                    },
                    font: {
                        color: 'black',
                        size: 14, // px
                        face: 'arial',
                        background: 'none',
                        strokeWidth: 0, // px
                        strokeColor: '#ffffff',
                        align: 'center',
                        multi: false,
                        vadjust: 0,
                    },
                    group: undefined,
                    heightConstraint: false,
                    hidden: false,
                    level: undefined,
                    physics: false,
                    scaling: {
                        min: 30,
                        max: 30,
                        label: {
                            enabled: true,
                            min: 10,
                            max: 30,
                            maxVisible: 30,
                            drawThreshold: 5
                        },
                        customScalingFunction: function (min, max, total, value) {
                            if (max === min) {
                                return 0.5;
                            }
                            else {
                                let scale = 1 / (max - min);
                                return Math.max(0, (value - min) * scale);
                            }
                        }
                    },
                    shadow: {
                        enabled: false,
                        color: 'rgba(0,0,0,0.5)',
                        size: 10,
                        x: 5,
                        y: 5
                    },
                    shape: 'circle',
                    shapeProperties: {
                        borderDashes: false,
                    },
                    size: 500,
                    title: undefined,
                    value: undefined,
                    widthConstraint: false,
                },
                edges: {
                    arrows: {
                        to: {
                            enabled: false,
                        },
                        from: {
                            enabled: false,
                        }
                    }
                },
                physics: {
                    enabled: true,
                    solver: 'repulsion',
                    repulsion: {
                        centralGravity: 0,
                        springLength: 200,
                        springConstant: 0.01,
                        nodeDistance: 100,
                        damping: 0.08,
                    },
                },
            };
            // Create a new network graph with the specified container, data, and options
            const newNetwork = new Network(container, data, options);

            // add a click event listener
            newNetwork.on("click", async (params) => {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0]; // get clicked node ID
                    // send a POST request about click event to the API
                    try {
                        const response = await axios.post(prefix + "/api/defender/network_data/clicked_node/", {
                            roomId: roomId,
                            nodeId: nodeId,
                        });
                        // console.log(response.data);
                        // Call handleNodeClick after getting the IP of the clicked node
                        if (response.data.nodeinfo) {
                            handleNodeClick(response.data.nodeinfo, nodeId); 
                        }
                    } catch (error) {
                        console.error('Error while posting clicked_node:', error);
                    }
                }
            });

            setNetwork(newNetwork);
        } else {
            // Update the network instance with the new nodes and edges
            network.setData({ nodes: nodes, edges: edges });
        }
    }, [nodes, edges, network, handleNodeClick, prefix, roomId]);

    // Render the network graph container
    return <div id="network-graph" style={{ width: '100%', height: '100%' }} />;
};

export default NetworkGraph;