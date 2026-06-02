import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';

interface Props {
  content: string;
}

const components: Components = {
  h1: ({ children }) => (
    <h1 style={{
      fontSize: 22, fontWeight: 700, color: '#f0e8da',
      margin: '24px 0 12px', paddingBottom: 8,
      borderBottom: '1px solid rgba(255,255,255,0.08)',
    }}>{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 style={{
      fontSize: 18, fontWeight: 700, color: '#f0e8da',
      margin: '20px 0 10px', paddingBottom: 6,
      borderBottom: '1px solid rgba(255,255,255,0.06)',
    }}>{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 style={{
      fontSize: 15, fontWeight: 700, color: '#f0e8da',
      margin: '16px 0 8px',
    }}>{children}</h3>
  ),
  p: ({ children }) => (
    <p style={{
      fontSize: 14, lineHeight: 1.8, color: '#d0c8c0',
      margin: '8px 0',
    }}>{children}</p>
  ),
  ul: ({ children }) => (
    <ul style={{
      margin: '8px 0', paddingLeft: 24,
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>{children}</ul>
  ),
  ol: ({ children }) => (
    <ol style={{
      margin: '8px 0', paddingLeft: 24,
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>{children}</ol>
  ),
  li: ({ children }) => (
    <li style={{
      fontSize: 14, lineHeight: 1.7, color: '#d0c8c0',
    }}>{children}</li>
  ),
  strong: ({ children }) => (
    <strong style={{ color: '#f0c040', fontWeight: 700 }}>{children}</strong>
  ),
  em: ({ children }) => (
    <em style={{ color: '#a8a0b8', fontStyle: 'italic' }}>{children}</em>
  ),
  code: ({ children }) => (
    <code style={{
      background: 'rgba(240,192,64,0.1)',
      color: '#f0c040',
      padding: '2px 6px', borderRadius: 4,
      fontSize: 12, fontFamily: '"Fira Code", monospace',
    }}>{children}</code>
  ),
  pre: ({ children }) => (
    <pre style={{
      background: 'rgba(10,14,26,0.7)',
      border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 10,
      padding: '14px 16px',
      overflow: 'auto',
      fontSize: 12, lineHeight: 1.6,
      fontFamily: '"Fira Code", monospace',
      margin: '12px 0',
    }}>{children}</pre>
  ),
  blockquote: ({ children }) => (
    <blockquote style={{
      borderLeft: '3px solid #f0c040',
      padding: '8px 16px',
      margin: '12px 0',
      background: 'rgba(240,192,64,0.04)',
      borderRadius: '0 8px 8px 0',
      color: '#a8a0b8',
      fontStyle: 'italic',
    }}>{children}</blockquote>
  ),
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noreferrer" style={{
      color: '#4a8fe7',
      textDecoration: 'underline',
      textUnderlineOffset: 2,
    }}>{children}</a>
  ),
  hr: () => (
    <hr style={{
      border: 'none', borderTop: '1px solid rgba(255,255,255,0.06)',
      margin: '20px 0',
    }} />
  ),
  img: ({ src, alt }) => (
    <img src={src} alt={alt} style={{
      maxWidth: '100%', borderRadius: 8,
      margin: '12px 0', border: '1px solid rgba(255,255,255,0.06)',
    }} />
  ),
  table: ({ children }) => (
    <div style={{ overflow: 'auto', margin: '12px 0' }}>
      <table style={{
        width: '100%', borderCollapse: 'collapse',
        fontSize: 13,
      }}>{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th style={{
      border: '1px solid rgba(255,255,255,0.1)',
      padding: '8px 12px', background: 'rgba(255,255,255,0.04)',
      color: '#f0e8da', fontWeight: 700, textAlign: 'left',
    }}>{children}</th>
  ),
  td: ({ children }) => (
    <td style={{
      border: '1px solid rgba(255,255,255,0.06)',
      padding: '8px 12px', color: '#d0c8c0',
    }}>{children}</td>
  ),
};

export default function MarkdownViewer({ content }: Props) {
  const processed = useMemo(() => {
    // 处理 [[wikiLink]] 语法 — 临时保留原样显示
    return content;
  }, [content]);

  if (!content) {
    return (
      <div style={{
        textAlign: 'center', padding: 40,
        color: '#6b6480', fontSize: 14,
      }}>
        无内容
      </div>
    );
  }

  return (
    <div style={{ padding: '4px 0' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={components}
      >
        {processed}
      </ReactMarkdown>
    </div>
  );
}
