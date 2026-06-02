import { useState, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, Search, Network, BarChart3, ChevronRight,
  FileText, Layers, AlertTriangle, CheckCircle, List, Server, Wifi, Sparkles,
} from 'lucide-react';
import AgentPanel from '../components/AgentPanel';
import KnowledgeGraph from '../components/KnowledgeGraph';
import KnowledgeGraph3D from '../components/KnowledgeGraph3D';
import FileDropZone from '../components/FileDropZone';
import {
  useKnowledgeBase, searchItems, SUBJECTS, SUBJECT_COLORS,
} from '../lib/knowledge';
import { parseFile, fileToNoteInput } from '../lib/fileParser';
import { checkMineruServer, isMineruOnline, convertWithMineru, getImageUrl, setServerUrl } from '../lib/mineruClient';
import { useStore } from '../lib/store';
import type { Note, KnowledgePoint, SubjectStat } from '../lib/knowledge';

type Tab = 'browse' | 'graph' | 'analysis' | 'agent';

function StatCard({ label, value, color, icon }: {
  label: string; value: number | string; color: string; icon: React.ReactNode;
}) {
  return (
    <div
      className="glass"
      style={{
        padding: '16px 20px', borderRadius: 12,
        display: 'flex', alignItems: 'center', gap: 14, minWidth: 140,
        border: `1px solid rgba(255,255,255,0.06)`,
      }}
    >
      <div style={{
        width: 40, height: 40, borderRadius: 10,
        background: `${color}15`, display: 'flex',
        alignItems: 'center', justifyContent: 'center',
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, color: '#f0e8da' }}>{value}</div>
        <div style={{ fontSize: 11, color: '#6b6480' }}>{label}</div>
      </div>
    </div>
  );
}

