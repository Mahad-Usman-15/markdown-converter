export type InputKind = 'pdf' | 'website' | 'text';
export type Limits = { max_pdf_bytes?: number; max_text_chars?: number; max_txt_bytes?: number };
export type Result = { markdown: string; title?: string; warnings?: string[] };
const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
export const apiConfigured = !!base;
export async function getLimits(signal: AbortSignal): Promise<Limits> {
  if (!base) return {};
  const r = await fetch(`${base}/config`, { signal });
  if (!r.ok) throw new Error('Could not load upload limits. Please retry.');
  return r.json();
}
export function formatText(text: string): string {
  // Conservative: retain words and existing Markdown, normalize whitespace only.
  return text.replace(/\r\n?/g, '\n').split('\n').map(l => l.trimEnd()).join('\n').replace(/\n{3,}/g, '\n\n').trim();
}
export function validUrl(value: string): boolean {
  try { const u = new URL(value); return ['http:', 'https:'].includes(u.protocol) && !!u.hostname && !u.username && !u.password; } catch { return false; }
}
function wait(ms: number, signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal.aborted) return reject(new DOMException('Aborted', 'AbortError'));
    const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve(); }, ms);
    signal.addEventListener('abort', abort, { once: true });
  });
}
export async function convertRemote(kind: InputKind, file: File | null, url: string, signal: AbortSignal, stage: (s: string) => void): Promise<Result> {
  if (!base) throw new Error('PDF and webpage conversion are not connected yet. You can convert plain text now.');
  const data = new FormData(); data.set('kind', kind);
  if (file && kind === 'pdf') data.set('file', file);
  if (kind === 'website') data.set('url', url.trim());
  stage(kind === 'pdf' ? 'Uploading your PDF…' : 'Reading the webpage…');
  const response = await fetch(`${base}/conversions`, { method: 'POST', body: data, signal });
  if (!response.ok) throw new Error(response.status === 413 ? 'This input exceeds the supported size. Try a smaller file.' : 'Could not start conversion. Check your input and try again.');
  const { job_id } = await response.json();
  if (typeof job_id !== 'string' || !job_id) throw new Error('The conversion service returned an invalid job. Please retry.');
  const deadline = Date.now() + 15 * 60 * 1000;
  let failures = 0;
  while (Date.now() < deadline) {
    await wait(1500, signal);
    let r: Response;
    try { r = await fetch(`${base}/conversions/${encodeURIComponent(job_id)}`, { signal }); }
    catch (e) { if (signal.aborted) throw e; if (++failures > 4) throw new Error('Connection lost. Please try again.'); stage('Reconnecting…'); continue; }
    if ([404, 410].includes(r.status)) throw new Error('This conversion was interrupted. Please try again.');
    if (r.status >= 500 && ++failures <= 4) { stage('Reconnecting…'); continue; }
    if (!r.ok) throw new Error('Could not check conversion progress. Please retry.');
    failures = 0;
    const job = await r.json();
    if (job.status === 'failed') throw new Error(typeof job.message === 'string' ? job.message : 'Conversion failed. Please try again.');
    if (job.status === 'completed') {
      if (typeof job.markdown !== 'string' || !job.markdown.trim()) throw new Error('No readable content was found. Try another input.');
      return { markdown: job.markdown, title: typeof job.title === 'string' ? job.title : undefined, warnings: Array.isArray(job.warnings) ? job.warnings.filter((x: unknown) => typeof x === 'string') : [] };
    }
    stage(job.stage === 'ocr' ? 'Reading scanned pages…' : kind === 'pdf' ? 'Reading your PDF…' : 'Reading the webpage…');
  }
  throw new Error('This conversion is taking too long. Please try a smaller input.');
}
