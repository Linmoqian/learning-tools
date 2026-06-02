import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { X, FileText, Bookmark } from 'lucide-react';
import MarkdownViewer from './MarkdownViewer';
import { getImageUrl } from '../lib/mineruClient';
import { SUBJECT_COLORS } from '../lib/knowledge';
import type { Note } from '../lib/knowledge';

interface Props {
  note: Note | null;
  isUploaded: boolean;
  onClose: () => void;
}

function ImageGallery({ images }: { images: string[] }) {
  if (!images.length) return null;
  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
      {images.map((img, i) => (
        <a key={i} href={getImageUrl(img)} target="_blank" rel="noreferrer">
          <img
            src={getImageUrl(img)}
            alt={`插图 ${i + 1}`}
            style={{
              height: 120, borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.08)',
              objectFit: 'cover', cursor: 'pointer',
              transition: 'opacity 0.2s',
            }}
            onMouseEnter={e => { e.currentTarget.style.opacity = '0.8'; }}
            onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
          />
        </a>
      ))}
    </div>
  );
}

export default function NoteDetailModal({ note, isUploaded, onClose }: Props) {
  const headerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (headerRef.current) {
      gsap.fromTo(headerRef.current, { y: -16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.3, ease: 'back.out(1.7)' });
    }
  }, [note]);

  return (
    <AnimatePresence>
      {note && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          style={{
            position: 'fixed', inset: 0, zIndex: 100,
            background: 'rgba(5,5,16,0.85)',
            backdropFilter: 'blur(16px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          onClick={onClose}
        >
          <motion.div
            key={note.id}
            initial={{ scale: 0.92, y: 30, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.92, y: 30, opacity: 0 }}
            transition={{ type: 'spring', damping: 22, stiffness: 280 }}
            onClick={e => e.stopPropagation()}
            style={{
              background: 'linear-gradient(180deg, #1a2038 0%, #0f1422 100%)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 20,
              width: '90vw', maxWidth: 800,
              maxHeight: '85vh',
              display: 'flex', flexDirection: 'column',
              position: 'relative',
              boxShadow: '0 32px 80px rgba(0,0,0,0.5)',
            }}
          >
            {/* Header */}
            <div ref={headerRef} style={{
              padding: '20px 24px 16px',
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              display: 'flex', alignItems: 'flex-start', gap: 12,
              flexShrink: 0,
            }}>
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: `${SUBJECT_COLORS[note.subject] || '#666'}18`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                <FileText size={18} color={SUBJECT_COLORS[note.subject] || '#666'} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4,
                }}>
                  <h2 style={{
                    fontSize: 18, fontWeight: 700, color: '#f0e8da',
                    margin: 0, overflow: 'hidden', textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}>
                    {note.title}
                  </h2>
                  {isUploaded && (
                    <span style={{
                      fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 4,
                      background: 'rgba(240,192,64,0.12)', color: '#f0c040',
                      flexShrink: 0,
                    }}>
                      已上传
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#6b6480' }}>
                  <span style={{
                    padding: '1px 8px', borderRadius: 4,
                    background: `${SUBJECT_COLORS[note.subject] || '#666'}18`,
                    color: SUBJECT_COLORS[note.subject] || '#666',
                    fontWeight: 600,
                  }}>
                    {note.subject}
                  </span>
                  <span>{note.name}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: '50%', width: 32, height: 32,
                  cursor: 'pointer', color: '#6b6480',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(240,192,64,0.12)'; e.currentTarget.style.color = '#f0c040'; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.color = '#6b6480'; }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Wiki links */}
            {note.wikiLinks.length > 0 && (
              <div style={{
                padding: '10px 24px',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center',
              }}>
                <Bookmark size={12} color="#f0c040" />
                {note.wikiLinks.map((link, i) => (
                  <span key={i} style={{
                    fontSize: 11, padding: '2px 10px', borderRadius: 4,
                    background: 'rgba(240,192,64,0.08)', color: '#f0c040',
                  }}>
                    {link}
                  </span>
                ))}
              </div>
            )}

            {/* Content */}
            <div style={{
              flex: 1, overflow: 'auto', padding: '20px 24px 24px',
            }}>
              <MarkdownViewer content={note.content} />

              {/* Image gallery */}
              <ImageGallery images={note.images || []} />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