function SubjectCard({ stat, onClick }: { stat: SubjectStat; onClick: () => void }) {
  const healthPct = stat.linkCount > 0 ? Math.round(stat.validCount / stat.linkCount * 100) : 100;
  const healthColor = healthPct >= 90 ? '#27ae60' : healthPct >= 70 ? '#e67e22' : '#e74c3c';

  return (
    <motion.div
      whileHover={{ y: -3, scale: 1.01 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="glass"
      style={{
        padding: 18, borderRadius: 14, cursor: 'pointer',
        border: `1px solid ${stat.color}20`,
        borderLeft: `3px solid ${stat.color}`,
        display: 'flex', flexDirection: 'column', gap: 10,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: stat.color }}>{stat.name}</div>
        <ChevronRight size={14} color="#6b6480" />
      </div>
      <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
        <span style={{ color: '#a8a0b8' }}>
          <FileText size={12} style={{ marginRight: 3, verticalAlign: -1 }} />
          {stat.noteCount} 笔记
        </span>
        <span style={{ color: '#a8a0b8' }}>
          <Layers size={12} style={{ marginRight: 3, verticalAlign: -1 }} />
          {stat.kpCount} 知识点
        </span>
        <span style={{ color: healthColor }}>
          {stat.linkCount > 0 ? `${healthPct}% 健康` : '无链接'}
        </span>
      </div>
      {stat.linkCount > 0 && (
        <div style={{ height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
          <div style={{
            width: `${healthPct}%`, height: '100%',
            background: `linear-gradient(90deg, ${healthColor}, ${healthColor}88)`,
            borderRadius: 2, transition: 'width 0.5s',
          }} />
        </div>
      )}
    </motion.div>
  );
}

function NoteCard({ note, isUploaded }: { note: Note; isUploaded?: boolean }) {
  const color = SUBJECT_COLORS[note.subject] || '#666';
  const ext = isUploaded ? note.name.split('.').pop()?.toLowerCase() : null;
  const fileExtColors: Record<string, string> = {
    pdf: '#e74c3c', pptx: '#e67e22', docx: '#3498db', md: '#2ecc71',
  };
  const [showImages, setShowImages] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass"
      style={{
        padding: 14, borderRadius: 12,
        border: '1px solid rgba(255,255,255,0.06)',
        borderLeft: `3px solid ${isUploaded ? `${color}88` : color}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        {ext && (
          <span style={{
            fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 3,
            background: `${fileExtColors[ext] || '#a8a0b8'}18`,
            color: fileExtColors[ext] || '#a8a0b8',
            border: `1px solid ${fileExtColors[ext] || '#a8a0b8'}30`,
          }}>
            {ext.toUpperCase()}
          </span>
        )}
        <div style={{ fontSize: 13, fontWeight: 600, color: '#f0e8da' }}>
          {note.title}
        </div>
        {isUploaded && (
          <span style={{ fontSize: 9, color: '#f0c040', marginLeft: 'auto' }}>
            已上传
          </span>
        )}
      </div>
      <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 6, lineHeight: 1.5 }}>
        {note.content.slice(0, 120)}…
      </div>

      {/* Image thumbnails (uploaded notes with MinerU images) */}
      {note.images && note.images.length > 0 && (
        <div style={{ marginBottom: 6 }}>
          <button
            onClick={() => setShowImages(!showImages)}
            style={{
              fontSize: 10, color: '#3498db', background: 'none', border: 'none',
              cursor: 'pointer', padding: 0, fontWeight: 600,
            }}
          >
            {showImages ? '收起图片' : `查看 ${note.images.length} 张图片`}
          </button>
          {showImages && (
            <div style={{ display: 'flex', gap: 6, marginTop: 6, flexWrap: 'wrap' }}>
              {note.images.map((img, i) => (
                <img
                  key={i}
                  src={getImageUrl(img)}
                  alt={`图片 ${i + 1}`}
                  style={{
                    width: 80, height: 60, objectFit: 'cover', borderRadius: 6,
                    border: '1px solid rgba(255,255,255,0.08)',
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {note.wikiLinks.map((link, i) => (
          <span key={i} style={{
            fontSize: 10, padding: '1px 6px', borderRadius: 4,
            background: 'rgba(240,192,64,0.1)', color: '#f0c040',
          }}>
            {link}
          </span>
        ))}
      </div>
    </motion.div>
  );
}

function KnowledgePointCard({ kp }: { kp: KnowledgePoint }) {
  const color = SUBJECT_COLORS[kp.subject] || '#666';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        padding: 14, borderRadius: 12,
        background: `linear-gradient(135deg, ${color}08, transparent)`,
        border: `1px solid ${color}20`,
        borderLeft: `3px solid ${color}`,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: '#f0e8da', marginBottom: 4 }}>
        {kp.name}
      </div>
      <div style={{ fontSize: 11, color: '#6b6480', lineHeight: 1.5 }}>
        {kp.description}
      </div>
      {kp.linkedFrom.length > 0 && (
        <div style={{ fontSize: 10, color: '#a8a0b8', marginTop: 6 }}>
          被 {kp.linkedFrom.length} 篇笔记引用
        </div>
      )}
    </motion.div>
  );
}

function BrowseTab({ notes, knowledgePoints, subjectFilter, setSubjectFilter, uploadedIds }:
  { notes: Note[]; knowledgePoints: KnowledgePoint[]; subjectFilter: string | null; setSubjectFilter: (s: string | null) => void; uploadedIds: Set<string> }) {

  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'all' | 'notes' | 'knowledge'>('all');

  const filteredNotes = notes.filter(n => !subjectFilter || n.subject === subjectFilter);
  const filteredKps = knowledgePoints.filter(k => !subjectFilter || k.subject === subjectFilter);

  const searchResults = searchQuery ? searchItems(filteredNotes, filteredKps, searchQuery) : null;
  const searchedNoteIds = searchResults ? new Set(searchResults.filter(r => r.type === 'note').map(r => r.id)) : null;
  const searchedKpIds = searchResults ? new Set(searchResults.filter(r => r.type === 'knowledge').map(r => r.id)) : null;

  const displayNotes = searchQuery
    ? filteredNotes.filter(n => searchedNoteIds?.has(n.id))
    : filteredNotes;
  const displayKps = searchQuery
    ? filteredKps.filter(k => searchedKpIds?.has(k.id))
    : filteredKps;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ position: 'relative' }}>
        <Search size={16} color="#6b6480" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
        <input
          placeholder="搜索笔记或知识点..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          style={{
            width: '100%', padding: '10px 14px 10px 38px',
            borderRadius: 10, border: '1px solid rgba(255,255,255,0.08)',
            background: 'rgba(255,255,255,0.04)',
            color: '#f0e8da', fontSize: 13, outline: 'none',
          }}
        />
      </div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <button
          onClick={() => setSubjectFilter(null)}
          style={{
            padding: '4px 12px', borderRadius: 8, border: 'none',
            background: !subjectFilter ? 'rgba(240,192,64,0.15)' : 'rgba(255,255,255,0.05)',
            color: !subjectFilter ? '#f0c040' : '#a8a0b8',
            fontSize: 12, fontWeight: 600, cursor: 'pointer',
          }}
        >
          全部
        </button>
        {SUBJECTS.map(s => (
          <button
            key={s}
            onClick={() => setSubjectFilter(subjectFilter === s ? null : s)}
            style={{
              padding: '4px 12px', borderRadius: 8, border: 'none',
              background: subjectFilter === s ? `${SUBJECT_COLORS[s]}25` : 'rgba(255,255,255,0.05)',
              color: subjectFilter === s ? SUBJECT_COLORS[s] : '#a8a0b8',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
            }}
          >
            {s}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 4, background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: 3, width: 'fit-content' }}>
        {(['all', 'notes', 'knowledge'] as const).map(mode => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            style={{
              padding: '5px 14px', borderRadius: 6, border: 'none',
              background: viewMode === mode ? 'rgba(240,192,64,0.15)' : 'transparent',
              color: viewMode === mode ? '#f0c040' : '#a8a0b8',
              fontSize: 12, cursor: 'pointer', fontWeight: 600,
            }}
          >
            {mode === 'all' ? '全部' : mode === 'notes' ? '笔记' : '知识点'}
          </button>
        ))}
      </div>

      {(viewMode === 'all' || viewMode === 'notes') && displayNotes.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: '#6b6480', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <FileText size={12} />
            笔记 ({displayNotes.length})
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
            {displayNotes.map(note => <NoteCard key={note.id} note={note} isUploaded={uploadedIds.has(note.id)} />)}
          </div>
        </div>
      )}

      {(viewMode === 'all' || viewMode === 'knowledge') && displayKps.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: '#6b6480', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Layers size={12} />
            知识点 ({displayKps.length})
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
            {displayKps.map(kp => <KnowledgePointCard key={kp.id} kp={kp} />)}
          </div>
        </div>
      )}

      {searchQuery && !displayNotes.length && !displayKps.length && (
        <div style={{ textAlign: 'center', padding: 40, color: '#6b6480', fontSize: 13 }}>
          未找到匹配的内容
        </div>
      )}
    </div>
  );
}

function AnalysisTab({ analysis }: { analysis: ReturnType<typeof useKnowledgeBase>['analysis'] }) {
  const healthPct = analysis.totalLinks > 0
    ? Math.round(analysis.validLinks / analysis.totalLinks * 100) : 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="glass" style={{ padding: 20, borderRadius: 14 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#f0e8da', marginBottom: 14 }}>
          链接健康概览
        </div>
        <div style={{ display: 'flex', gap: 24, alignItems: 'center', marginBottom: 16 }}>
          <div style={{ position: 'relative', width: 80, height: 80 }}>
            <svg width="80" height="80" viewBox="0 0 80 80">
              <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
              <circle
                cx="40" cy="40" r="34"
                fill="none"
                stroke={healthPct >= 90 ? '#27ae60' : healthPct >= 70 ? '#e67e22' : '#e74c3c'}
                strokeWidth="6"
                strokeDasharray={`${2 * Math.PI * 34 * healthPct / 100} ${2 * Math.PI * 34 * (100 - healthPct) / 100}`}
                strokeLinecap="round"
                transform="rotate(-90 40 40)"
                style={{ transition: 'stroke-dasharray 0.5s' }}
              />
              <text x="40" y="40" textAnchor="middle" dominantBaseline="middle" fill="#f0e8da" fontSize="14" fontWeight="700">
                {healthPct}%
              </text>
            </svg>
          </div>
          <div style={{ display: 'flex', gap: 20 }}>
            <div>
              <div style={{ fontSize: 11, color: '#6b6480' }}>链接总数</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#f0e8da' }}>{analysis.totalLinks}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#6b6480' }}>有效链接</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#27ae60' }}>{analysis.validLinks}</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#6b6480' }}>断链</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#e74c3c' }}>{analysis.brokenLinks}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="glass" style={{ padding: 20, borderRadius: 14 }}>
        <div style={{ fontSize: 15, fontWeight: 700, color: '#f0e8da', marginBottom: 14 }}>
          各科目链接状态
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {SUBJECTS.map(subject => {
            const s = analysis.bySubject[subject];
            if (!s || s.links === 0) return null;
            const pct = Math.round(s.valid / s.links * 100);
            const color = SUBJECT_COLORS[subject] || '#666';
            return (
              <div key={subject}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color }}>{subject}</span>
                  <span style={{ color: '#a8a0b8' }}>{s.valid}/{s.links} ({pct}%)</span>
                </div>
                <div style={{ height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                  <div style={{
                    width: `${pct}%`, height: '100%',
                    background: `linear-gradient(90deg, ${color}, ${color}88)`,
                    borderRadius: 2,
                  }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {analysis.brokenDetails.length > 0 && (
        <div className="glass" style={{ padding: 20, borderRadius: 14 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e74c3c', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={16} />
            断链详情 ({analysis.brokenDetails.length})
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {analysis.brokenDetails.map((issue, i) => (
              <div key={i} style={{
                padding: '8px 12px', borderRadius: 8,
                background: 'rgba(231,76,60,0.06)',
                border: '1px solid rgba(231,76,60,0.15)',
                fontSize: 12,
              }}>
                <span style={{ color: SUBJECT_COLORS[issue.noteSubject] }}>[{issue.noteSubject}]</span>{' '}
                <span style={{ color: '#f0e8da' }}>{issue.noteName}</span>
                <span style={{ color: '#6b6480', margin: '0 4px' }}>→</span>
                <span style={{ color: '#e74c3c' }}>{issue.targetName}</span>
                <span style={{ color: '#6b6480', marginLeft: 6 }}>(知识点不存在)</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {analysis.missingReferences.length > 0 && (
        <div className="glass" style={{ padding: 20, borderRadius: 14 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#e67e22', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
            <List size={16} />
            缺失知识点引用 ({analysis.missingReferences.length})
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {analysis.missingReferences.map((ref, i) => (
              <span key={i} style={{
                padding: '3px 10px', borderRadius: 6,
                background: 'rgba(230,126,34,0.1)',
                border: '1px solid rgba(230,126,34,0.2)',
                color: '#e67e22', fontSize: 12,
              }}>
                {ref}
              </span>
            ))}
          </div>
        </div>
      )}

      {analysis.brokenLinks === 0 && analysis.missingReferences.length === 0 && (
        <div style={{
          textAlign: 'center', padding: 40, color: '#27ae60',
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
        }}>
          <CheckCircle size={32} />
          <div style={{ fontSize: 14 }}>所有链接状态良好</div>
        </div>
      )}
    </div>
  );
}

export default function KnowledgePage() {
  const [tab, setTab] = useState<Tab>('browse');
  const [subjectFilter, setSubjectFilter] = useState<string | null>(null);
  const [graphView3D, setGraphView3D] = useState(true);
  const { notes, knowledgePoints, analysis, graph, subjectStats, addNotes } = useKnowledgeBase();
  const [processingFiles, setProcessingFiles] = useState(false);
  const [mineruOnline, setMineruOnline] = useState(false);
  const serverCheckDone = useRef(false);
  const { data } = useStore();

  // 从设置读取 MinerU 服务地址
  useEffect(() => {
    const { mineru } = data.settings;
    if (mineru.apiUrl) {
      setServerUrl(mineru.apiUrl);
    }
  }, [data.settings.mineru.apiUrl]);

  // Check MinerU server status on mount
  useEffect(() => {
    if (serverCheckDone.current) return;
    serverCheckDone.current = true;
    (async () => {
      const online = await checkMineruServer();
      setMineruOnline(online);
    })();
  }, []);

  const handleFileDrop = useCallback(async (files: File[]) => {
    setProcessingFiles(true);

    // 尝试 MinerU 服务（优先）
    if (isMineruOnline()) {
      let success = 0, failed = 0;
      for (const file of files) {
        try {
          const result = await convertWithMineru(file);
          addNotes([{
            name: result.name || file.name,
            title: result.title || file.name.replace(/\.[^.]+$/, ''),
            subject: '计算机',
            wikiLinks: [],
            content: result.content,
            images: result.images || [],
          }]);
          success++;
        } catch (err) {
          console.error(`MinerU 转换失败: ${file.name}`, err);
          failed++;
        }
      }
      if (failed > 0 && success === 0) {
        // 全部失败，尝试 fallback
        console.warn('MinerU 全部失败，回退到客户端解析');
        for (const file of files) {
          try {
            const parsed = await parseFile(file);
            const newNote = fileToNoteInput(parsed, analysis.knowledgePointNames);
            addNotes([newNote]);
          } catch (fallbackErr) {
            console.error(`客户端解析失败: ${file.name}`, fallbackErr);
          }
        }
      }
    } else {
      // 使用客户端解析
      for (const file of files) {
        try {
          const parsed = await parseFile(file);
          const newNote = fileToNoteInput(parsed, analysis.knowledgePointNames);
          addNotes([newNote]);
        } catch (err) {
          console.error(`解析失败: ${file.name}`, err);
        }
      }
    }

    setProcessingFiles(false);
  }, [addNotes, analysis.knowledgePointNames]);

  const uploadedIds = new Set(notes.filter(n => n.id.startsWith('upload_')).map(n => n.id));

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BookOpen size={24} color="#f0c040" />
          <span className="gradient-text">知识库</span>
        </h1>

        {/* Stats + MinerU status */}
        <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'stretch' }}>
          <StatCard label="笔记" value={analysis.totalNotes} color="#4a8fe7" icon={<FileText size={18} color="#4a8fe7" />} />
          <StatCard label="知识点" value={analysis.totalKnowledgePoints} color="#9b59b6" icon={<Layers size={18} color="#9b59b6" />} />
          <StatCard label="链接" value={analysis.totalLinks} color="#f0c040" icon={<List size={18} color="#f0c040" />} />
          <StatCard
            label="健康度"
            value={analysis.totalLinks > 0 ? `${Math.round(analysis.validLinks / analysis.totalLinks * 100)}%` : '-'}
            color={analysis.totalLinks > 0 && analysis.validLinks / analysis.totalLinks >= 0.9 ? '#27ae60' : '#e74c3c'}
            icon={<CheckCircle size={18} color={analysis.totalLinks > 0 && analysis.validLinks / analysis.totalLinks >= 0.9 ? '#27ae60' : '#e74c3c'} />}
          />
          {/* MinerU status */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass"
            style={{
              padding: '10px 16px', borderRadius: 12, minWidth: 120,
              display: 'flex', flexDirection: 'column', justifyContent: 'center',
              border: `1px solid ${mineruOnline ? 'rgba(46,204,113,0.2)' : 'rgba(255,255,255,0.06)'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {mineruOnline ? <Wifi size={14} color="#27ae60" /> : <Server size={14} color="#6b6480" />}
              <span style={{ fontSize: 13, fontWeight: 700, color: mineruOnline ? '#27ae60' : '#6b6480' }}>
                {mineruOnline ? 'MinerU 在线' : 'MinerU 离线'}
              </span>
            </div>
            <div style={{ fontSize: 9, color: '#6b6480', marginTop: 2 }}>
              {mineruOnline ? '文件转换由服务端处理' : '使用客户端解析（轻量）'}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 3, width: 'fit-content' }}>
        {[
          { key: 'browse' as Tab, label: '浏览', icon: Search },
          { key: 'graph' as Tab, label: '知识图谱', icon: Network },
          { key: 'analysis' as Tab, label: '链接分析', icon: BarChart3 },
          { key: 'agent' as Tab, label: 'AI Agent', icon: Sparkles },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '7px 18px', borderRadius: 8, border: 'none',
              display: 'flex', alignItems: 'center', gap: 6,
              background: tab === t.key ? 'rgba(240,192,64,0.12)' : 'transparent',
              color: tab === t.key ? '#f0c040' : '#a8a0b8',
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <AnimatePresence mode="wait">
          {tab === 'browse' && (
            <motion.div
              key="browse" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ height: '100%', overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}
            >
              <FileDropZone onFiles={handleFileDrop} disabled={processingFiles} />

              {/* MinerU hint when offline */}
              {!mineruOnline && (
                <div style={{
                  fontSize: 10, color: '#6b6480', textAlign: 'center',
                  background: 'rgba(255,255,255,0.02)', padding: '4px 12px', borderRadius: 6,
                }}>
                  提示：启动 <code style={{ color: '#f0c040' }}>mineru-service</code> 可启用服务端文档转换（公式/表格/图片）
                </div>
              )}

              {!subjectFilter && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
                  {subjectStats.map(stat => (
                    <SubjectCard key={stat.name} stat={stat} onClick={() => setSubjectFilter(stat.name)} />
                  ))}
                </div>
              )}

              {subjectFilter && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <button
                    onClick={() => setSubjectFilter(null)}
                    style={{
                      padding: '4px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.12)',
                      background: 'none', color: '#a8a0b8', fontSize: 11, cursor: 'pointer',
                    }}
                  >
                    ← 返回全部
                  </button>
                  <span style={{ fontSize: 14, fontWeight: 600, color: SUBJECT_COLORS[subjectFilter] }}>
                    {subjectFilter}
                  </span>
                </div>
              )}

              <BrowseTab
                notes={notes}
                knowledgePoints={knowledgePoints}
                subjectFilter={subjectFilter}
                setSubjectFilter={setSubjectFilter}
                uploadedIds={uploadedIds}
              />
            </motion.div>
          )}

          {tab === 'graph' && (
            <motion.div
              key="graph" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ height: '100%', minHeight: 500, display: 'flex', flexDirection: 'column' }}
            >
              <div style={{ display: 'flex', gap: 4, marginBottom: 8, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: 3, width: 'fit-content' }}>
                <button
                  onClick={() => setGraphView3D(true)}
                  style={{
                    padding: '5px 14px', borderRadius: 6, border: 'none',
                    background: graphView3D ? 'rgba(240,192,64,0.12)' : 'transparent',
                    color: graphView3D ? '#f0c040' : '#a8a0b8',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  3D 图谱
                </button>
                <button
                  onClick={() => setGraphView3D(false)}
                  style={{
                    padding: '5px 14px', borderRadius: 6, border: 'none',
                    background: !graphView3D ? 'rgba(240,192,64,0.12)' : 'transparent',
                    color: !graphView3D ? '#f0c040' : '#a8a0b8',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  2D 图谱
                </button>
              </div>

              <div style={{ flex: 1, minHeight: 0 }}>
                {graphView3D ? (
                  <KnowledgeGraph3D data={graph} />
                ) : (
                  <KnowledgeGraph data={graph} />
                )}
              </div>
            </motion.div>
          )}

          {tab === 'analysis' && (
            <motion.div
              key="analysis" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ height: '100%', overflow: 'auto' }}
            >
              <AnalysisTab analysis={analysis} />
            </motion.div>
          )}

          {tab === 'agent' && (
            <motion.div
              key="agent" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ height: '100%', overflow: 'auto' }}
            >
              <AgentPanel notes={notes} knowledgePoints={knowledgePoints} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
