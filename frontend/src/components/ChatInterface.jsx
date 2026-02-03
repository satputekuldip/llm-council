import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Stage1 from './Stage1';
import Stage2 from './Stage2';
import Stage3 from './Stage3';
import './ChatInterface.css';

export default function ChatInterface({
  conversation,
  onSendMessage,
  isLoading,
  personas = [],
}) {
  const [input, setInput] = useState('');
  const [subject, setSubject] = useState('');
  const [selectedPersonaIds, setSelectedPersonaIds] = useState([]);
  const [showPersonaDropdown, setShowPersonaDropdown] = useState(false);
  const messagesEndRef = useRef(null);
  const dropdownRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowPersonaDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      const personaIds = selectedPersonaIds.filter((id) => id && id.trim());
      onSendMessage(input, personaIds.length > 0 ? personaIds : null, subject.trim() || null);
      setInput('');
      setSubject('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (!conversation) {
    return (
      <div className="chat-interface">
        <div className="empty-state">
          <h2>Welcome to LLM Council</h2>
          <p>Create a new conversation to get started</p>
        </div>
      </div>
    );
  }

  const validPersonaIds = selectedPersonaIds.filter((id) => id && id.trim());
  const selectedPersonas = validPersonaIds
    .map((id) => personas.find((p) => p.id === id))
    .filter(Boolean);
  const personaLabel = selectedPersonas.length > 0
    ? selectedPersonas.map((p) => p.name).join(', ')
    : null;

  const togglePersona = (personaId) => {
    const idx = selectedPersonaIds.indexOf(personaId);
    if (idx >= 0) {
      setSelectedPersonaIds((prev) => prev.filter((_, i) => i !== idx));
    } else {
      setSelectedPersonaIds((prev) => [...prev, personaId]);
    }
  };

  const isEmpty = conversation.messages.length === 0;

  return (
    <div className="chat-interface">
      <div className="messages-container">
        {isEmpty ? (
          <div className="empty-state empty-state-centered">
            <h2 className="empty-state-title">
              Let&apos;s <span className="highlight">Debate</span> together
            </h2>
            <p className="empty-state-subtitle">Add personas, set a subject, and ask your question</p>
          </div>
        ) : (
          conversation.messages.map((msg, index) => (
            <div key={index} className="message-group">
              {msg.role === 'user' ? (
                <div className="user-message">
                  <div className="message-label">You</div>
                  <div className="message-content">
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="assistant-message">
                  <div className="message-label">LLM Council</div>

                  {msg.loading?.stage1 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 1: Collecting individual responses...</span>
                    </div>
                  )}
                  {msg.stage1 && <Stage1 responses={msg.stage1} />}

                  {msg.loading?.stage2 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 2: Peer rankings...</span>
                    </div>
                  )}
                  {msg.stage2 && (
                    <Stage2
                      rankings={msg.stage2}
                      labelToModel={msg.metadata?.label_to_model}
                      aggregateRankings={msg.metadata?.aggregate_rankings}
                    />
                  )}

                  {msg.loading?.stage3 && (
                    <div className="stage-loading">
                      <div className="spinner"></div>
                      <span>Running Stage 3: Final synthesis...</span>
                    </div>
                  )}
                  {msg.stage3 && <Stage3 finalResponse={msg.stage3} />}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Consulting the council...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {conversation && (
        <div className="input-area">
          <div className="input-bar" ref={dropdownRef}>
            <div className="input-bar-inner">
              <div className="persona-trigger-wrap">
                <button
                  type="button"
                  className="persona-trigger"
                  onClick={() => setShowPersonaDropdown(!showPersonaDropdown)}
                  title="Select personas"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                  <span className="persona-trigger-text">
                    {personaLabel || 'Add personas…'}
                  </span>
                  {validPersonaIds.length > 0 && (
                    <span className="persona-count">{validPersonaIds.length}</span>
                  )}
                </button>
                {showPersonaDropdown && (
                  <div className="persona-dropdown">
                    <div className="persona-dropdown-header">
                      <span>Personas {validPersonaIds.length}/{personas.length}</span>
                      <span className="persona-dropdown-hint">Add perspectives</span>
                    </div>
                    <div className="persona-dropdown-list">
                      {personas.map((p) => {
                        const isSelected = validPersonaIds.includes(p.id);
                        return (
                          <button
                            key={p.id}
                            type="button"
                            className={`persona-dropdown-item ${isSelected ? 'selected' : ''}`}
                            onClick={() => togglePersona(p.id)}
                          >
                            <span className="persona-check">{isSelected ? '✓' : ''}</span>
                            <span className="persona-initial">{p.name?.[0] || '?'}</span>
                            <div className="persona-info">
                              <span className="persona-name">{p.name}</span>
                              {p.description && (
                                <span className="persona-desc">{p.description}</span>
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
              <div className="input-top-row">
                <input
                  type="text"
                  className="subject-inline"
                  placeholder="Subject"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <form className="input-form-inline" onSubmit={handleSubmit}>
                <textarea
                  className="message-input-inline"
                  placeholder={personaLabel ? `Ask ${personaLabel}…` : 'Ask anything…'}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isLoading}
                  rows={1}
                />
                <button
                  type="submit"
                  className="send-btn-inline"
                  disabled={!input.trim() || isLoading}
                  title="Send"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
