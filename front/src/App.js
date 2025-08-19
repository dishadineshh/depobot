import React, { useState } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import ChatBubble from './components/ChatBubble';
import Suggestions from './components/Suggestions';

function App() {
  const [chat, setChat] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const sendQuestion = async (text) => {
    const q = text || question;
    if (!q.trim()) return;

    const newChat = [...chat, { type: 'user', text: q, time: new Date() }];
    setChat(newChat);
    setQuestion('');
    setLoading(true);

    try {
      const res = await fetch('http://127.0.0.1:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });

      const data = await res.json();
      setChat([...newChat, { type: 'bot', text: data.answer || data.error, time: new Date() }]);
    } catch (error) {
      setChat([...newChat, { type: 'bot', text: 'Error connecting to server.', time: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendQuestion();
    }
  };

  return (
    <div className="app">
      <Sidebar />
      <main className="chat-area">
        <header className="chat-header">
          <h1>Data Depository Agent</h1>
          <span className="search-icon">🔍</span>
        </header>
        <section className="hero">
          Hi! I’m your company’s knowledge companion. Ask me anything about projects, updates, changes, or history – I’ve got it all.
        </section>
        <div className="chat-box">
          {chat.map((msg, idx) => (
            <ChatBubble key={idx} type={msg.type} text={msg.text} time={msg.time} />
          ))}
          {loading && <ChatBubble type="bot" text="Typing..." time={new Date()} />}
        </div>
        <div className="input-bar">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question about your team, projects, or company history…"
          />
          <button onClick={() => sendQuestion()}>Send</button>
        </div>
        <Suggestions onSelect={sendQuestion} />
      </main>
    </div>
  );
}

export default App;
