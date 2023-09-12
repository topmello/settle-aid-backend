export const Message = ({ message }) => {
  if (message.type === 'join_room') return <p>{message.message}</p>;
  if (message.type === 'move') return <p>{`${message.sid}: Latitude: ${message.lat}, Longitude: ${message.long}`}</p>;
};
