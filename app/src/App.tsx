import { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Sparkles, ListTodo, Trash2, CalendarDays } from 'lucide-react';
import { StoreProvider } from './lib/store';
import GachaPage from './pages/GachaPage';
import TasksPage from './pages/TasksPage';
import DiscardPage from './pages/DiscardPage';
import SchedulePage from './pages/SchedulePage';

const NAV_ITEMS = [
  { path: '/gacha', label: '抽卡', icon: Sparkles },
  { path: '/tasks', label: '任务', icon: ListTodo },
  { path: '/discard', label: '弃牌堆', icon: Trash2 },
  { path: '/schedule', label: '日程', icon: CalendarDays },
];

function AppShell() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar */}
      <motion.nav
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
        animate={{ width: expanded ? 180 : 56 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        style={{
          background: 'rgba(15,20,34,0.9)',
          backdropFilter: 'blur(16px)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
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
          style={{
            padding: '12px 16px',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            overflow: 'hidden',
          }}
        >
          <div
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
