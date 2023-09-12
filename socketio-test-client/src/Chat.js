import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

import { Message } from './Message';


const socket = io(process.env.REACT_APP_API_URL, {
  path: process.env.REACT_APP_SOCKET_PATH,
  transportOptions: {
    polling: {
      extraHeaders: {
        'Authorization': `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InRlc3QiLCJleHAiOjE2OTQ0NzgxNzN9.t9uilH_-7X1aogmc2CAn7uzq2iiG6Rri7vEEmxjWAFw`
      }
    }
  }
});


export const Chat = () => {
  const [isConnected, setIsConnected] = useState(socket.connected);
  const [roomId, setRoomId] = useState('');
  const [messages, setMessages] = useState([]);

  const [lat, setLat] = useState('');  // New state for latitude
  const [long, setLong] = useState('');  // New state for longitude
  
  console.log(socket);
  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected');
      setIsConnected(socket.connected);
    });
    socket.on('your_pin', (pin) => {
      console.log("Your pin is:", pin);
  });
    socket.on('disconnect', () => {
      setIsConnected(socket.connected);
    });
    socket.on('join', (data) => {
      setMessages((prevMessages) => [...prevMessages, { ...data, type: 'join' }]);
    });

    socket.on('move', (data) => {
      console.log("Received 'move' event:", data);
      setMessages((prevMessages) => [...prevMessages, { ...data, type: 'move' }]);
    });

  }, []);

    // Join a room
    const joinRoom = (user_id, pin) => {
      socket.emit('join_room', { roomId: roomId, pin: '1234' });
  };

  const handleLeaveRoom = (roomId) => {
    socket.emit('leave_room', roomId);
    // Optional: Update the UI or state to reflect that the client has left the room
};

  const handleSendMessage = () => {
    if (lat && long) {
        socket.emit('move', { lat: parseFloat(lat), long: parseFloat(long), roomId: roomId });
        setLat(''); // Clear the latitude
        setLong(''); // Clear the longitude
    }
  };

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
        onClick={handleSendMessage}
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
      <button onClick={() => joinRoom(roomId)}>
        Join Room
      </button>
      <button onClick={() => handleLeaveRoom(roomId)}>
        Leave Room
      </button>
    </>
  );
};
