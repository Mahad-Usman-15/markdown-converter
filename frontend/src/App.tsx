import { useEffect, useRef, useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { markdown as markdownLanguage } from '@codemirror/lang-markdown';
import { EditorView } from '@codemirror/view';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowDownToLine, ArrowRight, Check, CheckCircle2, ChevronRight, Clipboard, FileText, Globe2, LoaderCircle, Plus, Type, Upload, X, AlertCircle } from 'lucide-react';
import { apiConfigured, convertRemote, formatText, getLimits, validUrl, type InputKind, type Limits } from './conversion';
const tabs = [{ id: 'pdf' as const, name: 'PDF', icon: FileText }, { id: 'website' as const, name: 'Website', icon: Globe2 }, { id: 'text' as const, name: 'Plain text', icon: Type }];
const editorTheme = EditorView.theme({ '&': { background: 'transparent', fontSize: '14px' }, '.cm-content': { padding: '24px 8px', fontFamily: 'ui-monospace, Consolas, monospace', lineHeight: '1.65' }, '.cm-gutters': { background: 'transparent', border: 'none', color: '#858278' }, '.cm-scroller': { overflow: 'auto' }, '&.cm-focused': { outline: '2px solid #7b4936', outlineOffset: '-2px' } });
export default function App() {
  const [tab, setTab] = useState<InputKind>('pdf');
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState(''); const [text, setText] = useState('');
  const [limits, setLimits] = useState<Limits>({}); const [limitsReady, setLimitsReady] = useState(!apiConfigured);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [stage, setStage] = useState('');
  const [output, setOutput] = useState<string | null>(null); const [original, setOriginal] = useState('');
  const [title, setTitle] = useState(''); const [warnings, setWarnings] = useState<string[]>([]);
  const [view, setView] = useState('markdown'); const [copied, setCopied] = useState(false); const [dragging, setDragging] = useState(false);
  const pdfPicker = useRef<HTMLInputElement>(null); const txtPicker = useRef<HTMLInputElement>(null);
  const task = useRef<AbortController | null>(null); const lock = useRef(false); const resultHeading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { const ctl = new AbortController(); getLimits(ctl.signal).then(l => { setLimits(l); setLimitsReady(true); }).catch(() => { if (!ctl.signal.aborted) setError('Could not load upload limits. Reload the page to try again.'); }); return () => { ctl.abort(); task.current?.abort(); }; }, []);
  useEffect(() => { if (output !== null) resultHeading.current?.focus(); }, [original]);
  useEffect(() => { if (!copied) return; const timer = setTimeout(() => setCopied(false), 2000); return () => clearTimeout(timer); }, [copied]);
  const textTooLong = !!limits.max_text_chars && text.length > limits.max_text_chars;
  const ready = tab === 'pdf' ? !!file && limitsReady : tab === 'website' ? validUrl(url.trim()) : !!text.trim() && !textTooLong;
  async function pickPdf(f?: File) {
    if (!f) return; setError('');
    if (!f.name.toLowerCase().endsWith('.pdf')) return setError('Choose a PDF file.');
    if (limits.max_pdf_bytes && f.size > limits.max_pdf_bytes) return setError('This PDF exceeds the supported file size.');
    if (!f.size) return setError('This file is empty. Choose another PDF.');
    const signature = await f.slice(0, 1024).text();
    if (!signature.includes('%PDF-')) return setError('This file does not appear to be a valid PDF.');
    setFile(f);
  }
  async function pickText(f?: File) {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.txt')) return setError('Choose a .txt file.');
    if (limits.max_txt_bytes && f.size > limits.max_txt_bytes) return setError('This text file exceeds the supported size.');
    if (text.trim() && !window.confirm('Replace your current text with this file?')) return;
    try { const content = await f.text(); if (limits.max_text_chars && content.length > limits.max_text_chars) return setError('This text file exceeds the character limit.'); setText(content); setError(''); } catch { setError('Could not read this text file. Please try another.'); }
  }
  async function convert() {
    if (!ready || lock.current) return; lock.current = true; setBusy(true); setError('');
    const ctl = new AbortController(); task.current = ctl;
    try {
      setStage('Structuring your text…');
      const r = tab === 'text' ? { markdown: formatText(text), title: 'Plain text', warnings: [] } : await convertRemote(tab, file, url, ctl.signal, setStage);
      setOriginal(r.markdown); setOutput(r.markdown); setTitle(r.title || (tab === 'pdf' ? file!.name : url)); setWarnings(r.warnings || []); setView('markdown');
    } catch (e) { if (!ctl.signal.aborted) setError(e instanceof Error ? e.message : 'Could not convert this input. Please try again.'); }
    finally { lock.current = false; setBusy(false); }
  }
  function reset() { if (output !== original && !window.confirm('Discard your Markdown edits and convert another input?')) return; setOutput(null); setError(''); setCopied(false); }
  async function copy() { try { await navigator.clipboard.writeText(output || ''); setCopied(true); } catch { setError('Could not copy automatically. Select the Markdown and copy it.'); } }
  function download() { const link = document.createElement('a'); const objectUrl = URL.createObjectURL(new Blob([output || ''], { type: 'text/markdown;charset=utf-8' })); link.href = objectUrl; link.download = `${title.replace(/\.[^.]+$/, '').replace(/[^a-z0-9_-]/gi, '-').slice(0, 70) || 'converted'}.md`; link.click(); setTimeout(() => URL.revokeObjectURL(objectUrl), 1000); }
  return <div className="app-shell">
    <a href="#main" className="skip-link">Skip to content</a>
    <header className="header"><a className="brand" href="/" aria-label="Markdown Converter home"><span className="brand-mark">M<span>↓</span></span><span>Markdown Converter</span></a><a className="how-link" href="#how-it-works">How it works <ChevronRight size={16}/></a></header>
    <main id="main">
      <section className={`intro ${output !== null ? 'compact' : ''}`}><div><p className="eyebrow">A LITTLE LESS FORMATTING. A LOT MORE CLARITY.</p><h1>Turn your content<br className="desktop-break"/> into <span>Markdown.</span></h1></div><p className="intro-copy">Convert PDFs, webpages, and text into structured Markdown you can edit and copy.</p></section>
      {error && <div className="notice error" role="alert"><AlertCircle size={20}/><span>{error}</span><button className="icon-button" aria-label="Dismiss error" onClick={() => setError('')}><X size={18}/></button></div>}
      {output === null ? <section className="converter" aria-label="Convert your content">
        <div className="input-tabs" role="tablist" aria-label="Input type">{tabs.map(({ id, name, icon: Icon }, i) => <button key={id} id={`tab-${id}`} type="button" role="tab" aria-selected={tab === id} aria-controls={`panel-${id}`} tabIndex={tab === id ? 0 : -1} disabled={busy} className={tab === id ? 'active' : ''} onClick={() => { setTab(id); setError(''); }} onKeyDown={e => { let n: number | undefined; if (e.key === 'ArrowRight') n = (i + 1) % 3; if (e.key === 'ArrowLeft') n = (i + 2) % 3; if (e.key === 'Home') n = 0; if (e.key === 'End') n = 2; if (n !== undefined) { e.preventDefault(); setTab(tabs[n].id); document.getElementById(`tab-${tabs[n].id}`)?.focus(); } }}><Icon size={18}/>{name}</button>)}<span className="tab-note">YOUR CONTENT, REFORMATTED</span></div>
        <div className="input-body" id={`panel-${tab}`} role="tabpanel" aria-labelledby={`tab-${tab}`}>
          {tab === 'pdf' && <><input ref={pdfPicker} type="file" accept=".pdf,application/pdf" hidden onChange={e => { void pickPdf(e.target.files?.[0]); e.target.value = ''; }}/><div className={`dropzone ${dragging ? 'dragging' : ''}`} onDragOver={e => { e.preventDefault(); if (!busy) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); if (!busy) { if (e.dataTransfer.files.length !== 1) setError('Choose one PDF at a time.'); else void pickPdf(e.dataTransfer.files[0]); } }}><span className="upload-symbol"><FileText size={32} strokeWidth={1.4}/></span><h2>{file ? file.name : 'Drop a PDF here'}</h2><p>{file ? `${(file.size / 1024).toFixed(1)} KB · Ready to convert` : 'Bring the content. We’ll take care of the formatting.'}</p>{file ? <button className="secondary" disabled={busy} onClick={() => setFile(null)}><X size={16}/>Remove file</button> : <button className="secondary" disabled={busy || !limitsReady} onClick={() => pdfPicker.current?.click()}><Plus size={17}/>Choose PDF</button>}<small>Text-based and scanned PDFs{limits.max_pdf_bytes ? ` · Up to ${(limits.max_pdf_bytes / 1048576).toFixed(0)} MB` : ''}</small></div></>}
          {tab === 'website' && <div className="website-area"><span className="upload-symbol"><Globe2 size={32} strokeWidth={1.4}/></span><h2>A webpage, without the clutter.</h2><label htmlFor="url">Webpage URL</label><div className="url-field"><Globe2 size={20}/><input id="url" type="url" value={url} disabled={busy} onChange={e => setUrl(e.target.value)} placeholder="https://example.com/article" aria-describedby="url-help" aria-invalid={!!url && !validUrl(url.trim())}/></div><p id="url-help">{url && !validUrl(url.trim()) ? 'Enter a valid URL beginning with https:// or http://.' : 'Enter one public webpage URL. Login-protected pages are not supported.'}</p></div>}
          {tab === 'text' && <div className="text-area"><div className="field-heading"><label htmlFor="plain-text">Your plain text</label><input hidden ref={txtPicker} type="file" accept=".txt,text/plain" onChange={e => { void pickText(e.target.files?.[0]); e.target.value = ''; }}/><button className="quiet" disabled={busy} onClick={() => txtPicker.current?.click()}><Upload size={16}/>Upload .txt</button></div><textarea id="plain-text" value={text} disabled={busy} onChange={e => setText(e.target.value)} placeholder={'Paste your notes, an article, or any text here…'} aria-invalid={textTooLong} aria-describedby="text-help"/><div id="text-help" className="text-meta"><span>{textTooLong ? 'Your text exceeds the supported character limit.' : 'Your words stay yours. Spacing gets a little cleaner.'}</span><span>{text.length.toLocaleString()}{limits.max_text_chars ? ` / ${limits.max_text_chars.toLocaleString()}` : ''} characters</span></div></div>}
        </div>
        <div className="convert-footer"><p><Check size={16}/>Headings, lists, links & tables</p><button className="primary" disabled={!ready || busy} onClick={() => void convert()}>{busy ? <><LoaderCircle className="spinner" size={18}/>Converting…</> : <>Convert to Markdown <ArrowRight size={18}/></>}</button></div>
        {busy && <div className="progress" role="status"><LoaderCircle className="spinner" size={16}/>{stage}</div>}
        {!apiConfigured && tab !== 'text' && <p className="connection-note">PDF and webpage conversion will be available when the conversion service is connected. <button onClick={() => setTab('text')}>Try plain text</button></p>}
      </section> : <section className="results" aria-label="Conversion result"><div className="result-top"><div><p className="success-line"><CheckCircle2 size={17}/>Conversion complete</p><h2 ref={resultHeading} tabIndex={-1}>Your Markdown is ready.</h2><p className="source-title">{title}</p></div><button className="secondary" onClick={reset}><Plus size={16}/>Convert another</button></div>{warnings.length > 0 && <div className="notice warning"><AlertCircle size={20}/><div><strong>Some content needs review.</strong><ul>{warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></div></div>}<div className="result-toolbar"><span className="document-meta">{output.trim() ? output.trim().split(/\s+/).length : 0} words <span>·</span> Markdown</span><div className="result-actions"><button className="secondary" onClick={download}><ArrowDownToLine size={17}/>Download .md</button><button className="primary" onClick={() => void copy()}>{copied ? <Check size={17}/> : <Clipboard size={17}/>} {copied ? 'Copied' : 'Copy Markdown'}</button></div></div><div className="view-tabs" aria-label="Result view">{['markdown', 'preview'].map(v => <button aria-pressed={view === v} className={view === v ? 'active' : ''} key={v} onClick={() => setView(v)}>{v === 'markdown' ? 'Markdown' : 'Preview'}</button>)}</div><div className="workspace"><div className={`pane ${view === 'markdown' ? 'selected' : ''}`}><div className="pane-heading"><span><Type size={16}/>Markdown</span><small>EDITABLE</small></div><CodeMirror aria-label="Markdown editor" value={output} onChange={setOutput} height="480px" extensions={[markdownLanguage(), EditorView.lineWrapping, editorTheme]} basicSetup={{ foldGutter: false, highlightActiveLine: false, highlightActiveLineGutter: false }} /></div><div className={`pane ${view === 'preview' ? 'selected' : ''}`}><div className="pane-heading"><span><FileText size={16}/>Preview</span><small>LIVE</small></div><article className="markdown-preview"><ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={{ img: ({ alt }) => <span className="image-placeholder">[Image: {alt || 'image'}]</span> }}>{output}</ReactMarkdown></article></div></div><p className="editor-hint">Make it yours. Edits appear in the preview and are included when you copy or download.</p><span className="sr-only" aria-live="polite">{copied ? 'Markdown copied to clipboard.' : ''}</span></section>}
      <section id="how-it-works" className="steps" aria-label="How it works">{[{ number: '01', title: 'Add your content', copy: 'A PDF, a webpage, or a few words.' }, { number: '02', title: 'Review the result', copy: 'Clean structure. Room for your edits.' }, { number: '03', title: 'Copy or download', copy: 'Ready for wherever you write next.' }].map(s => <div className="step" key={s.number}><span>{s.number}</span><div><h3>{s.title}</h3><p>{s.copy}</p></div></div>)}</section>
    </main><footer className="page-footer"><span>Good content deserves a clean format.</span><span>PDF / WEB / TEXT <span className="footer-arrow">→</span> MARKDOWN</span></footer>
  </div>;
}
