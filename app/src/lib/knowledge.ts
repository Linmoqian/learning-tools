import { useMemo, useState, useCallback, useEffect } from 'react';

// ===== Subjects =====
export const SUBJECTS = [
  '高数',
  '线代',
  '大物',
  '电子技术',
  '计算机',
  '英语四级',
] as const;
export type Subject = (typeof SUBJECTS)[number];

export const SUBJECT_COLORS: Record<string, string> = {
  '高数': '#e74c3c',
  '线代': '#9b59b6',
  '大物': '#3498db',
  '电子技术': '#e67e22',
  '计算机': '#2ecc71',
  '英语四级': '#f1c40f',
};

// ===== Data Model =====
export interface KnowledgePoint {
  id: string;
  name: string;
  subject: string;
  description: string;
  linkedFrom: string[];
  relatedPoints: string[];
}

export interface Note {
  id: string;
  name: string;
  subject: string;
  title: string;
  wikiLinks: string[];
  content: string;
  images?: string[];
}

export interface LinkIssue {
  type: 'broken_link' | 'missing_reference';
  noteId: string;
  noteName: string;
  noteSubject: string;
  targetName: string;
}

export interface SubjectLinkStats {
  notes: number;
  knowledgePoints: number;
  links: number;
  valid: number;
  broken: number;
}

