export interface MinerUResult {
  name: string;
  title: string;
  content: string;
  images: string[];
  error?: string;
}

let serverUrl = 'http://127.0.0.1:8899';
let serverOnline = false;

export function setServerUrl(url: string) {
  serverUrl = url;
  // 切换服务器时重置状态
  serverOnline = false;
}

export function getServerUrl(): string {
  return serverUrl;
}

export async function checkMineruServer(): Promise<boolean> {
  try {
    const resp = await fetch(`${serverUrl}/health`, { signal: AbortSignal.timeout(3000) });
    const data = await resp.json();
    serverOnline = data.status === 'ok';
    return serverOnline;
  } catch {
    serverOnline = false;
    return false;
  }
}

export function isMineruOnline(): boolean {
  return serverOnline;
}

export async function convertWithMineru(file: File): Promise<MinerUResult> {
  const formData = new FormData();
  formData.append('file', file);

  const resp = await fetch(`${serverUrl}/convert`, {
    method: 'POST',
    body: formData,
    signal: AbortSignal.timeout(300_000),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: `${resp.status} ${resp.statusText}` }));
    throw new Error(err.error || '转换失败');
  }

  return resp.json();
}

export function getImageUrl(filename: string): string {
  return `${serverUrl}/images/${filename}`;
}
