import React, { useState } from 'react';

import { Message } from './Message';

import useSocket from './hooks/useSocket';





export const Chat = () => {
  const [token, setToken] = useState('');
  const [roomId, setRoomId] = useState('');

  const [lat, setLat] = useState(''); 
  const [long, setLong] = useState('');
  
  const { isConnected, messages, joinRoom, handleLeaveRoom, handleSendLocation  } = useSocket(token);


  const onSendLocation = () => {
    if (lat && long) {
      handleSendLocation(parseFloat(lat), parseFloat(long), roomId);
      setLat(''); 
      setLong(''); 
    }
  };

  const joinTheRoom = (e) => {
    e.preventDefault();
    joinRoom(roomId);
}

  return (
    <>
      <h2>status: {isConnected ? 'connected' : 'disconnected'}</h2>
      <div
        style={{
          height: '500px',
          overflowY: 'scroll',
          border: 'solid black 1px',
          padding: '10px',
          marginTop: '15px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {messages.map((message, index) => (
          <Message message={message} key={index} />
        ))}
      </div>
      <input
        type={'text'}
        id='latitude'
        placeholder="Enter Latitude"
        value={lat}
        onChange={(event) => {
          setLat(event.target.value);
        }}
      ></input>
      <input
        type={'text'}
        id='longitude'
        placeholder="Enter Longitude"
        value={long}
        onChange={(event) => {
          setLong(event.target.value);
        }}
      ></input>
      <button
        onClick={onSendLocation}
      >
        Send Coordinates
      </button>
      <input
        type="text"
        id="room"
        placeholder="Enter room number"
        value={roomId}
        onChange={(event) => setRoomId(event.target.value)}
      />
      <button onClick={joinTheRoom}>
        Join Room
      </button>
      <button onClick={() => handleLeaveRoom(roomId)}>
        Leave Room
      </button>
      <input
        type="text"
        id="token"
        placeholder="Enter Token"
        value={token}
        onChange={(event) => setToken(event.target.value)}
      />
    </>
  );
};
