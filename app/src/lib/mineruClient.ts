const SERVER_URL = 'http://127.0.0.1:8899';

export interface MinerUResult {
  name: string;
  title: string;
  content: string;
  images: string[];
  error?: string;
}

let serverOnline = false;

export async function checkMineruServer(): Promise<boolean> {
  try {
    const resp = await fetch(`${SERVER_URL}/health`, { signal: AbortSignal.timeout(3000) });
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

  const resp = await fetch(`${SERVER_URL}/convert`, {
    method: 'POST',
    body: formData,
    signal: AbortSignal.timeout(300_000), // 5min timeout for large files
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: `${resp.status} ${resp.statusText}` }));
    throw new Error(err.error || '转换失败');
  }

  return resp.json();
}

export function getImageUrl(filename: string): string {
  return `${SERVER_URL}/images/${filename}`;
}
