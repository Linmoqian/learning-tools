import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, Settings, Play, CheckCircle,
  AlertCircle, Loader2, Copy,
} from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import type { Note } from '../lib/knowledge';
import {
  type AgentType, type AIProvider, type AgentResult, type ApiKeyStatus,
  AGENT_TYPES, AGENT_LABELS, AGENT_DESCRIPTIONS,
  PROVIDER_LABELS, PROVIDER_MODELS, DEFAULT_MODELS,
} from '../../../agent/types';

type Status = 'idle' | 'loading' | 'success' | 'error';

export default function AgentPanel({ notes }: { notes: Note[] }) {
  const [agentType, setAgentType] = useState<AgentType>('note_organizer');
  const [selectedNoteId, setSelectedNoteId] = useState<string>('');
  const [provider, setProvider] = useState<AIProvider>('claude');
  const [model, setModel] = useState(DEFAULT_MODELS.claude);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [claudeKey, setClaudeKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [keyStatus, setKeyStatus] = useState<ApiKeyStatus>({ claude: false, openai: false });

  const selectedNote = notes.find(n => n.id === selectedNoteId);

  // Load API key status
  useEffect(() => {
    invoke<ApiKeyStatus>('get_api_key_status')
      .then(setKeyStatus)
      .catch(() => {});
  }, []);

  const handleRun = useCallback(async () => {
    if (!selectedNote) return;

    setStatus('loading');
    setResult(null);
    setError('');

    try {
      const res = await invoke<AgentResult>('run_agent', {
        request: {
          agentType,
          noteContent: selectedNote.content,
          provider,
          model,
        },
      });
      setResult(res);
      setStatus('success');
    } catch (e) {
      setError(typeof e === 'string' ? e : '运行 Agent 失败');
      setStatus('error');
    }
  }, [agentType, selectedNote, provider, model]);

  const handleSaveKey = useCallback(async (providerName: string, key: string) => {
    try {
      await invoke('save_api_key', { provider: providerName, key });
      setKeyStatus(prev => ({ ...prev, [providerName]: true }));
    } catch (e) {
      setError(typeof e === 'string' ? e : '保存失败');
    }
  }, []);

  const handleCopyResult = useCallback(() => {
    if (result?.content) {
      navigator.clipboard.writeText(result.content);
    }
  }, [result]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, height: '100%' }}>
      {/* API Settings bar */}
      <div className="glass" style={{ padding: '10px 16px', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: '#6b6480' }}>API: </span>
          {(['claude', 'openai'] as const).map(p => (
            <span key={p} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 4,
              background: keyStatus[p] ? 'rgba(39,174,96,0.1)' : 'rgba(231,76,60,0.1)',
              color: keyStatus[p] ? '#27ae60' : '#e74c3c',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: keyStatus[p] ? '#27ae60' : '#e74c3c' }} />
              {PROVIDER_LABELS[p]}
            </span>
          ))}
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          style={{ padding: '6px 12px', borderRadius: 6, border: 'none', background: 'rgba(255,255,255,0.06)', color: '#a8a0b8', fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Settings size={14} />
          配置 API Key
        </button>
      </div>

      {/* Settings panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="glass" style={{ padding: 16, borderRadius: 10, overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, color: '#a8a0b8', marginBottom: 4, display: 'block' }}>Claude API Key</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="password"
                    value={claudeKey}
                    onChange={e => setClaudeKey(e.target.value)}
                    placeholder="sk-ant-..."
                    style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.04)', color: '#f0e8da', fontSize: 12, outline: 'none' }}
                  />
                  <button onClick={() => handleSaveKey('claude', claudeKey)} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: 'rgba(240,192,64,0.15)', color: '#f0c040', fontSize: 12, cursor: 'pointer' }}>保存</button>
                </div>
              </div>
              <div>
                <label style={{ fontSize: 12, color: '#a8a0b8', marginBottom: 4, display: 'block' }}>OpenAI API Key</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="password"
                    value={openaiKey}
                    onChange={e => setOpenaiKey(e.target.value)}
                    placeholder="sk-..."
                    style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.04)', color: '#f0e8da', fontSize: 12, outline: 'none' }}
                  />
                  <button onClick={() => handleSaveKey('openai', openaiKey)} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: 'rgba(240,192,64,0.15)', color: '#f0c040', fontSize: 12, cursor: 'pointer' }}>保存</button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Control row: Agent + Provider + Note */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {/* Agent selector */}
        <div className="glass" style={{ padding: 12, borderRadius: 10, flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>选择 Agent</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {AGENT_TYPES.map(at => (
              <button
                key={at}
                onClick={() => { setAgentType(at); setStatus('idle'); }}
                style={{
                  padding: '8px 12px', borderRadius: 8, textAlign: 'left',
                  background: agentType === at ? 'rgba(240,192,64,0.12)' : 'rgba(255,255,255,0.03)',
                  border: agentType === at ? '1px solid rgba(240,192,64,0.2)' : '1px solid transparent',
                  color: agentType === at ? '#f0c040' : '#a8a0b8',
                  fontSize: 12, cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 2 }}>{AGENT_LABELS[at]}</div>
                <div style={{ fontSize: 10, color: '#6b6480' }}>{AGENT_DESCRIPTIONS[at]}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Note + Provider selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 200 }}>
          {/* Note selector */}
          <div className="glass" style={{ padding: 12, borderRadius: 10 }}>
            <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>选择笔记</div>
            <select
              value={selectedNoteId}
              onChange={e => { setSelectedNoteId(e.target.value); setStatus('idle'); }}
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 6,
                border: '1px solid rgba(255,255,255,0.08)',
                background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                fontSize: 12, outline: 'none',
              }}
            >
              <option value="">-- 请选择笔记 --</option>
              {notes.map(n => (
                <option key={n.id} value={n.id}>
                  [{n.subject}] {n.title}
                </option>
              ))}
            </select>
          </div>

          {/* Provider + Model */}
          <div className="glass" style={{ padding: 12, borderRadius: 10 }}>
            <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>Provider & 模型</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <select
                value={provider}
                onChange={e => {
                  const p = e.target.value as AIProvider;
                  setProvider(p);
                  setModel(DEFAULT_MODELS[p]);
                }}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 6,
                  border: '1px solid rgba(255,255,255,0.08)',
                  background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                  fontSize: 12, outline: 'none',
                }}
              >
                <option value="claude">Claude</option>
                <option value="openai">OpenAI</option>
              </select>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 6,
                  border: '1px solid rgba(255,255,255,0.08)',
                  background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                  fontSize: 12, outline: 'none',
                }}
              >
                {PROVIDER_MODELS[provider].map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={!selectedNote || status === 'loading'}
        style={{
          padding: '12px 24px', borderRadius: 10, border: 'none',
          background: status === 'loading' ? 'rgba(240,192,64,0.3)' : 'linear-gradient(135deg, #f0c040, #c99f2e)',
          color: status === 'loading' ? '#a8a0b8' : '#0a0e1a',
          fontSize: 14, fontWeight: 700, cursor: status === 'loading' ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          opacity: !selectedNote ? 0.5 : 1,
        }}
      >
        {status === 'loading' ? (
          <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> 正在分析...</>
        ) : (
          <><Play size={18} /> 运行 Agent</>
        )}
      </button>

      {/* Error state */}
      <AnimatePresence>
        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="glass"
            style={{
              padding: 16, borderRadius: 10,
              border: '1px solid rgba(231,76,60,0.2)',
              background: 'rgba(231,76,60,0.06)',
              display: 'flex', alignItems: 'flex-start', gap: 10,
            }}
          >
            <AlertCircle size={18} color="#e74c3c" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontSize: 12, color: '#e74c3c', fontWeight: 600, marginBottom: 4 }}>运行失败</div>
              <div style={{ fontSize: 12, color: '#a8a0b8', whiteSpace: 'pre-wrap' }}>{error}</div>
              <button
                onClick={handleRun}
                style={{ marginTop: 8, padding: '4px 12px', borderRadius: 6, border: '1px solid rgba(231,76,60,0.3)', background: 'none', color: '#e74c3c', fontSize: 11, cursor: 'pointer' }}
              >
                重试
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result display */}
      <AnimatePresence mode="wait">
        {status === 'loading' && (
          <motion.div
            key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 12,
              color: '#6b6480',
            }}
          >
            <Loader2 size={32} style={{ animation: 'spin 1s linear infinite' }} />
            <div style={{ fontSize: 13 }}>
              正在使用 {PROVIDER_LABELS[provider]} {model} 处理笔记...
            </div>
          </motion.div>
        )}

        {status === 'success' && result && (
          <motion.div
            key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="glass"
            style={{
              flex: 1, padding: 20, borderRadius: 12,
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle size={16} color="#27ae60" />
                <span style={{ fontSize: 13, color: '#27ae60', fontWeight: 600 }}>分析完成</span>
                <span style={{ fontSize: 11, color: '#6b6480' }}>
                  ({result.provider} / {result.model})
                </span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={handleCopyResult} style={iconBtnStyle} title="复制结果">
                  <Copy size={14} />
                </button>
              </div>
            </div>
            <div
              style={{
                flex: 1, overflow: 'auto', fontSize: 13, lineHeight: 1.7,
                color: '#d0c8d8',
              }}
            >
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0 }}>
                {result.content}
              </pre>
            </div>
          </motion.div>
        )}

        {status === 'idle' && (
          <motion.div
            key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 12,
              color: '#6b6480',
            }}
          >
            <Sparkles size={32} opacity={0.3} />
            <div style={{ fontSize: 13 }}>选择笔记和 Agent 后开始分析</div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

const iconBtnStyle: React.CSSProperties = {
  padding: '6px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)',
  background: 'rgba(255,255,255,0.04)', color: '#a8a0b8',
  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
};
