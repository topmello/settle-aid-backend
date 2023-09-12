export const Message = ({ message }) => {
  if (message.type === 'join') return <p>{`${message.sid} just joined`}</p>;
  if (message.type === 'move') return <p>{`${message.sid}: Latitude: ${message.lat}, Longitude: ${message.long}`}</p>;
};
