import React, { useState, useContext } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { UrlPrefixContext } from '../App';

const GameSelection = () => {
  const prefix = useContext(UrlPrefixContext);
  const [gameMode, setGameMode] = useState("Human");
  const [role, setRole] = useState("attacker");
  const [roomId, setRoomId] = useState("");
  const navigate = useNavigate();

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

  const containerStyle = {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    backgroundColor: "#e5e5e5",
    padding: "2rem",
  };

  const formStyle = {
    backgroundColor: "#ffffff",
    borderRadius: "10px",
    padding: "2rem",
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

  return (
    <div style={containerStyle}>
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
          <button style={buttonStyle} onClick={createGame}>
            Create Game
          </button>
          <button style={buttonStyle} onClick={joinGame}>
            Join Game
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameSelection;
