import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import { Settings, Save, Eye, EyeOff } from 'lucide-react';
import { useStore } from '../lib/store';
import { AppSettings, DEFAULT_SETTINGS } from '../lib/types';

/** 将 hex 颜色变亮（混合白色） */
function lightenHex(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, ((num >> 16) & 0xff) + Math.round(amount * (255 - ((num >> 16) & 0xff))));
  const g = Math.min(255, ((num >> 8) & 0xff) + Math.round(amount * (255 - ((num >> 8) & 0xff))));
  const b = Math.min(255, (num & 0xff) + Math.round(amount * (255 - (num & 0xff))));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}

/** 将 hex 颜色变暗（混合黑色） */
function darkenHex(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.round(((num >> 16) & 0xff) * (1 - amount));
  const g = Math.round(((num >> 8) & 0xff) * (1 - amount));
  const b = Math.round((num & 0xff) * (1 - amount));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}

/** 将 hex 转为 RGB 分量字符串 "r, g, b" */
function hexToRgb(hex: string): string {
  const num = parseInt(hex.replace('#', ''), 16);
  return `${(num >> 16) & 0xff}, ${(num >> 8) & 0xff}, ${num & 0xff}`;
}

/** 应用主题颜色到 CSS 变量 */
function applyTheme(theme: AppSettings['theme']) {
  const root = document.documentElement;
  root.style.setProperty('--gold', theme.primaryColor);
  root.style.setProperty('--gold-light', theme.primaryColorLight);
  root.style.setProperty('--gold-dark', theme.primaryColorDark);
  root.style.setProperty('--text-gold', theme.primaryColor);
  root.style.setProperty('--shadow-glow', `0 0 20px rgba(${hexToRgb(theme.primaryColor)}, 0.3)`);
  root.style.setProperty('--shadow-btn', `0 4px 16px rgba(${hexToRgb(theme.primaryColor)}, 0.25)`);
}

