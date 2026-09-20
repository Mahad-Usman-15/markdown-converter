import assert from 'node:assert/strict';
import { createServer } from 'vite';
process.env.VITE_API_BASE_URL = 'https://conversion.test';
const server = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
const originalFetch = globalThis.fetch;
try {
  const { formatText, validUrl, convertRemote } = await server.ssrLoadModule('/src/conversion.ts');
  assert.equal(formatText('  # Title\r\n\r\n\r\n- Item  \r\n'), '# Title\n\n- Item');
  assert.equal(formatText('A sentence.\nNext line.'), 'A sentence.\nNext line.');
  assert.equal(validUrl('javascript:alert(1)'), false);
  assert.equal(validUrl('https://user:pass@example.com'), false);
  assert.equal(validUrl('https://example.com/article'), true);
  async function scenario(job, status = 200) {
    let calls = 0;
    globalThis.fetch = async (_url, init) => {
      if (++calls === 1) {
        assert.equal(init.method, 'POST');
        assert.equal(init.body.get('kind'), 'website');
        assert.equal(init.body.get('url'), 'https://example.com');
        return new Response(JSON.stringify({ job_id: 'test-job' }), { status: 202 });
      }
      return new Response(JSON.stringify(job), { status });
    };
    return convertRemote('website', null, 'https://example.com', new AbortController().signal, () => {});
  }
  assert.equal((await scenario({ status: 'completed', markdown: '# Converted', warnings: [] })).markdown, '# Converted');
  await assert.rejects(scenario({}, 410), /interrupted/);
  await assert.rejects(scenario({ status: 'completed', markdown: '  ' }), /No readable content/);
  await assert.rejects(scenario({ status: 'failed', message: 'Page unavailable' }), /Page unavailable/);
  console.log('Passed: text preservation, URL validation, multipart submission, success, expired job, empty output, backend failure.');
} finally { globalThis.fetch = originalFetch; await server.close(); }
