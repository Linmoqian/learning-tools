import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, ListTodo, BookOpen, CalendarDays, Settings, ChevronRight, ChevronLeft } from 'lucide-react';

const GUIDE_STORAGE_KEY = 'learning-tools-guide-seen';

export function hasSeenGuide(): boolean {
  try {
    return localStorage.getItem(GUIDE_STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

export function markGuideSeen() {
  try {
    localStorage.setItem(GUIDE_STORAGE_KEY, 'true');
  } catch { /* ignore */ }
}

const STEPS = [
  {
    icon: <Sparkles size={32} />,
    title: '欢迎使用学习工具',
    desc: '这是一套帮你管理学习任务、积累知识、合理安排时间的超级自动化工具。',
    details: [
      '通过「抽卡」机制随机选中任务，降低决策成本',
      '番茄钟计时，专注完成任务',
      '知识库关联笔记与知识点，构建知识网络',
    ],
  },
  {
    icon: <ListTodo size={32} />,
    title: '任务管理',
    desc: '在「任务」页面创建和管理你的学习任务。',
    details: [
      '设置任务名称、预计时间、优先级、截止日期',
      '标记任务分类（每日/每周/柔性截止）和策略类型',
      '按标签筛选、搜索任务',
      '前置任务链式解锁，完成后自动解锁后续任务',
    ],
  },
  {
    icon: <Sparkles size={32} />,
    title: '抽卡与执行',
    desc: '在「抽卡」页面用抽卡机制选择当前要做的任务。',
    details: [
      '输入可用时间，自动匹配对应卡池（碎片/番茄/深度）',
      '点击「祈愿」随机抽取 3 个任务供你选择',
      '选中后启动番茄钟计时，专注执行',
      '可「另寻天命」换一批任务',
    ],
  },
  {
    icon: <BookOpen size={32} />,
    title: '知识库',
    desc: '在「知识库」页面管理你的学习笔记和知识点。',
    details: [
      '浏览已导入的笔记及其关联的知识点',
      '3D/2D 知识图谱可视化展示知识点关联',
      '链接分析页面查看断链和缺失引用',
      '拖拽上传 PDF/DOCX/PPT/MD 文件自动解析',
      'AI Agent 基于知识库内容回答问题',
    ],
  },
  {
    icon: <CalendarDays size={32} />,
    title: '日程安排',
    desc: '在「日程」页面规划每日时间表。',
    details: [
      '10 个预设时段覆盖全天（早读→晚自习）',
      '每个时段可分配不同活动（学习、工作、运动等）',
      '支持自定义活动选项',
      '切换日期查看和编辑不同天的安排',
    ],
  },
  {
    icon: <Settings size={32} />,
    title: '个性化设置',
    desc: '在「设置」页面配置你的偏好。',
    details: [
      '配置 LLM API（用于 AI 分析建议）',
      '配置 MinerU 服务地址（文档解析）',
      '自定义主题颜色和深色/浅色模式',
      '本引导可在设置中随时重新打开',
    ],
  },
];

interface UserGuideProps {
  open: boolean;
  onClose: () => void;
}

export default function UserGuide({ open, onClose }: UserGuideProps) {
  const [step, setStep] = useState(0);
  const total = STEPS.length;
  const current = STEPS[step];

  const handleClose = () => {
    markGuideSeen();
    onClose();
  };

  const handleFinish = () => {
    markGuideSeen();
    onClose();
    setStep(0);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          style={{
            position: 'fixed', inset: 0, zIndex: 200,
            background: 'rgba(5,5,16,0.85)',
            backdropFilter: 'blur(20px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 40, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ type: 'spring', damping: 22, stiffness: 250 }}
            style={{
              background: 'linear-gradient(180deg, #1a2038 0%, #0f1422 100%)',
              border: '1px solid rgba(240,192,64,0.12)',
              borderRadius: 24,
              padding: '36px 40px',
              maxWidth: 520, width: '90vw',
              position: 'relative',
              boxShadow: '0 32px 80px rgba(0,0,0,0.5)',
            }}
          >
            {/* Close */}
            <button
              onClick={handleClose}
              style={{
                position: 'absolute', top: 14, right: 14,
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '50%', width: 32, height: 32,
                cursor: 'pointer', color: '#6b6480',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <X size={16} />
            </button>

            {/* Step indicator */}
            <div style={{
              display: 'flex', gap: 6, marginBottom: 24,
              justifyContent: 'center',
            }}>
              {Array.from({ length: total }).map((_, i) => (
                <div
                  key={i}
                  style={{
                    width: i === step ? 24 : 8, height: 8, borderRadius: 4,
                    background: i === step
                      ? 'linear-gradient(90deg, #f0c040, #d4a843)'
                      : 'rgba(255,255,255,0.1)',
                    transition: 'all 0.3s ease',
                  }}
                />
              ))}
            </div>

            {/* Icon */}
            <div style={{
              width: 64, height: 64, borderRadius: 16,
              background: 'rgba(240,192,64,0.1)',
              border: '1px solid rgba(240,192,64,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 20px',
              color: '#f0c040',
            }}>
              {current.icon}
            </div>

            {/* Title */}
            <h2 style={{
              fontSize: 22, fontWeight: 700, color: '#f0e8da',
              textAlign: 'center', marginBottom: 8,
            }}>
              {current.title}
            </h2>

            {/* Description */}
            <p style={{
              fontSize: 14, color: '#a8a0b8', textAlign: 'center',
              lineHeight: 1.6, marginBottom: 20,
            }}>
              {current.desc}
            </p>

            {/* Detail list */}
            <div style={{
              background: 'rgba(255,255,255,0.03)',
              borderRadius: 12, padding: '16px 20px',
              display: 'flex', flexDirection: 'column', gap: 8,
            }}>
              {current.details.map((d, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'flex-start', gap: 8,
                  fontSize: 13, color: '#f0e8da', lineHeight: 1.5,
                }}>
                  <span style={{ color: '#f0c040', flexShrink: 0 }}>✦</span>
                  <span>{d}</span>
                </div>
              ))}
            </div>

            {/* Navigation */}
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', marginTop: 24,
            }}>
              <div style={{ fontSize: 12, color: '#6b6480' }}>
                {step + 1} / {total}
              </div>

              <div style={{ display: 'flex', gap: 8 }}>
                {step > 0 && (
                  <button
                    onClick={() => setStep(step - 1)}
                    style={{
                      padding: '8px 18px', borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.1)',
                      background: 'rgba(255,255,255,0.03)',
                      color: '#a8a0b8', fontSize: 13, fontWeight: 600,
                      cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    <ChevronLeft size={14} />
                    上一步
                  </button>
                )}

                {step < total - 1 ? (
                  <button
                    onClick={() => setStep(step + 1)}
                    style={{
                      padding: '8px 22px', borderRadius: 8, border: 'none',
                      background: 'linear-gradient(135deg, #f0c040, #c99f2e)',
                      color: '#0a0e1a', fontSize: 13, fontWeight: 700,
                      cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    下一步
                    <ChevronRight size={14} />
                  </button>
                ) : (
                  <button
                    onClick={handleFinish}
                    style={{
                      padding: '8px 22px', borderRadius: 8, border: 'none',
                      background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                      color: '#fff', fontSize: 13, fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    ✅ 开始使用
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
