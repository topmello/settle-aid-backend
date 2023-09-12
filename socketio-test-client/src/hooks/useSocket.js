import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

const useSocket = (token) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);

  const handleConnect = () => setIsConnected(true);
  const handleDisconnect = () => setIsConnected(false);
  const handleJoin = (message) => {
    setMessages((prev) => [...prev, { message, type: 'join_room' }]);
  }; 
  const handleMove = (data) => setMessages((prev) => [...prev, { ...data, type: 'move' }]);

  useEffect(() => {
    if (token) {
      const newSocket = io(process.env.REACT_APP_API_URL, {
        path: process.env.REACT_APP_SOCKET_PATH,
        transportOptions: {
          polling: {
            extraHeaders: {
              'Authorization': `Bearer ${token}`
            }
          }
        }
      });

      setSocket(newSocket);
      setIsConnected(newSocket.connected);

      

      newSocket.on('connect', handleConnect);
      newSocket.on('disconnect', handleDisconnect);
      newSocket.on('room_message', handleJoin);
      newSocket.on('move', handleMove);

      return () => {
        newSocket.off('connect', handleConnect);
        newSocket.off('disconnect', handleDisconnect);
        newSocket.off('room_message', handleJoin);
        newSocket.off('move', handleMove);
        newSocket.close();
      };
    }
  }, [token]);

  // Join a room
  const joinRoom = (roomId) => {
    if (socket) {
    socket.emit('join_room', roomId);
    }
  };

  const handleLeaveRoom = (roomId) => {
    if (socket) {
        socket.emit('leave_room', roomId);
    }
};

  const handleSendLocation = (lat, long, roomId) => {
    if (lat && long && socket) {
        socket.emit('move', { lat: parseFloat(lat), long: parseFloat(long), roomId: roomId });

    }
  };

  return { isConnected, messages, joinRoom, handleLeaveRoom, handleSendLocation };
};

export default useSocket;
