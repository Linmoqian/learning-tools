import type { Note } from './knowledge';

// ===== 支持的文件类型 =====
export const ACCEPTED_TYPES = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
  'application/vnd.ms-powerpoint': '.ppt',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'application/msword': '.doc',
  'text/markdown': '.md',
  'text/plain': '.md',
} as const;

export const ACCEPTED_EXTENSIONS = '.pdf,.ppt,.pptx,.doc,.docx,.md';

// ===== 科目关键词检测 =====
const SUBJECT_KEYWORDS: Record<string, string[]> = {
  '高数': ['极限', '导数', '积分', '微分', '函数', '微积分', '定积分', '不定积分', '泰勒', '洛必达', '中值定理', '数列', '无穷小', '连续', '间断'],
  '线代': ['矩阵', '行列式', '向量', '特征值', '特征向量', '线性方程组', '秩', '克莱姆', '齐次', '正交', '对角化'],
  '大物': ['力学', '热学', '电磁', '光学', '振动', '波动', '质点', '刚体', '转动惯量', '动量', '能量守恒', '电场', '磁场', '干涉', '衍射'],
  '电子技术': ['电路', '二极管', '三极管', '逻辑门', '布尔代数', '放大器', '运算放大器', '数字电路', '组合逻辑', '时序逻辑', 'MOSFET', 'BJT'],
  '计算机': ['算法', '数据结构', '网络', '操作系统', '进程', '线程', '内存', '排序', '查找', 'TCP', 'UDP', 'HTTP', '二叉树', '链表'],
  '英语四级': ['vocabulary', 'listening', 'reading', 'writing', 'translation', '四级', 'CET', '英语', 'grammar'],
};

function detectSubject(text: string): string {
  const lower = text.toLowerCase();
  const scores: Record<string, number> = {};
  for (const [subject, keywords] of Object.entries(SUBJECT_KEYWORDS)) {
    scores[subject] = keywords.reduce((acc, kw) => acc + (lower.includes(kw.toLowerCase()) ? 1 : 0), 0);
  }
  const best = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];
  return best && best[1] > 0 ? best[0] : '计算机';
}

// ===== WikiLink 提取 =====
export function extractWikiLinks(text: string): string[] {
  const regex = /\[\[([^\]]+)\]\]/g;
  const links: string[] = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    const name = match[1].trim();
    if (name && !links.includes(name)) links.push(name);
  }
  return links;
}

// ===== 文件解析器 =====
export interface ParsedFile {
  name: string;
  content: string;
}

export async function parseFile(file: File): Promise<ParsedFile> {
  const ext = file.name.split('.').pop()?.toLowerCase();

  switch (ext) {
    case 'pdf':
      return parsePDF(file);
    case 'docx':
    case 'doc':
      return parseDOCX(file);
    case 'pptx':
    case 'ppt':
      return parsePPTX(file);
    case 'md':
      return parseMD(file);
    default:
      throw new Error(`不支持的文件格式: .${ext}`);
  }
}

export function fileToNoteInput(parsed: ParsedFile, existingKpNames: string[]): Omit<Note, 'id'> {
  const wikilinks = extractWikiLinks(parsed.content);
  // 只保留指向已有知识点的链接
  const validLinks = wikilinks.filter(w => existingKpNames.includes(w));
  // 从文件名提取第一行作为标题
  const title = parsed.name.replace(/\.(pdf|docx|doc|pptx|ppt|md)$/i, '').replace(/[_-]/g, ' ');
  const subject = detectSubject(parsed.content);

  return {
    name: parsed.name,
    title,
    subject,
    wikiLinks: validLinks,
    content: parsed.content.slice(0, 2000),
  };
}

// ---- PDF ----
async function parsePDF(file: File): Promise<ParsedFile> {
  const pdfjsLib = await import('pdfjs-dist');
  pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`;

  const buffer = await file.arrayBuffer();
  const doc = await pdfjsLib.getDocument({ data: buffer }).promise;
  const pages: string[] = [];

  for (let i = 1; i <= Math.min(doc.numPages, 20); i++) {
    const page = await doc.getPage(i);
    const content = await page.getTextContent();
    const text = content.items.map((item: any) => item.str).join(' ');
    pages.push(text);
  }

  return { name: file.name, content: pages.join('\n\n') };
}

// ---- DOCX ----
async function parseDOCX(file: File): Promise<ParsedFile> {
  const mammoth = await import('mammoth');
  const buffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer: buffer });
  return { name: file.name, content: result.value };
}

// ---- PPTX ----
async function parsePPTX(file: File): Promise<ParsedFile> {
  const JSZip = await import('jszip');
  const buffer = await file.arrayBuffer();
  const zip = await JSZip.loadAsync(buffer);

  const slideFiles = Object.keys(zip.files)
    .filter(name => name.startsWith('ppt/slides/slide') && name.endsWith('.xml'))
    .sort();

  const texts: string[] = [];
  for (const slideName of slideFiles) {
    const slideXml = await zip.files[slideName].async('string');
    const textMatches = slideXml.match(/<a:t[^>]*>([^<]+)<\/a:t>/g) || [];
    const slideText = textMatches.map((m: string) => m.replace(/<[^>]+>/g, '')).join(' ');
    if (slideText.trim()) texts.push(slideText);
  }

  return { name: file.name, content: texts.join('\n\n') };
}

// ---- MD ----
async function parseMD(file: File): Promise<ParsedFile> {
  const text = await file.text();
  return { name: file.name, content: text };
}