// ===== Mock Knowledge Points =====
const KNOWLEDGE_POINTS_DATA: Record<string, Omit<KnowledgePoint, 'id' | 'subject'>[]> = {
  '高数': [
    { name: '函数的概念与基本要素', description: '函数的定义、定义域、值域、对应法则', linkedFrom: [], relatedPoints: ['数列的极限'] },
    { name: '数列的极限', description: '数列极限的定义、性质与收敛判别', linkedFrom: [], relatedPoints: ['函数的极限与运算法则'] },
    { name: '函数的极限与运算法则', description: '极限的四则运算、复合函数极限', linkedFrom: [], relatedPoints: ['极限存在准则与重要极限'] },
    { name: '极限存在准则与重要极限', description: '夹逼准则、单调有界准则、两个重要极限', linkedFrom: [], relatedPoints: ['无穷小与无穷大'] },
    { name: '无穷小与无穷大', description: '无穷小的阶、等价无穷小替换', linkedFrom: [], relatedPoints: ['函数的连续性与间断点'] },
    { name: '函数的连续性与间断点', description: '连续定义、间断点分类、闭区间连续性质', linkedFrom: [], relatedPoints: ['求导法则与基本公式'] },
    { name: '求导法则与基本公式', description: '基本求导公式、四则运算、链式法则', linkedFrom: [], relatedPoints: ['导数应用——曲率与函数形态'] },
    { name: '不定积分的概念与性质', description: '原函数、不定积分、线性性质', linkedFrom: [], relatedPoints: ['分部积分法'] },
    { name: '定积分的概念与牛顿-莱布尼兹公式', description: '定积分的定义、积分上限函数、NL公式', linkedFrom: [], relatedPoints: ['定积分的应用——面积计算'] },
    { name: '向量的数量积', description: '点积定义、投影、夹角计算', linkedFrom: [], relatedPoints: [] },
  ],
  '线代': [
    { name: '行列式的定义与性质', description: '行列式的展开、性质、计算方法', linkedFrom: [], relatedPoints: ['克莱姆法则'] },
    { name: '克莱姆法则', description: '用行列式计算线性方程组', linkedFrom: [], relatedPoints: ['矩阵的运算'] },
    { name: '矩阵的运算', description: '矩阵加减法、乘法、转置、逆矩阵', linkedFrom: [], relatedPoints: ['矩阵的秩'] },
    { name: '矩阵的秩', description: '秩的定义、行阶梯形、秩的计算', linkedFrom: [], relatedPoints: ['线性方程组的解的结构'] },
    { name: '线性方程组的解的结构', description: '齐次/非齐次方程组解的结构、基础解系', linkedFrom: [], relatedPoints: ['特征值与特征向量'] },
    { name: '特征值与特征向量', description: '特征值的定义、求解、对角化', linkedFrom: [], relatedPoints: [] },
  ],
  '大物': [
    { name: '质点运动描述的物理量', description: '位置矢量、速度、加速度、运动方程', linkedFrom: [], relatedPoints: ['质点运动学两类问题与例题'] },
    { name: '自然坐标系与加速度分解', description: '切向加速度、法向加速度、曲率半径', linkedFrom: [], relatedPoints: ['圆周运动的角量与线量'] },
    { name: '动量定理与解题步骤', description: '冲量、动量、动量定理及其应用', linkedFrom: [], relatedPoints: ['角动量定理与守恒定律'] },
    { name: '刚体定轴转动定律与转动惯量', description: '转动定律、转动惯量的计算', linkedFrom: [], relatedPoints: ['角动量定理与守恒定律'] },
    { name: '三大守恒律复习与简谐振动入门', description: '动量、角动量、机械能守恒', linkedFrom: [], relatedPoints: ['旋转矢量法与简谐振动描述'] },
    { name: '静电场与电场强度', description: '库仑定律、电场叠加原理、电场强度计算', linkedFrom: [], relatedPoints: ['电通量与高斯定理'] },
    { name: '热力学第一定律与四大过程', description: '等温、等容、等压、绝热过程分析', linkedFrom: [], relatedPoints: ['热力学循环与效率计算'] },
    { name: '光的干涉原理与两类装置', description: '杨氏双缝、薄膜干涉、光程差', linkedFrom: [], relatedPoints: ['半波损失的原理与判断'] },
    { name: '惠更斯-菲涅耳原理与衍射分类', description: '衍射原理、单缝衍射、光栅衍射', linkedFrom: [], relatedPoints: ['圆孔衍射与光学仪器分辨本领'] },
  ],
  '电子技术': [
    { name: '半导体基础与PN结', description: '本征半导体、掺杂、PN结的形成', linkedFrom: [], relatedPoints: ['二极管特性与等效模型'] },
    { name: '二极管特性与等效模型', description: '伏安特性、理想模型、恒压降模型', linkedFrom: [], relatedPoints: ['半导体三极管原理'] },
    { name: '半导体三极管原理', description: 'BJT结构、放大条件、三种组态', linkedFrom: [], relatedPoints: ['三极管放大电路——静态分析'] },
    { name: '布尔代数与逻辑门电路', description: '基本逻辑运算、逻辑门符号、真值表', linkedFrom: [], relatedPoints: ['逻辑函数化简——公式法与卡诺图'] },
    { name: '组合逻辑电路分析与设计', description: '编码器、译码器、数据选择器', linkedFrom: [], relatedPoints: ['编码器与集成电路实现'] },
    { name: '数字信号与编码技术', description: '进制转换、BCD码、补码运算', linkedFrom: [], relatedPoints: [] },
  ],
  '计算机': [
    { name: '数据结构与算法基础', description: '数组、链表、栈、队列、树', linkedFrom: [], relatedPoints: ['排序与查找算法'] },
    { name: '排序与查找算法', description: '冒泡、快排、归并、二分查找', linkedFrom: [], relatedPoints: [] },
    { name: '计算机网络分层模型', description: 'OSI七层、TCP/IP四层、各层功能', linkedFrom: [], relatedPoints: ['TCP与UDP协议'] },
    { name: 'TCP与UDP协议', description: 'TCP三次握手、流量控制、UDP特点', linkedFrom: [], relatedPoints: [] },
    { name: '进程与线程管理', description: '进程状态、调度算法、同步互斥', linkedFrom: [], relatedPoints: ['内存管理'] },
    { name: '内存管理', description: '分页分段、虚拟内存、页面置换', linkedFrom: [], relatedPoints: [] },
  ],
  '英语四级': [
    { name: '听力高频场景词汇', description: '校园、生活、学术场景常见词汇', linkedFrom: [], relatedPoints: [] },
    { name: '阅读长难句分析', description: '从句识别、主干提取、快速阅读', linkedFrom: [], relatedPoints: ['写作模板与句型'] },
    { name: '写作模板与句型', description: '议论文框架、常用句式、过渡词', linkedFrom: [], relatedPoints: ['翻译高频考点'] },
    { name: '翻译高频考点', description: '中国文化、成语翻译、句型转换', linkedFrom: [], relatedPoints: [] },
  ],
};

