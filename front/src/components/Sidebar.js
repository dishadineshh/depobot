import React from 'react';
import './Sidebar.css';

const Sidebar = () => {
  return (
    <aside className="sidebar">
      <div className="logo">Upload Digital</div>
      <button className="new-chat">+ New Chat</button>
      <div className="chat-history">
        <p className="history-label">Conversation History</p>
        {/* In the future: map conversation list here */}
      </div>
    </aside>
  );
};

export default Sidebar;
