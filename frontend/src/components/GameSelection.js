import React, { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { UrlPrefixContext } from '../App';
import { Collapse } from 'react-collapse';
import backgroundImage from './background.png';
import pngq1p1 from './q1p1.png'
import pngq1p2 from './q1p2.png'
import pngq1p3 from './q1p3.png'
import pngq1p4 from './q1p4.png'
import pngq2p1 from './q2p1.png'
import pngq2p2 from './q2p2.png'
import pngq2p3 from './q2p3.png'
import pngq2p4 from './q2p4.png'

const GameSelection = () => {
  const prefix = useContext(UrlPrefixContext);
  const [gameMode, setGameMode] = useState("Human");
  const [role, setRole] = useState("attacker");
  const [roomId, setRoomId] = useState("");
  const navigate = useNavigate();
  const [activeQuestion, setActiveQuestion] = useState(null); // Track the currently open question

  const createGame = async () => {
    try {
        const response = await axios.post(prefix + "/api/create_game_room/", {
        game_mode: gameMode,
        creator_role: role,
        room_id: roomId,
        });
        navigate(`/game/${response.data.creator_role}/${response.data.room_id}`);
    } catch (error) {
        // console.error("Error create room:", error);
        alert(`Your game room has been created. Please input right room number and click Join Game.`);
    }
    
  };
  
  const joinGame = async () => {
    try {
        const response = await axios.post(prefix + "/api/join_game_room/", {
        joiner_role: role,
        room_id: roomId,
        });
        navigate(`/game/${response.data.joiner_role}/${response.data.room_id}`);
    } catch (error) {
        // console.error("Error join room:", error);
        alert(`Join game failed. It may because the room has not been created.`);
    } 
  };

  // Function to toggle the visibility of answers
  const toggleAnswer = (index) => {
    if (activeQuestion === index) {
      setActiveQuestion(null);
    } else {
      setActiveQuestion(index);
    }
  };

  const containerStyle = {
    display: "flex",
    flexDirection: "row",
    justifyContent: "center", // centering the main two containers
    alignItems: "center",
    height: "100vh",
    backgroundImage: `url(${backgroundImage})`,
    backgroundSize: 'cover',  // let the image cover background
    backgroundPosition: 'center center',
  };

  const leftContainerStyle = {
    width: "50%",
    height: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  };
  
  const rightContainerStyle = {
    width: "50%",
    height: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  };

  const formStyle = {
    width: "30%",
    height: "25%",
    marginLeft: "10%",
    backgroundColor: "#eeeeee",
    borderRadius: "10px",
    padding: "2rem",
    boxShadow: "0px 6px 16px rgba(255, 255, 0, 0.8)"
  };

  const buttonStyle = {
    backgroundColor: "#4CAF50",
    border: "none",
    color: "white",
    padding: "10px 20px",
    textAlign: "center",
    textDecoration: "none",
    display: "inline-block",
    fontSize: "16px",
    margin: "4px 2px",
    cursor: "pointer",
  };

  const tutorialContainerStyle = {
    width: "65%",
    minHeight: "75%",
    maxHeight: "75%",
    marginLeft: "20%",
    overflowY: "auto", // Show scrollbars when the content exceeds the height of the container
    padding: "1rem",
    borderRadius: "10px",
    backgroundColor: "#dddddd",
    boxShadow: "0px 6px 16px rgba(255, 0, 0, 0.8)"
  };

  const accordionStyle = {
    width: "100%",
    cursor: "pointer",
    backgroundColor: "#bbb",
    padding: "10px",
    border: "none",
    textAlign: "left",
    outline: "none",
    transition: "0.4s",
  };

  const accordionStyleWithBorder = {
    ...accordionStyle,  // Use the spread operator to include properties from the previous accordionStyle
    position: 'relative',  // This ensures our pseudo-element is positioned relative to this element
    marginBottom: '1px',  // Make space for the height of the pseudo-element
    '::after': {
      content: '""',  // This is necessary for the pseudo-element to be displayed
      position: 'absolute',  
      bottom: '0',
      left: '0',
      width: '100%',
      height: '1px',  
      backgroundColor: 'white',
    }
  };  
  
  return (
    <div style={containerStyle}>
      <div style={leftContainerStyle}>
        <div style={formStyle}>
          <h1>Game Selection</h1>
          <div>
            <label>Game Mode: </label>
            <select
              value={gameMode}
              onChange={(e) => setGameMode(e.target.value)}
            >
              <option value="Human">Human vs Human</option>
              <option value="Computer">Human vs Computer</option>
            </select>
          </div>
          <div>
            <label>Role Selection: </label>
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="attacker">Attacker</option>
              <option value="defender">Defender</option>
            </select>
          </div>
          <div>
            <label>Room ID: </label>
            <input value={roomId} onChange={(e) => setRoomId(e.target.value)} />
          </div>
          <div>
            <p> </p>
          </div>
          <div>
            <button style={buttonStyle} onClick={createGame}>
              Create Game
            </button>
            <button style={buttonStyle} onClick={joinGame}>
              Join Game
            </button>
          </div>
        </div>
      </div>
      
      <div style={rightContainerStyle}>
        <div style={tutorialContainerStyle}>
          <h2>Game Tutorial</h2>
          <button style={activeQuestion === 0 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(0)}>
            Q: How to play this game as an attacker
          </button>
          <Collapse isOpened={activeQuestion === 0}>
            <div>
              <p>As an attacker, you only see part of a simulated network at the beginning of the game, with each node representing a host on the network. </p>
              <img src={pngq1p1} alt="Game guide"  style={{ maxWidth: '350px', width: '100%', height: 'auto' }} />
              <p>You need to attack these nodes one by one within the specified time, and finally find the target nodes (white color). </p>
              <img src={pngq1p2} alt="Game guide"  style={{ maxWidth: '500px', width: '100%', height: 'auto' }} />
              <p>There are 3 attacker operations to attack a node: scan port, exploit vulnerabilities, brute force. And you can scan its neighbor after compromising a host.</p>
              <img src={pngq1p3} alt="Game guide"  style={{ maxWidth: '500px', width: '100%', height: 'auto' }} />
              <p>After comprmise one of the target nodes, attacker can win.</p>
              <img src={pngq1p4} alt="Game guide"  style={{ maxWidth: '400px', width: '100%', height: 'auto' }} />
            </div>
          </Collapse>
          <button style={activeQuestion === 1 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(1)}>
            Q: How to play this game as a defender
          </button>
          <Collapse isOpened={activeQuestion === 1}>
            <div>
              <p>As a defender, you can see the whole network at the beginning of the game. The nodes in layer 1,2,3,4 are green, blue, yellow, purple. And the target nodes for attacker are white. </p>
              <img src={pngq2p1} alt="Game guide"  style={{ maxWidth: '450px', width: '100%', height: 'auto' }} />
              <p>You can see the attacker's behavior in real time. The node turns red means the host on it is compromised. </p>
              <img src={pngq2p2} alt="Game guide"  style={{ maxWidth: '450px', width: '100%', height: 'auto' }} />
              <p>You can apply 4 different MTD operations to different nodes according to the attacker's behavior in real time: IP shuffling, topological shuffling, OS diversity, service diversity. </p>
              <img src={pngq2p3} alt="Game guide"  style={{ maxWidth: '500px', width: '100%', height: 'auto' }} />
              <p>As long as the target node is not compromised within the specified time, defender can win.</p>
              <img src={pngq2p4} alt="Game guide"  style={{ maxWidth: '400px', width: '100%', height: 'auto' }} />
            </div>
          </Collapse>
        </div>
      </div>
      
    </div>
  );
};

export default GameSelection;
