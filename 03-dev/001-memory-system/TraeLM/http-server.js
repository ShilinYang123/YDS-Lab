// 极简 HTTP 包装器：把 TraeLM 核心暴露为 REST 服务
const { LongTermMemorySystem } = require('./dist/src/index.js');
const http = require('http');
const url = require('url');
const prom = require('prom-client');

const register = new prom.Registry();
prom.collectDefaultMetrics({ register });

const cpuGauge = new prom.Gauge({ name: 'traelm_cpu_percent', help: 'TraeLM process CPU %', registers: [register] });
const memGauge = new prom.Gauge({ name: 'traelm_mem_mb', help: 'TraeLM process memory MB', registers: [register] });
const portUpGauge = new prom.Gauge({ name: 'traelm_port_listening', help: 'Port 8765 listening', registers: [register] });
const pingOkGauge = new prom.Gauge({ name: 'traelm_ping_ok', help: 'ICMP ping localhost ok', registers: [register] });
const pyExitGauge = new prom.Gauge({ name: 'traelm_py_health_exit', help: 'Python health script exit code', registers: [register] });

const PORT = process.env.PORT || 8765;
// 统一到公司级 LongMemory 日志目录（可被环境变量覆盖）
// YDS_LONGMEMORY_ROOT 优先，其次 LOGS_DIR，最后使用规范默认值
const DEFAULT_LONGMEMORY_ROOT = 'S:/YDS-Lab/01-struc/logs/longmemory';
const LOGS_DIR = process.env.YDS_LONGMEMORY_ROOT || process.env.LOGS_DIR || DEFAULT_LONGMEMORY_ROOT;
const PID_FILE = process.env.PID_FILE || './trae-lm.pid';

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
    } else if (path === '/update-metrics' && req.method === 'POST') {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        const d = JSON.parse(body);
        if (typeof d.cpu === 'number') cpuGauge.set(d.cpu);
        if (typeof d.mem === 'number') memGauge.set(d.mem);
        if (typeof d.portListening === 'boolean') portUpGauge.set(d.portListening ? 1 : 0);
        if (typeof d.pingOk === 'boolean') pingOkGauge.set(d.pingOk ? 1 : 0);
        if (typeof d.pyExitCode === 'number') pyExitGauge.set(d.pyExitCode);
        res.writeHead(200); res.end('ok');
      });
    } else if (path === '/metrics' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': register.contentType });
      res.end(await register.metrics());
    } else if (path === '/health/history' && req.method === 'GET') {
      try {
        const limit = parseInt(parsed.query.limit || '100', 10);
        const sinceRaw = parsed.query.since;
        let since = null;
        if (sinceRaw) {
          const d = new Date(sinceRaw);
          if (isNaN(d.getTime())) { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ error: 'invalid since param, expected ISO8601' })); return; }
          since = d;
        }
        const fs = require('fs');
        const pathModule = require('path');
        const healthDir = pathModule.join(LOGS_DIR, 'health');
        if (!fs.existsSync(healthDir)) throw new Error('health dir not found');
        const files = fs.readdirSync(healthDir)
          .filter(f => f.startsWith('health_') && f.endsWith('.jsonl'))
          .map(f => ({ name: f, path: pathModule.join(healthDir, f) }))
          .sort((a, b) => b.name.localeCompare(a.name));
        // 调试：打印找到的文件
        console.log('[debug] healthDir:', healthDir, 'files:', files.map(x => x.name));
        const records = [];
        for (const f of files) {
          const content = fs.readFileSync(f.path, 'utf8').trim();
          if (!content) continue;
          const lines = content.split(/\r?\n/).filter(Boolean);
          for (const l of lines) {
            try { records.push(JSON.parse(l.trim())); } catch (e) { console.log('[debug] bad line:', l, e.message); }
          }
        }
        // 可选按时间过滤（since）
        const filtered = since ? records.filter(r => {
          const t = new Date(r.timestamp);
          return !isNaN(t.getTime()) && t >= since;
        }) : records;
        // 按时间倒序返回最新数据
        filtered.sort((a, b) => {
          const ta = new Date(a.timestamp).getTime();
          const tb = new Date(b.timestamp).getTime();
          return tb - ta;
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(filtered.slice(0, limit)));
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: e.message }));
      }
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
    // 写入 PID 文件供外部监控脚本读取
    require('fs').writeFileSync(PID_FILE, JSON.stringify({ pid: process.pid }));
    console.log(`[TraeLM-HTTP] listening on http://localhost:${PORT}/health`);
  });
  // 退出时清理 PID 文件
  process.on('SIGINT', () => { try { require('fs').unlinkSync(PID_FILE); } catch {} process.exit(0); });
  process.on('SIGTERM', () => { try { require('fs').unlinkSync(PID_FILE); } catch {} process.exit(0); });
}

bootstrap().catch(err => {
  console.error('[TraeLM-HTTP] bootstrap failed:', err);
  process.exit(1);
});