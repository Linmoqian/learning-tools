import { useState, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, Play, CheckCircle, AlertCircle, Loader2, Copy, Brain,
  ChevronDown, ChevronRight, Settings, WifiOff,
} from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { useStore } from '../lib/store';
import {
  type AgentType, type AIProvider, type AgentResult, type ApiKeyStatus,
  AGENT_TYPES, AGENT_LABELS, AGENT_DESCRIPTIONS,
  PROVIDER_LABELS, PROVIDER_MODELS, DEFAULT_MODELS,
} from '../../../agent/types';
import { useKnowledgeBase } from '../lib/knowledge';

type Status = 'idle' | 'loading' | 'success' | 'error';

interface ThinkingContent {
  content: string;
  expanded: boolean;
}

export default function AgentPage() {
  const navigate = useNavigate();
  const { data } = useStore();
  const { notes, knowledgePoints } = useKnowledgeBase();

  const [agentType, setAgentType] = useState<AgentType>('note_organizer');
  const [selectedNoteId, setSelectedNoteId] = useState<string>('');
  const [provider, setProvider] = useState<AIProvider>('claude');
  const [model, setModel] = useState(DEFAULT_MODELS.claude);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');

  // Streaming state
  const [streamingContent, setStreamingContent] = useState('');
  const [thinking, setThinking] = useState<ThinkingContent>({ content: '', expanded: false });
  const [hasThinking, setHasThinking] = useState(false);
  const [keyStatus, setKeyStatus] = useState<ApiKeyStatus>({ claude: false, openai: false });

  const streamContentRef = useRef('');
  const thinkingRef = useRef('');
  const isMounted = useRef(true);

  const isQa = agentType === 'knowledge_qa';
  const selectedNote = notes.find(n => n.id === selectedNoteId);

  // API key status: check both stored keys and settings
  const hasSettingsKey = !!data.settings.llm.apiKey;

  // Load stored key status from Rust backend
  useEffect(() => {
    invoke<ApiKeyStatus>('get_api_key_status')
      .then(setKeyStatus)
      .catch(() => {});
  }, []);

  const effectiveHasApiKey = provider === 'claude'
    ? (keyStatus.claude || hasSettingsKey)
    : (keyStatus.openai || hasSettingsKey);

  useEffect(() => {
    return () => { isMounted.current = false; };
  }, []);

  const buildQaContext = useCallback((q: string): string => {
    const query = q.toLowerCase();
    const matchedNotes = notes.filter(n =>
      n.title.toLowerCase().includes(query) || n.content.toLowerCase().includes(query)
    );
    const matchedKps = knowledgePoints.filter(kp =>
      kp.name.toLowerCase().includes(query) || kp.description.toLowerCase().includes(query)
    );

    const parts: string[] = [];

    if (matchedNotes.length > 0) {
      parts.push('## 相关笔记');
      matchedNotes.slice(0, 5).forEach(n => {
        parts.push(`- [${n.subject}] ${n.title}：${n.content.slice(0, 300)}`);
      });
    }

    if (matchedKps.length > 0) {
      parts.push('## 相关知识点');
      matchedKps.slice(0, 5).forEach(kp => {
        parts.push(`- [${kp.subject}] ${kp.name}：${kp.description}`);
      });
    }

    const context = parts.join('\n\n');
    if (!context) {
      return `用户问题：${q}\n\n（知识库中未找到与问题相关的内容）`;
    }
    return `以下是与问题相关的知识库内容：\n\n${context}\n\n用户问题：${q}`;
  }, [notes, knowledgePoints]);

  const handleRun = useCallback(async () => {
    if (isQa ? !question.trim() : !selectedNote) return;
    if (!effectiveHasApiKey) return;

    setStatus('loading');
    setResult(null);
    setError('');
    setStreamingContent('');
    setThinking({ content: '', expanded: false });
    setHasThinking(false);
    streamContentRef.current = '';
    thinkingRef.current = '';

    const noteContent = isQa ? buildQaContext(question) : selectedNote!.content;

    // Set up event listeners before invoke
    const unlisteners: Array<() => void> = [];

    try {
      const unlistenToken = await listen<{ token: string }>('agent-token', (event) => {
        if (!isMounted.current) return;
        streamContentRef.current += event.payload.token;
        setStreamingContent(streamContentRef.current);
      });
      unlisteners.push(unlistenToken);

      const unlistenThinking = await listen<{ token: string }>('agent-thinking', (event) => {
        if (!isMounted.current) return;
        thinkingRef.current += event.payload.token;
        setThinking(prev => ({ ...prev, content: thinkingRef.current }));
        setHasThinking(true);
      });
      unlisteners.push(unlistenThinking);

      const unlistenDone = await listen<{ content: string; model: string; provider: string }>('agent-done', (event) => {
        if (!isMounted.current) return;
        setResult({
          content: event.payload.content,
          model: event.payload.model,
          provider: event.payload.provider as AIProvider,
        });
        setStatus('success');
      });
      unlisteners.push(unlistenDone);

      const unlistenError = await listen<{ message: string }>('agent-error', (event) => {
        if (!isMounted.current) return;
        setError(event.payload.message);
        setStatus('error');
      });
      unlisteners.push(unlistenError);

      // Start streaming
      await invoke('run_agent_stream', {
        request: {
          agentType,
          noteContent,
          provider,
          model,
        },
      });
    } catch (e) {
      if (isMounted.current) {
        setError(typeof e === 'string' ? e : '运行 Agent 失败');
        setStatus('error');
      }
    } finally {
      unlisteners.forEach(fn => fn());
    }
  }, [agentType, isQa, question, selectedNote, provider, model, buildQaContext, effectiveHasApiKey]);

  const handleCopyResult = useCallback(() => {
    if (result?.content) {
      navigator.clipboard.writeText(result.content);
    }
  }, [result]);

  const isRunDisabled = (isQa ? !question.trim() : !selectedNote) || status === 'loading' || !effectiveHasApiKey;

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Brain size={24} color="var(--gold)" />
          <span className="gradient-text">AI Agent</span>
        </h1>
        <p className="page-subtitle">使用 AI 分析笔记、提取知识、回答问题</p>
      </div>

      {/* API Key Status */}
      <div
        className="glass"
        style={{
          padding: '12px 16px', borderRadius: 10, marginBottom: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          border: `1px solid ${effectiveHasApiKey ? 'rgba(39,174,96,0.2)' : 'rgba(231,76,60,0.2)'}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {effectiveHasApiKey ? (
            <CheckCircle size={18} color="#27ae60" />
          ) : (
            <WifiOff size={18} color="#e74c3c" />
          )}
          <span style={{ fontSize: 13, color: effectiveHasApiKey ? '#27ae60' : '#e74c3c', fontWeight: 600 }}>
            {effectiveHasApiKey
              ? `${PROVIDER_LABELS[provider]} API 已配置`
              : `${PROVIDER_LABELS[provider]} API 未配置`}
          </span>
          {!effectiveHasApiKey && (
            <span style={{ fontSize: 12, color: '#a8a0b8' }}>
              — 请先配置 API Key 后使用
            </span>
          )}
        </div>
        <button
          onClick={() => navigate('/settings')}
          style={{
            padding: '6px 14px', borderRadius: 6, border: '1px solid rgba(240,192,64,0.25)',
            background: 'rgba(240,192,64,0.08)', color: '#f0c040',
            fontSize: 12, fontWeight: 600, cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          <Settings size={14} />
          去设置配置
        </button>
      </div>

      {/* Control area */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        {/* Agent selector */}
        <div className="glass" style={{ padding: 12, borderRadius: 10, flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>选择 Agent</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {AGENT_TYPES.map(at => (
              <button
                key={at}
                onClick={() => { setAgentType(at); setStatus('idle'); setResult(null); }}
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

        {/* Input area */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1, minWidth: 200 }}>
          {isQa ? (
            <div className="glass" style={{ padding: 12, borderRadius: 10 }}>
              <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>输入你的问题</div>
              <textarea
                value={question}
                onChange={e => { setQuestion(e.target.value); setStatus('idle'); setResult(null); }}
                placeholder="例如：什么是数列的极限？"
                rows={4}
                style={{
                  width: '100%', padding: '8px 12px', borderRadius: 6, resize: 'vertical',
                  border: '1px solid rgba(255,255,255,0.08)',
                  background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                  fontSize: 12, outline: 'none', fontFamily: 'inherit',
                }}
              />
            </div>
          ) : (
            <div className="glass" style={{ padding: 12, borderRadius: 10 }}>
              <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>选择笔记</div>
              <select
                value={selectedNoteId}
                onChange={e => { setSelectedNoteId(e.target.value); setStatus('idle'); setResult(null); }}
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
          )}

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
        disabled={isRunDisabled}
        style={{
          padding: '12px 24px', borderRadius: 10, border: 'none',
          background: status === 'loading'
            ? 'rgba(240,192,64,0.3)'
            : 'linear-gradient(135deg, #f0c040, #c99f2e)',
          color: status === 'loading' ? '#a8a0b8' : '#0a0e1a',
          fontSize: 14, fontWeight: 700,
          cursor: isRunDisabled ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          opacity: isRunDisabled ? 0.5 : 1,
          marginBottom: 16,
        }}
      >
        {status === 'loading' ? (
          <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> AI 思考中...</>
        ) : (
          <><Play size={18} /> 运行 Agent</>
        )}
      </button>

      {/* Thinking process (collapsible) */}
      <AnimatePresence>
        {(status === 'loading' || (status === 'success' && hasThinking)) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="glass"
            style={{
              padding: 0, borderRadius: 10, marginBottom: 12,
              border: '1px solid rgba(240,192,64,0.12)',
              overflow: 'hidden',
            }}
          >
            <button
              onClick={() => setThinking(prev => ({ ...prev, expanded: !prev.expanded }))}
              style={{
                width: '100%', padding: '10px 16px',
                display: 'flex', alignItems: 'center', gap: 8,
                background: 'rgba(240,192,64,0.04)',
                border: 'none', cursor: 'pointer', color: '#f0c040',
                fontSize: 12, fontWeight: 600,
              }}
            >
              {thinking.expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <Brain size={15} />
              <span>思考过程</span>
              {status === 'loading' && (
                <Loader2 size={12} style={{ animation: 'spin 1s linear infinite', marginLeft: 'auto' }} />
              )}
              {!thinking.expanded && thinking.content && (
                <span style={{
                  marginLeft: 'auto', fontSize: 11, color: '#6b6480', overflow: 'hidden',
                  textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200,
                }}>
                  {thinking.content.slice(0, 60)}…
                </span>
              )}
            </button>
            <AnimatePresence>
              {thinking.expanded && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  style={{ overflow: 'hidden' }}
                >
                  <div style={{
                    padding: '8px 16px 16px',
                    fontSize: 12, lineHeight: 1.7,
                    color: '#a8a0b8',
                    fontStyle: 'italic',
                    maxHeight: 200, overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    fontFamily: '"Fira Code", monospace',
                  }}>
                    {thinking.content || (status === 'loading' ? 'AI 正在思考中...' : '')}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Output area */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Streaming output */}
        <AnimatePresence mode="wait">
          {status === 'loading' && (
            <motion.div
              key="streaming"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="glass"
              style={{
                flex: 1, padding: 20, borderRadius: 12,
                display: 'flex', flexDirection: 'column', overflow: 'hidden',
                border: '1px solid rgba(240,192,64,0.1)',
              }}
            >
              <div style={{
                fontSize: 11, color: '#6b6480', marginBottom: 12,
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
                <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
                正在生成...
              </div>
              <div
                style={{
                  flex: 1, overflow: 'auto', fontSize: 13, lineHeight: 1.7,
                  color: '#d0c8d8', whiteSpace: 'pre-wrap',
                  fontFamily: '"Fira Code", monospace',
                }}
              >
                {streamingContent || (
                  <span style={{ color: '#6b6480', fontStyle: 'italic' }}>
                    等待 AI 响应...
                  </span>
                )}
              </div>
            </motion.div>
          )}

          {status === 'success' && result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass"
              style={{
                flex: 1, padding: 20, borderRadius: 12,
                display: 'flex', flexDirection: 'column', overflow: 'hidden',
              }}
            >
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                alignItems: 'center', marginBottom: 12, flexShrink: 0,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <CheckCircle size={16} color="#27ae60" />
                  <span style={{ fontSize: 13, color: '#27ae60', fontWeight: 600 }}>
                    分析完成
                  </span>
                  <span style={{ fontSize: 11, color: '#6b6480' }}>
                    ({result.provider} / {result.model})
                  </span>
                </div>
                <button
                  onClick={handleCopyResult}
                  style={{
                    padding: '6px', borderRadius: 6,
                    border: '1px solid rgba(255,255,255,0.08)',
                    background: 'rgba(255,255,255,0.04)', color: '#a8a0b8',
                    cursor: 'pointer', display: 'flex', alignItems: 'center',
                  }}
                  title="复制结果"
                >
                  <Copy size={14} />
                </button>
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
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 12,
                color: '#6b6480',
              }}
            >
              <Sparkles size={40} opacity={0.3} />
              <div style={{ fontSize: 13 }}>
                {isQa
                  ? '输入问题后开始基于知识库回答'
                  : '选择笔记和 Agent 后开始分析'}
              </div>
              {!effectiveHasApiKey && (
                <div style={{
                  marginTop: 8, padding: '10px 18px', borderRadius: 8,
                  background: 'rgba(231,76,60,0.06)',
                  border: '1px solid rgba(231,76,60,0.15)',
                  display: 'flex', alignItems: 'center', gap: 8,
                  fontSize: 12, color: '#e74c3c',
                }}>
                  <AlertCircle size={14} />
                  API Key 未配置，请先在设置中配置
                  <button
                    onClick={() => navigate('/settings')}
                    style={{
                      padding: '4px 10px', borderRadius: 4,
                      border: '1px solid rgba(231,76,60,0.3)',
                      background: 'rgba(231,76,60,0.1)',
                      color: '#e74c3c', fontSize: 11, cursor: 'pointer',
                      fontWeight: 600,
                    }}
                  >
                    去设置
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {status === 'error' && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass"
              style={{
                padding: 16, borderRadius: 10,
                border: '1px solid rgba(231,76,60,0.2)',
                background: 'rgba(231,76,60,0.06)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <AlertCircle size={18} color="#e74c3c" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontSize: 12, color: '#e74c3c', fontWeight: 600, marginBottom: 4 }}>
                    运行失败
                  </div>
                  <div style={{ fontSize: 12, color: '#a8a0b8', whiteSpace: 'pre-wrap' }}>{error}</div>
                  <button
                    onClick={handleRun}
                    style={{
                      marginTop: 8, padding: '4px 12px', borderRadius: 6,
                      border: '1px solid rgba(231,76,60,0.3)',
                      background: 'none', color: '#e74c3c',
                      fontSize: 11, cursor: 'pointer',
                    }}
                  >
                    重试
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
