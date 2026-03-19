import React, { useState } from 'react';
import { useUserContext } from '../../App';
import './Menu.css';

const completionModelMap: Record<string, string> = {
  // Amazon
  "nova-micro": "us.amazon.nova-micro-v1:0",
  "nova-lite": "us.amazon.nova-lite-v1:0",
  "nova-pro": "us.amazon.nova-pro-v1:0",
  "nova-premier": "us.amazon.nova-premier-v1:0",
  // Anthropic
  "claude-haiku-3.5": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
  "claude-sonnet-4": "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "claude-sonnet-4.5": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "claude-opus-4": "us.anthropic.claude-opus-4-1-20250805-v1:0",
  // Meta
  "llama3.3-70b": "us.meta.llama3-3-70b-instruct-v1:0",
  "llama4-scout-17b": "us.meta.llama4-scout-17b-instruct-v1:0",
  "llama4-maverick-17b": "us.meta.llama4-maverick-17b-instruct-v1:0",
  // Mistral
  "mistral-large": "us.mistral.mistral-large-2402-v1:0",
  // DeepSeek
  "deepseek-r1": "us.deepseek.r1-v1:0",
  // Cohere
  "command-r-plus": "us.cohere.command-r-plus-v1:0",
};

const rerankerModelMap: Record<string, string> = {
  "voyage-rerank-2": "voyage/rerank-2",
  "no-rerank": "No rerank",
};

const Menu: React.FC = () => {
  const {
    selectedCompletion, setSelectedCompletion,
    selectedReRanker, setSelectedReRanker,
  } = useUserContext();

  const [showCustomCompletion, setShowCustomCompletion] = useState(false);
  const [customCompletion, setCustomCompletion] = useState('');
  const [showCustomReranker, setShowCustomReranker] = useState(false);
  const [customReranker, setCustomReranker] = useState('');

  // Reverse lookup for select values
  const getCompletionSelectValue = () => {
    for (const [key, val] of Object.entries(completionModelMap)) {
      if (val === selectedCompletion) return key;
    }
    return 'custom';
  };

  const getRerankerSelectValue = () => {
    for (const [key, val] of Object.entries(rerankerModelMap)) {
      if (val === selectedReRanker) return key;
    }
    return 'custom';
  };

  const handleCompletionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === 'custom') {
      setShowCustomCompletion(true);
    } else {
      setShowCustomCompletion(false);
      setSelectedCompletion(completionModelMap[val]);
    }
  };

  const handleRerankerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === 'custom') {
      setShowCustomReranker(true);
    } else {
      setShowCustomReranker(false);
      setSelectedReRanker(rerankerModelMap[val]);
    }
  };

  return (
    <div className="menu-nav">
      {/* Reranker Dropdown */}
      <div className="dropdown">
        <label className="dropdown-label">Reranker</label>
        {!showCustomReranker ? (
          <select
            className="form-select"
            value={getRerankerSelectValue()}
            onChange={handleRerankerChange}
            aria-label="Select reranker"
          >
            <option value="voyage-rerank-2">Voyage AI Rerank</option>
            <option value="no-rerank">No Reranking</option>
            <option value="custom">Custom...</option>
          </select>
        ) : (
          <div className="custom-model-input">
            <input
              type="text"
              className="form-input"
              placeholder="provider/model"
              value={customReranker}
              onChange={(e) => setCustomReranker(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && customReranker.trim()) {
                  setSelectedReRanker(customReranker.trim());
                }
              }}
              autoFocus
            />
            <div className="custom-model-buttons">
              <button className="custom-model-btn confirm-btn" onClick={() => {
                if (customReranker.trim()) setSelectedReRanker(customReranker.trim());
              }}>&#10003;</button>
              <button className="custom-model-btn cancel-btn" onClick={() => {
                setShowCustomReranker(false);
                setCustomReranker('');
                setSelectedReRanker('voyage/rerank-2');
              }}>&#10005;</button>
            </div>
          </div>
        )}
      </div>

      {/* Completion Dropdown */}
      <div className="dropdown">
        <label className="dropdown-label">Completion</label>
        {!showCustomCompletion ? (
          <select
            className="form-select"
            value={getCompletionSelectValue()}
            onChange={handleCompletionChange}
            aria-label="Select completion model"
          >
            <optgroup label="Amazon">
              <option value="nova-micro">Nova Micro</option>
              <option value="nova-lite">Nova Lite</option>
              <option value="nova-pro">Nova Pro</option>
              <option value="nova-premier">Nova Premier</option>
            </optgroup>
            <optgroup label="Anthropic">
              <option value="claude-haiku-3.5">Claude 3.5 Haiku</option>
              <option value="claude-sonnet-4">Claude Sonnet 4</option>
              <option value="claude-sonnet-4.5">Claude Sonnet 4.5</option>
              <option value="claude-opus-4">Claude Opus 4</option>
            </optgroup>
            <optgroup label="Meta">
              <option value="llama3.3-70b">Llama 3.3 70B</option>
              <option value="llama4-scout-17b">Llama 4 Scout 17B</option>
              <option value="llama4-maverick-17b">Llama 4 Maverick 17B</option>
            </optgroup>
            <optgroup label="Other">
              <option value="mistral-large">Mistral Large</option>
              <option value="deepseek-r1">DeepSeek R1</option>
              <option value="command-r-plus">Cohere Command R+</option>
            </optgroup>
            <option value="custom">Custom...</option>
          </select>
        ) : (
          <div className="custom-model-input">
            <input
              type="text"
              className="form-input"
              placeholder="provider/model (e.g., openai/gpt-4)"
              value={customCompletion}
              onChange={(e) => setCustomCompletion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && customCompletion.trim()) {
                  setSelectedCompletion(customCompletion.trim());
                }
              }}
              autoFocus
            />
            <div className="custom-model-buttons">
              <button className="custom-model-btn confirm-btn" onClick={() => {
                if (customCompletion.trim()) setSelectedCompletion(customCompletion.trim());
              }}>&#10003;</button>
              <button className="custom-model-btn cancel-btn" onClick={() => {
                setShowCustomCompletion(false);
                setCustomCompletion('');
                setSelectedCompletion('us.amazon.nova-lite-v1:0');
              }}>&#10005;</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Menu;
