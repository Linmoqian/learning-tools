import { FormEvent } from 'react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';

interface TaskFormData {
  name: string;
  description: string;
  estimatedTime: number;
  deadline: string;
  resistance: string;
  energyRequired: string;
  priority: number;
  repeatType: string;
  taskProfile: string;
  tags: string;
  prerequisiteIds: string;
}

interface TaskFormProps {
  data: TaskFormData;
  onChange: (data: TaskFormData) => void;
  onSubmit: () => void;
  onClose: () => void;
  title: string;
  availableTasks?: Array<{ id: number; name: string }>;
}

export default function TaskForm({ data, onChange, onSubmit, onClose, title, availableTasks }: TaskFormProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const update = (partial: Partial<TaskFormData>) => onChange({ ...data, ...partial });

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
    >
      <motion.form
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        onSubmit={handleSubmit}
        style={{
          background: 'linear-gradient(180deg, #1a2038, #0f1422)',
          border: '1px solid rgba(240,192,64,0.15)',
          borderRadius: 20,
          padding: '28px 32px',
          width: 460,
          maxHeight: '80vh',
          overflowY: 'auto',
          position: 'relative',
        }}
      >
        <button
          type="button"
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            background: 'none',
            border: 'none',
            color: '#a8a0b8',
            cursor: 'pointer',
            padding: 4,
          }}
        >
          <X size={20} />
        </button>

        <h3 style={{ fontSize: 20, fontWeight: 700, color: '#f0e8da', marginBottom: 20 }}>
          {title}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Field label="任务名称" required>
            <input
              value={data.name}
              onChange={e => update({ name: e.target.value })}
              placeholder="例如：复习高数第七章"
              style={inputStyle}
              autoFocus
            />
          </Field>

          <Field label="描述">
            <textarea
              value={data.description}
              onChange={e => update({ description: e.target.value })}
              placeholder="任务描述（可选）"
              rows={2}
              style={{ ...inputStyle, resize: 'vertical', minHeight: 50 }}
            />
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <Field label="预计时间 (分钟)">
              <input
                type="number"
                value={data.estimatedTime}
                onChange={e => update({ estimatedTime: Math.max(1, parseInt(e.target.value) || 25) })}
                min={1}
                max={480}
                style={inputStyle}
              />
            </Field>

            <Field label="优先级 (1-10)">
              <input
                type="number"
                value={data.priority}
                onChange={e => update({ priority: Math.min(10, Math.max(1, parseInt(e.target.value) || 5)) })}
                min={1}
                max={10}
                style={inputStyle}
              />
            </Field>
          </div>

          <Field label="截止日期">
            <input
              type="date"
              value={data.deadline}
              onChange={e => update({ deadline: e.target.value })}
              style={inputStyle}
            />
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <Field label="心理阻力">
              <select
                value={data.resistance}
                onChange={e => update({ resistance: e.target.value })}
                style={inputStyle}
              >
                <option value="low">🟢 低阻力</option>
                <option value="medium">🟡 中阻力</option>
                <option value="high">🔴 高阻力</option>
              </select>
            </Field>

            <Field label="所需精力">
              <select
                value={data.energyRequired}
                onChange={e => update({ energyRequired: e.target.value })}
                style={inputStyle}
              >
                <option value="low">🔋 低精力</option>
                <option value="medium">🔋🔋 中精力</option>
                <option value="high">🔋🔋🔋 高精力</option>
              </select>
            </Field>
          </div>

          <Field label="重复类型">
            <select
              value={data.repeatType}
              onChange={e => update({ repeatType: e.target.value })}
              style={inputStyle}
            >
              <option value="none">不重复</option>
              <option value="daily">每日</option>
              <option value="weekly">每周</option>
              <option value="accumulation">复习</option>
            </select>
          </Field>

          <Field label="任务策略">
            <select
              value={data.taskProfile}
              onChange={e => update({ taskProfile: e.target.value })}
              style={inputStyle}
            >
              <option value="deadline_flexible">柔性截止</option>
              <option value="deadline_progressive">渐进式截止</option>
              <option value="weekly_routine">每周例行</option>
              <option value="daily_habit">每日习惯</option>
            </select>
          </Field>

          <Field label="标签">
            <input
              value={data.tags}
              onChange={e => update({ tags: e.target.value })}
              placeholder="标签，用逗号分隔"
              style={inputStyle}
            />
          </Field>

          {availableTasks && availableTasks.length > 0 && (
            <Field label="前置任务 ID">
              <input
                value={data.prerequisiteIds}
                onChange={e => update({ prerequisiteIds: e.target.value })}
                placeholder="用逗号分隔任务 ID，例如：1, 2, 3"
                style={inputStyle}
              />
            </Field>
          )}
        </div>

        <div style={{ display: 'flex', gap: 12, marginTop: 24, justifyContent: 'flex-end' }}>
          <motion.button
            type="button"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              padding: '8px 20px',
              color: '#a8a0b8',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            取消
          </motion.button>
          <motion.button
            type="submit"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{
              background: 'linear-gradient(135deg, #f0c040, #c99f2e)',
              border: 'none',
              borderRadius: 8,
              padding: '8px 24px',
              color: '#0a0e1a',
              fontWeight: 700,
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            保存
          </motion.button>
        </div>
      </motion.form>
    </motion.div>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: 12, color: '#a8a0b8', marginBottom: 4 }}>
        {label}
        {required && <span style={{ color: '#e74c3c', marginLeft: 2 }}>*</span>}
      </label>
      {children}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  borderRadius: 8,
  border: '1px solid rgba(255,255,255,0.1)',
  background: 'rgba(255,255,255,0.05)',
  color: '#f0e8da',
  fontSize: 13,
  outline: 'none',
  fontFamily: 'inherit',
  boxSizing: 'border-box',
};
