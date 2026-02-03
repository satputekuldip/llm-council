import { useState, useEffect } from 'react';
import './PersonaForm.css';

function parseModel(modelStr) {
  if (!modelStr || !modelStr.includes('/')) return { provider: '', model: '' };
  const [provider, ...rest] = modelStr.split('/');
  return { provider, model: rest.join('/') };
}

function formatModel(provider, model) {
  if (!provider || !model) return null;
  if (provider === 'openrouter') return model;
  return `${provider}/${model}`;
}

export default function PersonaForm({
  persona = null,
  onSubmit,
  onCancel,
  providersModels = {},
}) {
  const [name, setName] = useState(persona?.name ?? '');
  const [prompt, setPrompt] = useState(persona?.prompt ?? '');
  const [provider, setProvider] = useState('');
  const [model, setModel] = useState('');

  const providers = Object.keys(providersModels);
  const modelsForProvider = provider ? (providersModels[provider] || []) : [];

  useEffect(() => {
    if (persona?.model) {
      const isOpenRouter = providersModels.openrouter?.includes(persona.model);
      if (isOpenRouter) {
        setProvider('openrouter');
        setModel(persona.model);
      } else {
        const { provider: p, model: m } = parseModel(persona.model);
        setProvider(p);
        setModel(m);
      }
    } else {
      setProvider('');
      setModel('');
    }
    if (persona) {
      setName(persona.name);
      setPrompt(persona.prompt);
    } else {
      setName('');
      setPrompt('');
    }
  }, [persona]);

  useEffect(() => {
    if (provider && !modelsForProvider.includes(model)) {
      setModel(modelsForProvider[0] || '');
    }
  }, [provider]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const fullModel = formatModel(provider, model);
    if (!fullModel) {
      return;
    }
    onSubmit({ name, prompt, model: fullModel });
  };

  const canSubmit = name.trim() && prompt.trim() && provider && model;

  return (
    <form className="persona-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="persona-name">Name</label>
        <input
          id="persona-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Skeptical Scientist"
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="persona-prompt">System Prompt</label>
        <textarea
          id="persona-prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="You are a skeptical scientist who demands evidence..."
          rows={5}
          required
        />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="persona-provider">Provider</label>
          <select
            id="persona-provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            required
          >
            <option value="">Select provider</option>
            {providers.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="persona-model">Model</label>
          <select
            id="persona-model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            required
            disabled={!provider}
          >
            <option value="">Select model</option>
            {modelsForProvider.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="form-actions">
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn-primary" disabled={!canSubmit}>
          {persona ? 'Update' : 'Create'} Persona
        </button>
      </div>
    </form>
  );
}
