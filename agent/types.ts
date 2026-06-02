// ===== Agent Types =====

export const AGENT_TYPES = [
  'note_organizer',
  'knowledge_extractor',
  'structure_reviewer',
  'content_reviewer',
  'knowledge_qa',
] as const;
export type AgentType = (typeof AGENT_TYPES)[number];

export const AGENT_LABELS: Record<AgentType, string> = {
  note_organizer: '笔记整理',
  knowledge_extractor: '知识点整理',
  structure_reviewer: '结构审查',
  content_reviewer: '内容审查',
  knowledge_qa: '知识问答',
};

export const AGENT_DESCRIPTIONS: Record<AgentType, string> = {
  note_organizer: '对笔记内容进行结构化整理、修正错别字、补充关键概念',
  knowledge_extractor: '从笔记中提取核心知识点，建立知识点间的关联关系',
  structure_reviewer: '审查笔记的章节结构和逻辑层次，提出结构优化建议',
  content_reviewer: '审查内容的准确性和完整性，检查概念错误和表述问题',
  knowledge_qa: '基于知识库内容回答你的学习问题',
};

export type AIProvider = 'claude' | 'openai';

export const PROVIDER_LABELS: Record<AIProvider, string> = {
  claude: 'Claude',
  openai: 'OpenAI',
};

export const PROVIDER_MODELS: Record<AIProvider, string[]> = {
  claude: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'],
  openai: ['gpt-4o', 'gpt-4o-mini'],
};

export const DEFAULT_MODELS: Record<AIProvider, string> = {
  claude: 'claude-sonnet-4-20250514',
  openai: 'gpt-4o',
};

export interface RunAgentRequest {
  agentType: AgentType;
  noteContent: string;
  provider?: AIProvider;
  model?: string;
}

export interface AgentResult {
  content: string;
  model: string;
  provider: AIProvider;
}

export type ApiKeyStatus = Record<AIProvider, boolean>;

export interface AgentError {
  message: string;
  code: 'missing_key' | 'api_error' | 'network_error' | 'parse_error' | 'timeout';
}