// ===== Input 子组件 =====
function InputField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  const [show, setShow] = useState(false);
  const isPassword = type === 'password';
  const inputType = isPassword ? (show ? 'text' : 'password') : type;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label style={{ fontSize: 12, color: '#a8a0b8', fontWeight: 600 }}>{label}</label>
      <div style={{ position: 'relative' }}>
        <input
          type={inputType}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          style={{
            width: '100%',
            padding: isPassword ? '8px 36px 8px 12px' : '8px 12px',
            borderRadius: 8,
            border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(255,255,255,0.04)',
            color: '#f0e8da',
            fontSize: 13,
            outline: 'none',
            transition: 'border-color 0.15s ease',
          }}
          onFocus={e => { e.target.style.borderColor = 'var(--gold)'; }}
          onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.1)'; }}
        />
        {isPassword && (
          <button
            onClick={() => setShow(!show)}
            style={{
              position: 'absolute',
              right: 8,
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#6b6480',
              display: 'flex',
              alignItems: 'center',
              padding: 2,
            }}
          >
            {show ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { data, dispatch } = useStore();
  const pageRef = useRef<HTMLDivElement>(null);
  const [localSettings, setLocalSettings] = useState<AppSettings>(data.settings);
  const [saved, setSaved] = useState(false);

  // 同步外部数据变化
  useEffect(() => {
    setLocalSettings(data.settings);
  }, [data.settings]);

  // 应用已保存的主题
  useEffect(() => {
    applyTheme(data.settings.theme);
  }, [data.settings.theme]);

  // GSAP 页面入场 + section 弹性交错
  useEffect(() => {
    const el = pageRef.current;
    if (!el) return;
    const title = el.querySelector('h1');
    const sections = el.querySelectorAll('[data-setting-section]');
    const tl = gsap.timeline();
    if (title) {
      tl.fromTo(title, { y: -16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35, ease: 'back.out(1.7)' });
    }
    if (sections.length) {
      tl.fromTo(
        sections,
        { y: 20, opacity: 0, scaleX: 0.97 },
        { y: 0, opacity: 1, scaleX: 1, duration: 0.4, ease: 'back.out(1.4)', stagger: 0.08 },
        '-=0.05',
      );
    }
    return () => { tl.kill(); };
  }, []);

  const update = (partial: Partial<AppSettings>) => {
    setLocalSettings(prev => ({ ...prev, ...partial }));
  };

  const handlePrimaryColorChange = (color: string) => {
    const theme = {
      primaryColor: color,
      primaryColorLight: lightenHex(color, 0.6),
      primaryColorDark: darkenHex(color, 0.25),
    };
    applyTheme(theme);
    update({ theme });
  };

  const handleSave = () => {
    dispatch({ type: 'UPDATE_SETTINGS', settings: localSettings });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setLocalSettings(DEFAULT_SETTINGS);
    applyTheme(DEFAULT_SETTINGS.theme);
  };

  const sections = [
    {
      title: 'LLM API 配置',
      desc: '用于 AI 分析任务、生成建议等',
      fields: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <InputField
            label="API 地址"
            value={localSettings.llm.apiUrl}
            onChange={v => update({ llm: { ...localSettings.llm, apiUrl: v } })}
            placeholder="https://api.openai.com/v1"
          />
          <InputField
            label="API Key"
            type="password"
            value={localSettings.llm.apiKey}
            onChange={v => update({ llm: { ...localSettings.llm, apiKey: v } })}
            placeholder="sk-..."
          />
          <InputField
            label="模型名称"
            value={localSettings.llm.modelName}
            onChange={v => update({ llm: { ...localSettings.llm, modelName: v } })}
            placeholder="gpt-4o"
          />
        </div>
      ),
    },
    {
      title: 'MinerU API 配置',
      desc: '用于文档解析、OCR 识别等',
      fields: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <InputField
            label="API 地址"
            value={localSettings.mineru.apiUrl}
            onChange={v => update({ mineru: { ...localSettings.mineru, apiUrl: v } })}
            placeholder="https://api.mineru.com/v1"
          />
          <InputField
            label="API Key"
            type="password"
            value={localSettings.mineru.apiKey}
            onChange={v => update({ mineru: { ...localSettings.mineru, apiKey: v } })}
            placeholder="输入 MinerU API Key"
          />
        </div>
      ),
    },
    {
      title: '主题颜色',
      desc: '更改应用的主色调',
      fields: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ position: 'relative' }}>
              <input
                type="color"
                value={localSettings.theme.primaryColor}
                onChange={e => handlePrimaryColorChange(e.target.value)}
                style={{
                  width: 48,
                  height: 48,
                  border: '2px solid rgba(255,255,255,0.15)',
                  borderRadius: 12,
                  cursor: 'pointer',
                  padding: 2,
                  background: 'none',
                }}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ fontSize: 14, color: '#f0e8da', fontWeight: 600 }}>
                主色
              </span>
              <span style={{ fontSize: 11, color: '#6b6480', fontFamily: 'monospace' }}>
                {localSettings.theme.primaryColor}
              </span>
            </div>
            {/* 预览色块 */}
            <div style={{ display: 'flex', gap: 6, marginLeft: 'auto' }}>
              {['primaryColor', 'primaryColorLight', 'primaryColorDark'].map(key => (
                <div
                  key={key}
                  title={key}
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: 6,
                    background: localSettings.theme[key as keyof typeof localSettings.theme],
                    border: '1px solid rgba(255,255,255,0.1)',
                  }}
                />
              ))}
            </div>
          </div>
          <p style={{ fontSize: 11, color: '#6b6480', lineHeight: 1.4 }}>
            选择主色后实时预览，保存后永久生效。暗色和浅色变体会自动生成。
          </p>
        </div>
      ),
    },
  ];

  return (
    <div ref={pageRef} style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', gap: 20, overflow: 'auto' }}>
      {/* Header */}
      <div>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Settings size={24} color="var(--gold)" />
          <span className="gradient-text">设置</span>
        </h1>
        <p className="page-subtitle">配置 API 连接和应用外观</p>
      </div>

      {/* Sections */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 560 }}>
        {sections.map(sec => (
          <div
            key={sec.title}
            data-setting-section
            className="glass"
            style={{
              padding: 20,
              borderRadius: 16,
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}
          >
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#f0e8da', marginBottom: 2 }}>
                {sec.title}
              </h3>
              <p style={{ fontSize: 12, color: '#6b6480' }}>{sec.desc}</p>
            </div>
            {sec.fields}
          </div>
        ))}

        {/* Actions */}
        <div
          className="glass"
          style={{
            padding: 16,
            borderRadius: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <button
            onClick={handleReset}
            style={{
              padding: '8px 18px',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.12)',
              background: 'none',
              color: '#a8a0b8',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            恢复默认
          </button>

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleSave}
            style={{
              padding: '8px 24px',
              borderRadius: 8,
              border: 'none',
              background: saved
                ? 'linear-gradient(135deg, #27ae60, #1e8449)'
                : 'linear-gradient(135deg, var(--gold), var(--gold-dark))',
              color: saved ? '#fff' : '#0a0e1a',
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              transition: 'all 0.2s ease',
            }}
          >
            <Save size={16} />
            {saved ? '已保存' : '保存设置'}
          </motion.button>
        </div>
      </div>
    </div>
  );
}
