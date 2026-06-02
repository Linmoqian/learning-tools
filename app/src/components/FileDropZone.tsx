import { useState, useRef, useCallback } from 'react';

// ===== File type icons (inline SVG for zero deps) =====
const FILE_ICONS: Record<string, string> = {
  pdf: '#e74c3c',
  pptx: '#e67e22',
  ppt: '#e67e22',
  docx: '#3498db',
  doc: '#3498db',
  md: '#2ecc71',
};

const FILE_LABELS: Record<string, string> = {
  pdf: 'PDF',
  pptx: 'PPT',
  ppt: 'PPT',
  docx: 'DOCX',
  doc: 'DOC',
  md: 'MD',
};

function FileTypeBadge({ ext }: { ext: string }) {
  const color = FILE_ICONS[ext] || '#a8a0b8';
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
      background: `${color}18`, color, border: `1px solid ${color}30`,
    }}>
      {FILE_LABELS[ext] || ext}
    </span>
  );
}

// ===== 主组件 =====
interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
  acceptedExtensions?: string;
}

export default function FileDropZone({ onFiles, disabled, acceptedExtensions = '.pdf,.pptx,.ppt,.docx,.doc,.md' }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [processing, setProcessing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (fileList: FileList) => {
    const files = Array.from(fileList).filter(f => {
      const ext = f.name.split('.').pop()?.toLowerCase();
      return ext && acceptedExtensions.includes(ext);
    });
    if (files.length === 0) return;
    setProcessing(true);
    // 小延迟让 UI 更新
    await new Promise(r => setTimeout(r, 50));
    onFiles(files);
    setProcessing(false);
  }, [onFiles, acceptedExtensions]);

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setDragOver(true);
  }, [disabled]);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(false);
    if (!disabled && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [disabled, handleFiles]);

  const onClick = useCallback(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  }, [disabled]);

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={acceptedExtensions}
        multiple
        style={{ display: 'none' }}
        onChange={e => e.target.files && handleFiles(e.target.files)}
      />

      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={onClick}
        style={{
          position: 'relative',
          padding: '28px 20px',
          borderRadius: 14,
          cursor: disabled ? 'default' : 'pointer',
          transition: 'all 0.2s ease',
          border: `2px dashed ${dragOver ? 'rgba(240,192,64,0.5)' : 'rgba(255,255,255,0.08)'}`,
          background: dragOver
            ? 'rgba(240,192,64,0.06)'
            : 'rgba(255,255,255,0.02)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 10,
          userSelect: 'none',
        }}
      >
        {/* Drag-over glow */}
        {dragOver && (
          <div style={{
            position: 'absolute', inset: -2, borderRadius: 16,
            boxShadow: '0 0 30px rgba(240,192,64,0.15), 0 0 60px rgba(240,192,64,0.05)',
            pointerEvents: 'none',
          }} />
        )}

        {/* Icon */}
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: dragOver ? 'rgba(240,192,64,0.12)' : 'rgba(255,255,255,0.04)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'all 0.2s',
        }}>
          {processing ? (
            <div style={{
              width: 20, height: 20,
              border: '2px solid rgba(240,192,64,0.3)',
              borderTopColor: '#f0c040',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite',
            }} />
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={dragOver ? '#f0c040' : '#6b6480'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          )}
        </div>

        {/* Text */}
        <div style={{ fontSize: 13, color: dragOver ? '#f0c040' : '#a8a0b8', fontWeight: 600, transition: 'color 0.2s' }}>
          {processing ? '正在处理...' : dragOver ? '释放文件以上传' : '拖拽文件到此处上传'}
        </div>

        {!processing && !dragOver && (
          <div style={{ fontSize: 11, color: '#6b6480' }}>
            或点击选择文件
          </div>
        )}

        {/* File type badges */}
        {!processing && (
          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
            {['pdf', 'pptx', 'docx', 'md'].map(ext => (
              <FileTypeBadge key={ext} ext={ext} />
            ))}
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </>
  );
}