// ===== Mock Notes =====
const NOTES_DATA: Record<string, Omit<Note, 'id'>[]> = {
  '高数': [
    {
      name: '01-01_函数的概念与基本要素',
      title: '函数的概念与基本要素',
      subject: '高数',
      wikiLinks: ['函数的概念与基本要素', '数列的极限'],
      content: '函数是数学中最重要的基本概念之一。本章从函数的定义出发，介绍定义域、值域、对应法则三要素...',
    },
    {
      name: '01-02_数列的极限',
      title: '数列的极限',
      subject: '高数',
      wikiLinks: ['数列的极限', '函数的极限与运算法则', '无穷小与无穷大'],
      content: '极限是高等数学的基石。数列极限的定义使用ε-N语言精确描述...',
    },
    {
      name: '02-01_求导法则与基本公式',
      title: '求导法则与基本公式',
      subject: '高数',
      wikiLinks: ['求导法则与基本公式', '函数的连续性与间断点', '不定积分的概念与性质'],
      content: '导数是函数变化率的度量。本章系统介绍基本求导公式和运算法则...',
    },
    {
      name: '05-02_定积分的概念与牛顿-莱布尼兹公式',
      title: '定积分的概念',
      subject: '高数',
      wikiLinks: ['定积分的概念与牛顿-莱布尼兹公式', '不定积分的概念与性质', '定积分的应用——面积计算'],
      content: '定积分是积分学的核心概念，通过"分割-近似-求和-取极限"的过程定义...',
    },
  ],
  '线代': [
    {
      name: '01_行列式的定义与性质',
      title: '行列式',
      subject: '线代',
      wikiLinks: ['行列式的定义与性质', '克莱姆法则'],
      content: '行列式是线性代数中的重要工具，由矩阵的n个n维行向量张成的平行多面体的有向体积...',
    },
    {
      name: '02_矩阵的运算',
      title: '矩阵运算',
      subject: '线代',
      wikiLinks: ['矩阵的运算', '矩阵的秩', '克莱姆法则'],
      content: '矩阵是线性代数的核心研究对象。本章介绍矩阵的基本运算和性质...',
    },
    {
      name: '03_线性方程组',
      title: '线性方程组',
      subject: '线代',
      wikiLinks: ['线性方程组的解的结构', '矩阵的秩', '克莱姆法则', '特征值与特征向量'],
      content: '线性方程组求解是线性代数最直接的应用。从Gauss消元法到解的结构分析...',
    },
  ],
  '大物': [
    {
      name: '01_质点运动描述的物理量',
      title: '质点运动学基础',
      subject: '大物',
      wikiLinks: ['质点运动描述的物理量', '自然坐标系与加速度分解'],
      content: '力学是物理学的基础。描述质点运动需要位置矢量、位移、速度、加速度等概念...',
    },
    {
      name: '05_动量定理与解题步骤',
      title: '动量与能量',
      subject: '大物',
      wikiLinks: ['动量定理与解题步骤', '三大守恒律复习与简谐振动入门'],
      content: '动量定理将力的时间累积效应与动量变化联系起来，是解决碰撞问题的核心工具...',
    },
    {
      name: '16_热力学第一定律与四大过程',
      title: '热力学基础',
      subject: '大物',
      wikiLinks: ['热力学第一定律与四大过程', '三大守恒律复习与简谐振动入门'],
      content: '热力学第一定律是能量守恒在热学中的体现：ΔU = Q + W...',
    },
    {
      name: '18_光的干涉原理与两类装置',
      title: '波动光学',
      subject: '大物',
      wikiLinks: ['光的干涉原理与两类装置', '惠更斯-菲涅耳原理与衍射分类'],
      content: '光的干涉是波动性的重要体现。杨氏双缝实验证明了光具有波动性...',
    },
  ],
  '电子技术': [
    {
      name: '01_半导体基础与PN结',
      title: '半导体器件基础',
      subject: '电子技术',
      wikiLinks: ['半导体基础与PN结', '二极管特性与等效模型'],
      content: '半导体是介于导体与绝缘体之间的材料。PN结是所有半导体器件的核心结构...',
    },
    {
      name: '08_布尔代数与逻辑门电路',
      title: '数字逻辑基础',
      subject: '电子技术',
      wikiLinks: ['布尔代数与逻辑门电路', '组合逻辑电路分析与设计', '数字信号与编码技术'],
      content: '布尔代数是数字电路的数学基础。基本逻辑运算包括与、或、非...',
    },
    {
      name: '10_组合逻辑电路分析与设计',
      title: '组合逻辑设计',
      subject: '电子技术',
      wikiLinks: ['组合逻辑电路分析与设计', '编码器与集成电路实现', '布尔代数与逻辑门电路'],
      content: '组合逻辑电路的输出仅取决于当前输入。设计步骤：分析需求→真值表→逻辑表达式→化简→电路图...',
    },
  ],
  '计算机': [
    {
      name: '01_数据结构基础',
      title: '数据结构概述',
      subject: '计算机',
      wikiLinks: ['数据结构与算法基础', '排序与查找算法'],
      content: '数据结构是计算机存储、组织数据的方式。常见类型：线性表、树、图、散列表...',
    },
    {
      name: '03_计算机网络',
      title: '计算机网络体系结构',
      subject: '计算机',
      wikiLinks: ['计算机网络分层模型', 'TCP与UDP协议'],
      content: '计算机网络通过分层模型实现复杂的通信功能。应用层→传输层→网络层→链路层→物理层...',
    },
    {
      name: '05_操作系统进程管理',
      title: '进程管理',
      subject: '计算机',
      wikiLinks: ['进程与线程管理', '内存管理'],
      content: '进程是程序的一次执行过程。操作系统通过进程控制块管理进程的生命周期...',
    },
  ],
  '英语四级': [
    {
      name: '01_听力高频场景',
      title: '听力训练',
      subject: '英语四级',
      wikiLinks: ['听力高频场景词汇'],
      content: '四级听力涵盖校园生活、学术讲座、新闻广播等场景。高频场景词汇是听力的基础...',
    },
    {
      name: '02_阅读长难句',
      title: '阅读理解',
      subject: '英语四级',
      wikiLinks: ['阅读长难句分析', '听力高频场景词汇'],
      content: '长难句分析能力直接影响阅读理解速度和准确度...',
    },
    {
      name: '03_写作模板',
      title: '写作与翻译',
      subject: '英语四级',
      wikiLinks: ['写作模板与句型', '翻译高频考点'],
      content: '四级写作要求30分钟内完成120-180词的短文。掌握常用模板和句型是快速成文的关键...',
    },
  ],
};

