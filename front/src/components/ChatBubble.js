import React from 'react';
import './ChatBubble.css';

const ChatBubble = ({ type, text, time }) => {
  const formattedTime = new Date(time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return (
    <div className={`bubble ${type}`}>
      <div className="message">{text}</div>
      <div className="timestamp">{formattedTime}</div>
    </div>
  );
};

export default ChatBubble;
