export const Message = ({ message }) => {
  // Handle join_room and error types
  if (message.type === 'join_room' || message.type === 'error') {
    return <p>{message.message.details.type} - {message.message.details.msg}</p>;
  }
  
  // Handle move type
  if (message.type === 'move' && message.details) {
    if (message.details.type === 'success') {
      return <p>Latitude: {message.details.msg.lat}, Longitude: {message.details.msg.long}</p>;
    } else {
      // Handle any other types within 'move' or simply return a default message
      return <p>{message.details.type}</p>;
    }
  }
  
  return <p>Invalid message format</p>;
};