// ===== Build Knowledge Points Index =====
export function buildKnowledgePoints(): KnowledgePoint[] {
  const result: KnowledgePoint[] = [];
  let id = 1;

  for (const [subject, points] of Object.entries(KNOWLEDGE_POINTS_DATA)) {
    for (const p of points) {
      result.push({
        ...p,
        id: `kp_${id}`,
        subject,
        linkedFrom: [],
      });
      id++;
    }
  }
  return result;
}

// ===== Build Notes Index =====
export function buildNotes(): Note[] {
  const result: Note[] = [];
  let id = 1;

  for (const notes of Object.values(NOTES_DATA)) {
    for (const n of notes) {
      result.push({ ...n, id: `note_${id}` });
      id++;
    }
  }
  return result;
}

// ===== Build cross-references =====
export function buildReferences(notes: Note[], knowledgePoints: KnowledgePoint[]): Note[] {
  // Build reference index: knowledgePoint name -> note IDs
  const refIndex: Record<string, string[]> = {};
  for (const note of notes) {
    for (const link of note.wikiLinks) {
      if (!refIndex[link]) refIndex[link] = [];
      refIndex[link].push(note.id);
    }
  }

  // Update knowledge points with linkedFrom
  for (const kp of knowledgePoints) {
    kp.linkedFrom = refIndex[kp.name] || [];
  }

  return notes;
}

// ===== Analysis Algorithms (ported from Python) =====
export interface LinkAnalysisResult {
  totalNotes: number;
  totalKnowledgePoints: number;
  totalLinks: number;
  validLinks: number;
  brokenLinks: number;
  bySubject: Record<string, SubjectLinkStats>;
  brokenDetails: LinkIssue[];
  missingReferences: string[];
  knowledgePointNames: string[];
}

