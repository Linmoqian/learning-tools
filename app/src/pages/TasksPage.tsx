import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ListTodo, Plus, Search, Edit3, Trash2 } from 'lucide-react';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import { useStore } from '../lib/store';
import { Task } from '../lib/types';
import { createDefaultTask } from '../lib/algorithms';

export default function TasksPage() {
  const { data, dispatch } = useStore();
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [search, setSearch] = useState('');
  const [tagFilter, setTagFilter] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'daily',
    estimatedTime: 25,
    deadline: '',
    resistance: 'medium',
    energyRequired: 'medium',
    priority: 5,
    repeatType: 'none',
    taskProfile: 'deadline_flexible',
    tags: '',
    prerequisiteIds: '',
  });

  const availableTasks = useMemo(
    () => data.tasks.filter(t => !t.inDiscardPile),
    [data.tasks],
  );

  const filteredTasks = useMemo(() => {
    let list = availableTasks;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(t => t.name.toLowerCase().includes(q) || t.tags.some(tag => tag.includes(q)));
    }
    if (tagFilter) {
      list = list.filter(t => t.tags.includes(tagFilter));
    }
    return list.sort((a) => (a.completed ? 1 : -1));
  }, [availableTasks, search, tagFilter]);

  const allTags = useMemo(() => {
    const set = new Set<string>();
    data.tasks.forEach(t => t.tags.forEach(tag => set.add(tag)));
    return Array.from(set).sort();
  }, [data.tasks]);

  const handleAdd = () => {
    const prereqIds = formData.prerequisiteIds
      .split(',')
      .map(s => parseInt(s.trim()))
      .filter(n => !isNaN(n));

    const defaultTask = createDefaultTask();
    const task: Task = {
      ...defaultTask,
      id: 0,
      category: formData.category,
      name: formData.name,
      description: formData.description || undefined,
      estimatedTime: formData.estimatedTime,
      deadline: formData.deadline || undefined,
      resistance: formData.resistance,
      energyRequired: formData.energyRequired,
      priority: formData.priority,
      repeatType: formData.repeatType,
      taskProfile: formData.taskProfile,
      tags: formData.tags.split(',').map(s => s.trim()).filter(Boolean),
      prerequisiteIds: prereqIds,
      isUnlocked: prereqIds.length === 0,
    };

    if (editingTask) {
      dispatch({ type: 'UPDATE_TASK', task: { ...task, id: editingTask.id } });
    } else {
      dispatch({ type: 'ADD_TASK', task });
    }

    resetForm();
  };

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setFormData({
      name: task.name,
      description: task.description || '',
      category: task.category,
      estimatedTime: task.estimatedTime,
      deadline: task.deadline || '',
      resistance: task.resistance,
      energyRequired: task.energyRequired,
      priority: task.priority,
      repeatType: task.repeatType,
      taskProfile: task.taskProfile,
      tags: task.tags.join(', '),
      prerequisiteIds: task.prerequisiteIds.join(', '),
    });
    setShowForm(true);
  };

  const handleDelete = (id: number) => {
    dispatch({ type: 'DELETE_TASK', id });
  };

  const resetForm = () => {
    setShowForm(false);
    setEditingTask(null);
    setFormData({
      name: '',
      description: '',
      category: 'daily',
      estimatedTime: 25,
      deadline: '',
      resistance: 'medium',
      energyRequired: 'medium',
      priority: 5,
      repeatType: 'none',
      taskProfile: 'deadline_flexible',
      tags: '',
      prerequisiteIds: '',
    });
  };

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ListTodo size={24} color="#f0c040" />
          <h1 className="page-title" style={{ margin: 0 }}>任务管理</h1>
          <span style={{ color: '#6b6480', fontSize: 13 }}>({availableTasks.filter(t => !t.completed).length} 个活跃)</span>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => { resetForm(); setShowForm(true); }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 16px',
            borderRadius: 10,
            border: 'none',
            background: 'linear-gradient(135deg, #f0c040, #c99f2e)',
            color: '#0a0e1a',
            fontSize: 13,
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          <Plus size={16} />
          添加任务
        </motion.button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: 300 }}>
          <Search size={14} style={{ position: 'absolute', left: 10, top: 10, color: '#6b6480' }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="搜索任务..."
            style={{
              width: '100%',
              padding: '8px 10px 8px 32px',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(255,255,255,0.05)',
              color: '#f0e8da',
              fontSize: 13,
              outline: 'none',
            }}
          />
        </div>
        <select
          value={tagFilter}
          onChange={e => setTagFilter(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(255,255,255,0.05)',
            color: '#f0e8da',
            fontSize: 13,
            outline: 'none',
          }}
        >
          <option value="">全部标签</option>
          {allTags.map(tag => <option key={tag} value={tag}>#{tag}</option>)}
        </select>
      </div>

      {/* Task list */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center', flex: 1, alignContent: 'flex-start' }}>
        {filteredTasks.length === 0 ? (
          <div style={{ color: '#6b6480', fontSize: 14, padding: 40, textAlign: 'center' }}>
            {search || tagFilter ? '没有匹配的任务' : '还没有任务，点击右上角添加'}
          </div>
        ) : (
          filteredTasks.map((task, i) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              style={{ position: 'relative' }}
            >
              <TaskCard
                task={task}
                index={i}
                compact
                onClick={() => handleEdit(task)}
              />
              <div style={{ display: 'flex', gap: 4, marginTop: 6, justifyContent: 'center' }}>
                <button
                  onClick={() => handleEdit(task)}
                  style={{ ...iconBtnStyle }}
                >
                  <Edit3 size={12} />
                </button>
                <button
                  onClick={() => handleDelete(task.id)}
                  style={{ ...iconBtnStyle, color: '#e74c3c' }}
                >
                  <Trash2 size={12} />
                </button>
                {!task.completed && (
                  <button
                    onClick={() => {
                      dispatch({ type: 'COMPLETE_TASK', id: task.id });
                    }}
                    style={{ ...iconBtnStyle, color: '#27ae60' }}
                  >
                    ✅
                  </button>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Task form modal */}
      <AnimatePresence>
        {showForm && (
          <TaskForm
            data={formData}
            onChange={setFormData}
            onSubmit={handleAdd}
            onClose={resetForm}
            title={editingTask ? '✏️ 编辑任务' : '➕ 添加新任务'}
            availableTasks={data.tasks.map(t => ({ id: t.id, name: t.name }))}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

const iconBtnStyle: React.CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: 6,
  border: '1px solid rgba(255,255,255,0.1)',
  background: 'rgba(255,255,255,0.05)',
  color: '#a8a0b8',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: 11,
};
