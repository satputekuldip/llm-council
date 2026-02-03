import { useState } from 'react';
import PersonaManager from './PersonaManager';
import './Sidebar.css';

export default function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  personas,
  onPersonasChange,
  providersModels = {},
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <span className="sidebar-logo">LLM Council</span>
          <button
            type="button"
            className="sidebar-toggle"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand' : 'Collapse'}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
              {collapsed ? (
                <path d="M9 18l6-6-6-6" />
              ) : (
                <path d="M15 18l-6-6 6-6" />
              )}
            </svg>
          </button>
        </div>
        {!collapsed && (
          <button className="new-chat-btn" onClick={onNewConversation}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Chat
          </button>
        )}
      </div>

      {!collapsed && (
        <>
          <div className="sidebar-nav">
            <div className="nav-item nav-item-personas">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              <span>Personas</span>
            </div>
          </div>

          <div className="sidebar-personas-section">
            <PersonaManager
              onPersonasChange={onPersonasChange}
              providersModels={providersModels}
            />
          </div>

          <div className="sidebar-chats">
            <div className="chats-label">CHATS</div>
            {conversations.length === 0 ? (
              <div className="no-conversations">No conversations yet</div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`conversation-item ${
                    conv.id === currentConversationId ? 'active' : ''
                  }`}
                  onClick={() => onSelectConversation(conv.id)}
                >
                  <div className="conversation-title">
                    {conv.title || 'New Conversation'}
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