export function analyzeLinks(notes: Note[], knowledgePoints: KnowledgePoint[]): LinkAnalysisResult {
  const kpNames = new Set(knowledgePoints.map(kp => kp.name));
  const bySubject: Record<string, SubjectLinkStats> = {};
  const brokenDetails: LinkIssue[] = [];
  const missingRefs = new Set<string>();
  let totalLinks = 0;
  let validLinks = 0;

  for (const subject of SUBJECTS) {
    bySubject[subject] = {
      notes: 0, knowledgePoints: 0, links: 0, valid: 0, broken: 0,
    };
  }

  for (const note of notes) {
    if (bySubject[note.subject]) {
      bySubject[note.subject].notes++;
    }

    for (const link of note.wikiLinks) {
      totalLinks++;
      if (bySubject[note.subject]) {
        bySubject[note.subject].links++;
      }

      if (kpNames.has(link)) {
        validLinks++;
        if (bySubject[note.subject]) {
          bySubject[note.subject].valid++;
        }
      } else {
        if (bySubject[note.subject]) {
          bySubject[note.subject].broken++;
        }
        missingRefs.add(link);
        brokenDetails.push({
          type: 'broken_link',
          noteId: note.id,
          noteName: note.name,
          noteSubject: note.subject,
          targetName: link,
        });
      }
    }
  }

  const kpCounts: Record<string, number> = {};
  for (const kp of knowledgePoints) {
    kpCounts[kp.subject] = (kpCounts[kp.subject] || 0) + 1;
    if (bySubject[kp.subject]) {
      bySubject[kp.subject].knowledgePoints = kpCounts[kp.subject];
    }
  }

  return {
    totalNotes: notes.length,
    totalKnowledgePoints: knowledgePoints.length,
    totalLinks,
    validLinks,
    brokenLinks: brokenDetails.length,
    bySubject,
    brokenDetails,
    missingReferences: [...missingRefs].sort(),
    knowledgePointNames: [...kpNames],
  };
}

