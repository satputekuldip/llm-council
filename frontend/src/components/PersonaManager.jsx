import { useState, useEffect } from 'react';
import { api } from '../api';
import PersonaForm from './PersonaForm';
import Modal from './Modal';
import './PersonaManager.css';

export default function PersonaManager({ onPersonasChange, providersModels = {} }) {
  const [personas, setPersonas] = useState([]);
  const [editingPersona, setEditingPersona] = useState(null);
  const [showFormModal, setShowFormModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadPersonas = async () => {
    try {
      setLoading(true);
      const list = await api.listPersonas();
      setPersonas(list);
      setError(null);
      onPersonasChange?.(list);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPersonas();
  }, []);

  const handleCreate = async (data) => {
    try {
      await api.createPersona(data);
      await loadPersonas();
      setShowFormModal(false);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleUpdate = async (data) => {
    try {
      await api.updatePersona(editingPersona.id, data);
      await loadPersonas();
      setEditingPersona(null);
      setShowFormModal(false);
    } catch (e) {
      setError(e.message);
    }
  };

  const closeModal = () => {
    setShowFormModal(false);
    setEditingPersona(null);
  };

  const handleDelete = async (personaId) => {
    if (!window.confirm('Delete this persona?')) return;
    try {
      await api.deletePersona(personaId);
      await loadPersonas();
      if (editingPersona?.id === personaId) {
        setEditingPersona(null);
        setShowFormModal(false);
      }
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="persona-manager">
      <div className="persona-manager-header">
        <h3>Personas</h3>
        <button
          className="add-persona-btn"
          onClick={() => {
            setEditingPersona(null);
            setShowFormModal(true);
          }}
        >
          + Add
        </button>
      </div>

      {error && (
        <div className="persona-manager-error">{error}</div>
      )}

      {loading ? (
        <div className="persona-manager-loading">Loading...</div>
      ) : (
        <div className="persona-list">
          {personas.length === 0 ? (
            <div className="no-personas">No personas yet. Add one to assign to council members.</div>
          ) : (
            personas.map((p) => (
              <div key={p.id} className="persona-item">
                <div className="persona-item-info">
                  <div className="persona-item-name">{p.name}</div>
                  {p.model && (
                    <div className="persona-item-model">{p.model}</div>
                  )}
                </div>
                <div className="persona-item-actions">
                  <button
                    className="persona-edit-btn"
                    onClick={() => {
                      setEditingPersona(p);
                      setShowFormModal(true);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="persona-delete-btn"
                    onClick={() => handleDelete(p.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      <Modal
        isOpen={showFormModal}
        onClose={closeModal}
        title={editingPersona ? 'Edit Persona' : 'Add Persona'}
      >
        <PersonaForm
          persona={editingPersona}
          providersModels={providersModels}
          onSubmit={editingPersona ? handleUpdate : handleCreate}
          onCancel={closeModal}
        />
      </Modal>
    </div>
  );
}
