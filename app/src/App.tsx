import { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import gsap from 'gsap';
import { Sparkles, ListTodo, Trash2, CalendarDays, BookOpen, Settings } from 'lucide-react';
import { StoreProvider, useStore } from './lib/store';
import GachaPage from './pages/GachaPage';
import TasksPage from './pages/TasksPage';
import DiscardPage from './pages/DiscardPage';
import SchedulePage from './pages/SchedulePage';
import KnowledgePage from './pages/KnowledgePage';
import SettingsPage from './pages/SettingsPage';

const NAV_ITEMS = [
  { path: '/gacha', label: '抽卡', icon: Sparkles },
  { path: '/tasks', label: '任务', icon: ListTodo },
  { path: '/knowledge', label: '知识库', icon: BookOpen },
  { path: '/discard', label: '弃牌堆', icon: Trash2 },
  { path: '/schedule', label: '日程', icon: CalendarDays },
  { path: '/settings', label: '设置', icon: Settings },
];

function AppShell() {
  const [expanded, setExpanded] = useState(false);
  const { data } = useStore();
  const navRef = useRef<HTMLDivElement>(null);

  // 应用保存的主题
  useEffect(() => {
    const { theme } = data.settings;
    const root = document.documentElement;
    // 背景模式
    root.setAttribute('data-theme', theme.themeMode);
    // 主色变量
    root.style.setProperty('--gold', theme.primaryColor);
    root.style.setProperty('--gold-light', theme.primaryColorLight);
    root.style.setProperty('--gold-dark', theme.primaryColorDark);
    root.style.setProperty('--text-gold', theme.primaryColor);
    const rgb = theme.primaryColor
      ? `${parseInt(theme.primaryColor.slice(1, 3), 16)}, ${parseInt(theme.primaryColor.slice(3, 5), 16)}, ${parseInt(theme.primaryColor.slice(5, 7), 16)}`
      : '240, 192, 64';
    root.style.setProperty('--shadow-glow', `0 0 20px rgba(${rgb}, 0.3)`);
    root.style.setProperty('--shadow-btn', `0 4px 16px rgba(${rgb}, 0.25)`);
  }, [data.settings.theme]);

  // GSAP 导航项弹性交错入场
  useEffect(() => {
    const el = navRef.current;
    if (!el) return;
    const links = el.querySelectorAll('a');
    if (!links.length) return;
    gsap.fromTo(
      links,
      { x: -24, opacity: 0, scale: 0.9 },
      {
        x: 0,
        opacity: 1,
        scale: 1,
        duration: 0.45,
        ease: 'back.out(1.7)',
        stagger: 0.06,
      },
    );
  }, []);

  // GSAP 导航项弹性悬停
  useEffect(() => {
    const el = navRef.current;
    if (!el) return;
    const links = Array.from(el.querySelectorAll('a'));
    const handlers = links.map(link => {
      const onEnter = () => gsap.to(link, { scale: 1.06, duration: 0.3, ease: 'back.out(2)' });
      const onLeave = () => gsap.to(link, { scale: 1, duration: 0.3, ease: 'elastic.out(1, 0.3)' });
      link.addEventListener('mouseenter', onEnter);
      link.addEventListener('mouseleave', onLeave);
      return { link, onEnter, onLeave };
    });
    return () => {
      handlers.forEach(({ link, onEnter, onLeave }) => {
        link.removeEventListener('mouseenter', onEnter);
        link.removeEventListener('mouseleave', onLeave);
      });
    };
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <motion.nav
        ref={navRef}
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
        animate={{ width: expanded ? 180 : 56 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        style={{
          background: 'var(--bg-sidebar)',
          backdropFilter: 'blur(16px)',
          borderRight: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          padding: '12px 0',
          gap: 4,
          flexShrink: 0,
          overflow: 'hidden',
          zIndex: 50,
        }}
      >
        {/* Logo */}
        <div
          data-tauri-drag-region
          style={{
            padding: '12px 16px',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            overflow: 'hidden',
            cursor: 'grab',
          }}
        >
          <div
            data-tauri-drag-region
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #f0c040, #c99f2e)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 14,
              fontWeight: 700,
              color: '#0a0e1a',
              flexShrink: 0,
            }}
          >
            L
          </div>
          <motion.span
            animate={{ opacity: expanded ? 1 : 0 }}
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: '#f0e8da',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
            }}
          >
            学习工具
          </motion.span>
        </div>

        {/* Nav items */}
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 16px',
              margin: '0 8px',
              borderRadius: 10,
              textDecoration: 'none',
              color: isActive ? '#f0c040' : '#a8a0b8',
              background: isActive ? 'rgba(240,192,64,0.1)' : 'transparent',
              border: isActive ? '1px solid rgba(240,192,64,0.2)' : '1px solid transparent',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              transition: 'all 0.15s ease',
            })}
          >
            <item.icon size={20} style={{ flexShrink: 0 }} />
            <motion.span
              animate={{ opacity: expanded ? 1 : 0 }}
              style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden' }}
            >
              {item.label}
            </motion.span>
          </NavLink>
        ))}
      </motion.nav>

      {/* Main content */}
      <main style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<Navigate to="/gacha" replace />} />
            <Route
              path="/gacha"
              element={
                <motion.div
                  key="gacha"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  style={{ height: '100%' }}
                >
                  <GachaPage />
                </motion.div>
              }
            />
            <Route
              path="/tasks"
              element={
                <motion.div
                  key="tasks"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  style={{ height: '100%' }}
                >
                  <TasksPage />
                </motion.div>
              }
            />
            <Route
              path="/knowledge"
              element={
                <motion.div
                  key="knowledge"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  style={{ height: '100%' }}
                >
                  <KnowledgePage />
                </motion.div>
              }
            />
            <Route
              path="/discard"
              element={
                <motion.div
                  key="discard"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  style={{ height: '100%' }}
                >
                  <DiscardPage />
                </motion.div>
              }
            />
            <Route
              path="/schedule"
              element={
                <motion.div
                  key="schedule"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  style={{ height: '100%' }}
                >
                  <SchedulePage />
                </motion.div>
              }
            />
            <Route
              path="/settings"
              element={
                <motion.div
                  key="settings"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  style={{ height: '100%' }}
                >
                  <SettingsPage />
                </motion.div>
              }
            />
          </Routes>
        </AnimatePresence>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <StoreProvider>
        <AppShell />
      </StoreProvider>
    </BrowserRouter>
  );
}