// ===== Graph data for visualization =====
export interface GraphNode {
  id: string;
  label: string;
  type: 'note' | 'knowledge';
  subject: string;
  radius: number;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function buildGraph(notes: Note[], knowledgePoints: KnowledgePoint[]): GraphData {
  const nodeMap = new Map<string, GraphNode>();
  const edges: GraphEdge[] = [];

  for (const note of notes) {
    nodeMap.set(note.id, {
      id: note.id,
      label: note.title.length > 8 ? note.title.slice(0, 8) + '…' : note.title,
      type: 'note',
      subject: note.subject,
      radius: 18,
    });
  }

  for (const kp of knowledgePoints) {
    nodeMap.set(kp.id, {
      id: kp.id,
      label: kp.name.length > 6 ? kp.name.slice(0, 6) + '…' : kp.name,
      type: 'knowledge',
      subject: kp.subject,
      radius: 14,
    });
  }

  for (const note of notes) {
    for (const link of note.wikiLinks) {
      const targetKp = knowledgePoints.find(kp => kp.name === link);
      if (targetKp) {
        edges.push({ source: note.id, target: targetKp.id });
      }
    }
  }

  return {
    nodes: [...nodeMap.values()],
    edges,
  };
}

// ===== Search =====
export interface SearchResult {
  type: 'note' | 'knowledge';
  id: string;
  name: string;
  subject: string;
  matchField: string;
}

export function searchItems(
  notes: Note[],
  knowledgePoints: KnowledgePoint[],
  query: string,
): SearchResult[] {
  const q = query.toLowerCase().trim();
  if (!q) return [];

  const results: SearchResult[] = [];

  for (const note of notes) {
    if (note.title.toLowerCase().includes(q) || note.name.toLowerCase().includes(q) || note.content.toLowerCase().includes(q)) {
      results.push({ type: 'note', id: note.id, name: note.title, subject: note.subject, matchField: '标题/内容' });
    }
  }

  for (const kp of knowledgePoints) {
    if (kp.name.toLowerCase().includes(q) || kp.description.toLowerCase().includes(q)) {
      results.push({ type: 'knowledge', id: kp.id, name: kp.name, subject: kp.subject, matchField: '名称/描述' });
    }
  }

  return results;
}

// ===== Subject Statistics =====
export interface SubjectStat {
  name: string;
  color: string;
  noteCount: number;
  kpCount: number;
  linkCount: number;
  validCount: number;
  brokenCount: number;
}

export function getSubjectStats(analysis: LinkAnalysisResult): SubjectStat[] {
  return SUBJECTS.map(name => {
    const s = analysis.bySubject[name] || { notes: 0, knowledgePoints: 0, links: 0, valid: 0, broken: 0 };
    return {
      name,
      color: SUBJECT_COLORS[name] || '#666',
      noteCount: s.notes,
      kpCount: s.knowledgePoints,
      linkCount: s.links,
      validCount: s.valid,
      brokenCount: s.broken,
    };
  });
}

// ===== React hooks =====
export interface NewNoteInput {
  name: string;
  title: string;
  subject: string;
  wikiLinks: string[];
  content: string;
  images?: string[];
}

// 是否是后端模式（数据由后端管理）
let backendMode = false;

export function isKnowledgeBackendMode(): boolean {
  return backendMode;
}

async function loadFromBackend(): Promise<{
  notes: Note[]; knowledgePoints: KnowledgePoint[]; analysis: LinkAnalysisResult;
  graph: GraphData; subjectStats: SubjectStat[];
} | null> {
  try {
    const api = await import('./api');

    const [notes, knowledgePoints, linkAnalysis, graphData, subjectStatsData] = await Promise.all([
      api.fetchNotes(),
      api.fetchKnowledgePoints(),
      api.fetchKnowledgeAnalysis().catch(() => null),
      api.fetchKnowledgeGraph().catch(() => null),
      api.fetchSubjectStats().catch(() => null),
    ]);

    backendMode = true;

    const analysis: LinkAnalysisResult = linkAnalysis || {
      totalNotes: notes.length,
      totalKnowledgePoints: knowledgePoints.length,
      totalLinks: 0,
      validLinks: 0,
      brokenLinks: 0,
      bySubject: {} as Record<string, SubjectLinkStats>,
      brokenDetails: [],
      missingReferences: [],
      knowledgePointNames: knowledgePoints.map(kp => kp.name),
    };

    const graph: GraphData = graphData || { nodes: [], edges: [] };

    const subjectStatsList: SubjectStat[] = subjectStatsData || SUBJECTS.map(name => ({
      name,
      color: SUBJECT_COLORS[name] || '#666',
      noteCount: 0, kpCount: 0, linkCount: 0, validCount: 0, brokenCount: 0,
    }));

    return { notes, knowledgePoints, analysis, graph, subjectStats: subjectStatsList };
  } catch {
    return null;
  }
}

export function useKnowledgeBase() {
  const [extraNotes, setExtraNotes] = useState<NewNoteInput[]>([]);
  const [backendData, setBackendData] = useState<{
    notes: Note[]; knowledgePoints: KnowledgePoint[];
    analysis: LinkAnalysisResult; graph: GraphData; subjectStats: SubjectStat[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  // 启动时尝试从后端加载
  useEffect(() => {
    loadFromBackend().then(data => {
      if (data) setBackendData(data);
      setLoading(false);
    });
  }, []);

  const addNotes = useCallback(async (notes: NewNoteInput[]) => {
    if (backendMode) {
      // 后端模式：写入 .md 文件
      const { createNote } = await import('./api');
      for (const note of notes) {
        try {
          await createNote({
            name: note.name,
            title: note.title,
            subject: note.subject,
            content: note.content,
            images: note.images,
          });
        } catch (e) {
          console.warn(`创建笔记失败: ${note.name}`, e);
        }
      }
      // 重新加载后端数据
      const data = await loadFromBackend();
      if (data) setBackendData(data);
    } else {
      setExtraNotes(prev => [...prev, ...notes]);
    }
  }, []);

  const data = useMemo(() => {
    // 后端优先
    if (backendData) return backendData;

    const baseNotes = buildNotes();
    const allNotes: Note[] = [
      ...baseNotes,
      ...extraNotes.map((n, i) => ({
        ...n,
        id: `upload_${Date.now()}_${i}`,
      })),
    ];
    const knowledgePoints = buildKnowledgePoints();
    buildReferences(allNotes, knowledgePoints);
    const analysisResult = analyzeLinks(allNotes, knowledgePoints);
    const graphResult = buildGraph(allNotes, knowledgePoints);
    const statsResult = getSubjectStats(analysisResult);

    return {
      notes: allNotes,
      knowledgePoints,
      analysis: analysisResult,
      graph: graphResult,
      subjectStats: statsResult,
    };
  }, [backendData, extraNotes]);

  return { ...data, addNotes, loading };
}
