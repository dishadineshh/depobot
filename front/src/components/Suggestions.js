import React from 'react';
import './Suggestions.css';

const Suggestions = ({ onSelect }) => {
  const suggestions = [
    'Show me project updates',
    'Who’s working on X?',
    'Server details'
  ];

  return (
    <div className="suggestion-chips">
      {suggestions.map((text, i) => (
        <button key={i} onClick={() => onSelect(text)}>{text}</button>
      ))}
    </div>
  );
};

export default Suggestions;
