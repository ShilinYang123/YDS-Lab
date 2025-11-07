// 极简 HTTP 包装器：把 TraeLM 核心暴露为 REST 服务
const { LongTermMemorySystem } = require('./dist/src/index.js');
const http = require('http');
const url = require('url');

const PORT = process.env.PORT || 8765;
const LOGS_DIR = process.env.LOGS_DIR || '../../01-struc/0B-general-manager/logs/longmemory';

let ltms;

async function handleRequest(req, res) {
  const parsed = url.parse(req.url, true);
  const path = parsed.pathname;

  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(200); res.end(); return; }

  try {
    if (path === '/health' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', service: 'trae-longmemory', port: PORT }));
    } else if (path === '/store' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', async () => {
        const memory = JSON.parse(body);
        const id = await ltms.storeMemory(memory);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ id }));
      });
    } else if (path === '/retrieve' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', async () => {
        const query = JSON.parse(body);
        const memories = await ltms.retrieveMemories(query);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(memories));
      });
    } else {
      res.writeHead(404);
      res.end('Not Found');
    }
  } catch (e) {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: e.message }));
  }
}

async function bootstrap() {
  ltms = new LongTermMemorySystem('./config/trae-memory-config.json');
  await ltms.initialize();
  const server = http.createServer(handleRequest);
  server.listen(PORT, () => {
    console.log(`[TraeLM-HTTP] listening on http://localhost:${PORT}/health`);
  });
}

bootstrap().catch(err => {
  console.error('[TraeLM-HTTP] bootstrap failed:', err);
  process.exit(1);
});