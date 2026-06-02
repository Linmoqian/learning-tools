import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BookOpen, Search, Network, BarChart3, ChevronRight,
  FileText, Layers, AlertTriangle, CheckCircle, List,
} from 'lucide-react';
import KnowledgeGraph from '../components/KnowledgeGraph';
import KnowledgeGraph3D from '../components/KnowledgeGraph3D';
import {
  useKnowledgeBase, searchItems, SUBJECTS, SUBJECT_COLORS,
} from '../lib/knowledge';
import type { Note, KnowledgePoint, SubjectStat } from '../lib/knowledge';

type Tab = 'browse' | 'graph' | 'analysis';

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
      {/* Mini health bar */}
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

function NoteCard({ note }: { note: Note }) {
  const color = SUBJECT_COLORS[note.subject] || '#666';
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass"
      style={{
        padding: 14, borderRadius: 12,
        border: '1px solid rgba(255,255,255,0.06)',
        borderLeft: `3px solid ${color}`,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 600, color: '#f0e8da', marginBottom: 4 }}>
        {note.title}
      </div>
      <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 6, lineHeight: 1.5 }}>
        {note.content.slice(0, 80)}…
      </div>
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

function BrowseTab({ notes, knowledgePoints, subjectFilter, setSubjectFilter }:
  { notes: Note[]; knowledgePoints: KnowledgePoint[]; subjectFilter: string | null; setSubjectFilter: (s: string | null) => void }) {

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
      {/* Search */}
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

      {/* Subject filter chips */}
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

      {/* View mode tabs */}
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

      {/* Results */}
      {(viewMode === 'all' || viewMode === 'notes') && displayNotes.length > 0 && (
        <div>
          <div style={{ fontSize: 12, color: '#6b6480', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            <FileText size={12} />
            笔记 ({displayNotes.length})
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
            {displayNotes.map(note => <NoteCard key={note.id} note={note} />)}
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
      {/* Main stats */}
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

      {/* By subject */}
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

      {/* Broken links */}
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

      {/* Missing references */}
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
  const { notes, knowledgePoints, analysis, graph, subjectStats } = useKnowledgeBase();

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <BookOpen size={24} color="#f0c040" />
          <span className="gradient-text">知识库</span>
        </h1>

        {/* Stats row */}
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <StatCard label="笔记" value={analysis.totalNotes} color="#4a8fe7" icon={<FileText size={18} color="#4a8fe7" />} />
          <StatCard label="知识点" value={analysis.totalKnowledgePoints} color="#9b59b6" icon={<Layers size={18} color="#9b59b6" />} />
          <StatCard label="链接" value={analysis.totalLinks} color="#f0c040" icon={<List size={18} color="#f0c040" />} />
          <StatCard
            label="健康度"
            value={analysis.totalLinks > 0 ? `${Math.round(analysis.validLinks / analysis.totalLinks * 100)}%` : '-'}
            color={analysis.totalLinks > 0 && analysis.validLinks / analysis.totalLinks >= 0.9 ? '#27ae60' : '#e74c3c'}
            icon={<CheckCircle size={18} color={analysis.totalLinks > 0 && analysis.validLinks / analysis.totalLinks >= 0.9 ? '#27ae60' : '#e74c3c'} />}
          />
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: 3, width: 'fit-content' }}>
        {[
          { key: 'browse' as Tab, label: '浏览', icon: Search },
          { key: 'graph' as Tab, label: '知识图谱', icon: Network },
          { key: 'analysis' as Tab, label: '链接分析', icon: BarChart3 },
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
              {/* Subject overview */}
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
              />
            </motion.div>
          )}

          {tab === 'graph' && (
            <motion.div
              key="graph" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ height: '100%', minHeight: 500, display: 'flex', flexDirection: 'column' }}
            >
              {/* 2D/3D toggle */}
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
        </AnimatePresence>
      </div>
    </div>
  );
}
