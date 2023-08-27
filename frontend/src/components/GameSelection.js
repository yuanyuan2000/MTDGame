import React, { useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { UrlPrefixContext } from '../App';
import { Collapse } from 'react-collapse';
import backgroundImage from './background.png';
import pngq1p1 from './img/q1p1.png'
import pngq1p2 from './img/q1p2.png'
import pngq1p3 from './img/q1p3.png'
import pngq1p4 from './img/q1p4.png'
import pngq2p1 from './img/q2p1.png'
import pngq2p2 from './img/q2p2.png'
import pngq2p3 from './img/q2p3.png'
import pngq2p4 from './img/q2p4.png'
import pngq3p1 from './img/q3p1.png'
import pngq3p2 from './img/q3p2.png'
import pngq3p3 from './img/q3p3.png'
import pngq4p1 from './img/q4p1.png'
import pngq4p2 from './img/q4p2.png'
import pngq4p3 from './img/q4p3.png'
import pngq4p4 from './img/q4p4.png'
import pngq4p5 from './img/q4p5.png'
import pngq5p1 from './img/q5p1.png'
import pngq5p2 from './img/q5p2.png'
import pngq5p3 from './img/q5p3.png'
import pngq6p1 from './img/q6p1.png'
import pngq6p2 from './img/q6p2.png'
import pngq6p3 from './img/q6p3.png'
import pngq7p1 from './img/q7p1.png'
import pngq7p2 from './img/q7p2.png'
import pngq8p1 from './img/q8p1.png'
import pngq8p2 from './img/q8p2.png'
import pngq9p1 from './img/q9p1.png'
import pngq9p2 from './img/q9p2.png'

const GameSelection = () => {
  const prefix = useContext(UrlPrefixContext);
  const [backgroundLoaded, setBackgroundLoaded] = useState(false);
  const [gameMode, setGameMode] = useState("Human");
  const [role, setRole] = useState("attacker");
  const [roomId, setRoomId] = useState("");
  const navigate = useNavigate();
  const [activeQuestion, setActiveQuestion] = useState(null); // Track the currently open question

  useEffect(() => {
    const img = new Image();
    img.src = backgroundImage;
    img.onload = () => {
      setBackgroundLoaded(true);
    };
  }, []);  // Empty dependencies array ensures useEffect is only run when the component is first mounted

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

  if (!backgroundLoaded) {
    return null;  // If the background image has not been loaded, render nothing
  }
  
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
              <p></p>
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
              <p></p>
            </div>
          </Collapse>
          <button style={activeQuestion === 2 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(2)}>
            Attcker operation: Scan Port
          </button>
          <Collapse isOpened={activeQuestion === 2}>
            <div>
              <p>As an attacker, you can select a node and click the "Scan Port" button, then you will get all accessible port numbers about this node.</p>
              <img src={pngq3p1} alt="Game guide"  style={{ maxWidth: '400px', width: '100%', height: 'auto' }} />
              <p>This step is necessary before exploiting the vulnerabilities. Because you need to use the port number access the services.</p>
              <img src={pngq3p2} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>In addition, this step will try to use some common passwords to compromise. It might be the correct password if you are very lucky.</p>
              <img src={pngq3p3} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>"Scan Port" will consume 5 resources. </p>
            </div>
          </Collapse>
          <button style={activeQuestion === 3 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(3)}>
            Attcker operation: Exploit vulnerability
          </button>
          <Collapse isOpened={activeQuestion === 3}>
            <div>
              <p>As an attacker, you can select a node and click the "Exploit Vuln" button, then it will exploit the vulnerabilities, which may exist on the services running on this host.</p>
              <img src={pngq4p1} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>This action consumes 15 resources and will finish in 3 seconds. If any vulnerability has been exploited, the node will be compromised.</p>
              <img src={pngq4p2} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>Before doing this operation, you should scan port on this node, because accessing the services needs the port number. Otherwise it will fail.</p>
              <img src={pngq4p3} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>However, if any defender operation interrupt this progress, or no vulnerability has been exploited, the node will still keep health.</p>
              <img src={pngq4p4} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>Besides, because every vulnerability depends on a service, if the exploited service on that node is removed by defender, the node will be set back to uncompromised.</p>
              <img src={pngq4p5} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p></p>
            </div>
          </Collapse>
          <button style={activeQuestion === 4 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(4)}>
            Attcker operation: Brute Force
          </button>
          <Collapse isOpened={activeQuestion === 4}>
            <div>
              <p>Brute force is also a very common attack method, which exhausts all possible passwords to attack a host.</p>
              <img src={pngq5p1} alt="Game guide"  style={{ maxWidth: '500px', width: '100%', height: 'auto' }} />
              <p>You just need to select a node and click the "Brute Force" button. It consumes 30 resources and will finish in 5 seconds.</p>
              <img src={pngq5p2} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>It seems that this method take more time and resources, but the node compromised by this method can't be set back to uncompromised. Because if you get the password of the super user on a host, you can do everything on it.</p>
              <p>And the more passwords you get, the easier to successfully brute force.</p>
              <img src={pngq5p3} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p></p>
            </div>
          </Collapse>
          <button style={activeQuestion === 5 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(5)}>
            MTD operation: IP shuffling
          </button>
          <Collapse isOpened={activeQuestion === 5}>
            <div>
              <p>"IP shuffling" is a good MTD operation on network layer, it can interrupt any running attack progress on a host such as brute force.</p>
              <img src={pngq6p1} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>You just need to select the node and click the button. It comsumes 30 resources and works immediately.</p>
              <img src={pngq6p2} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>As a result, it will change the IP of a node and interrupt all attack progress on this node. </p>
              <img src={pngq6p3} alt="Game guide"  style={{ maxWidth: '600px', width: '100%', height: 'auto' }} />
              <p></p>
            </div>
          </Collapse>
          <button style={activeQuestion === 6 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(6)}>
            MTD operation: Topological Shuffling
          </button>
          <Collapse isOpened={activeQuestion === 6}>
            <div>
              <p>"Topological shuffling" is the most terrible thing for the attacker. </p>
              <img src={pngq7p1} alt="Game guide"  style={{ maxWidth: '650px', width: '100%', height: 'auto' }} />
              <p>It comsumes 60 resources. As a result, it will suddenly change the connection of the whole network including the target nodes.</p>
              <img src={pngq7p2} alt="Game guide"  style={{ maxWidth: '650px', width: '100%', height: 'auto' }} />
              <p>However, This action can be used up to two times in a game, because it is too strong.</p>
              <p></p>
            </div>
          </Collapse>
          <button style={activeQuestion === 7 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(7)}>
            MTD operation: OS Diversity
          </button>
          <Collapse isOpened={activeQuestion === 7}>
            <div>
              <p>"OS diversity" can help defender change the OS for all nodes(not include endpoints) at the same time.</p>
              <img src={pngq8p1} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>If the attacker has compromised a node depends on a exploited service, and this service is OS service and it has been changed, then this node can be set back to uncompromised.</p>
              <img src={pngq8p2} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>This operation comsumes 45 resources. Just click the button it will start.</p>
              <p></p>
            </div>
          </Collapse>
          <button style={activeQuestion === 8 ? accordionStyle : accordionStyleWithBorder} onClick={() => toggleAnswer(8)}>
            MTD operation: Service Diversity
          </button>
          <Collapse isOpened={activeQuestion === 8}>
            <div>
              <p>"Service diversity" can help defender change the services for a nodes(can't do at the endpoints).</p>
              <img src={pngq9p1} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>If the attacker has compromised this node depends on a exploited service, and this service has been changed, then this node can be set back to uncompromised.</p>
              <img src={pngq9p2} alt="Game guide"  style={{ maxWidth: '550px', width: '100%', height: 'auto' }} />
              <p>This operation comsumes 15 resources. Just click the button it will start.</p>
              <p></p>
            </div>
          </Collapse>
        </div>
      </div>
      
    </div>
  );
};

export default GameSelection;
