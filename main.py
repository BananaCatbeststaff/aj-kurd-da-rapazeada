// server.js — Main API: distribui jobIds e monitora clientes ativos (com contador e TTL)
// npm i express

const express = require("express");

// ===================== CONFIG =====================
const PORT = Number(process.env.PORT || 4000);
const JOB_TTL_MS = Number(process.env.JOB_TTL_MS || 15 * 60_000); // 15 minutos
const CLIENT_TTL_MS = Number(process.env.CLIENT_TTL_MS || 2 * 60_000); // 2 minutos
const CLEAN_INTERVAL_MS = 60_000; // limpeza a cada 1 min
const DEFAULT_BATCH = Number(process.env.DEFAULT_BATCH || 5);

// ===================== ESTADO =====================
const jobs = new Map();        // jobId -> timestamp
const consumers = new Map();   // client -> { lastActive, lastJob, totalConsumed }

// ===================== FUNÇÕES =====================
function cleanupOldJobs() {
  const now = Date.now();
  for (const [id, ts] of jobs) {
    if (now - ts > JOB_TTL_MS) jobs.delete(id);
  }
}

function cleanupInactiveClients() {
  const now = Date.now();
  let removed = 0;
  for (const [client, data] of consumers.entries()) {
    if (now - data.lastActive > CLIENT_TTL_MS) {
      consumers.delete(client);
      removed++;
    }
  }
  if (removed > 0)
    console.log(`[cleanup] removidos ${removed} clients inativos (> ${CLIENT_TTL_MS / 1000}s)`);
}

function updateClientActivity(client, jobIds) {
  const now = Date.now();
  const jobList = Array.isArray(jobIds) ? jobIds : [jobIds];
  const lastJob = jobList[jobList.length - 1];

  const current = consumers.get(client) || {
    lastActive: 0,
    lastJob: null,
    totalConsumed: 0,
  };

  consumers.set(client, {
    lastActive: now,
    lastJob,
    totalConsumed: current.totalConsumed + jobList.length,
  });
}

// limpeza periódica
setInterval(() => {
  cleanupOldJobs();
  cleanupInactiveClients();
}, CLEAN_INTERVAL_MS);

// ===================== EXPRESS =====================
const app = express();
app.use(express.json({ limit: "10mb" }));

// 📥 Receber jobIds
app.post("/add-pool", (req, res) => {
  const { servers } = req.body;
  if (!Array.isArray(servers) || servers.length === 0)
    return res.status(400).json({ ok: false, error: "Corpo inválido ou lista vazia." });

  let added = 0;
  const now = Date.now();
  for (const id of servers) {
    if (!jobs.has(id)) {
      jobs.set(id, now);
      added++;
    }
  }

  console.log(`[add] recebidos ${servers.length}, adicionados ${added} (total=${jobs.size})`);
  res.json({ ok: true, added, total: jobs.size });
});

// 📤 GET /consume
app.get("/consume", (req, res) => {
  const count = Number(req.query.count || DEFAULT_BATCH);
  const client = (req.query.client || "unknown_client").trim();

  const available = Array.from(jobs.keys());
  if (available.length === 0) return res.status(204).end();

  const toSend = available.slice(0, count);
  toSend.forEach((id) => jobs.delete(id));

  updateClientActivity(client, toSend);
  console.log(`[consume:GET] client=${client} -> ${toSend.join(", ")}`);

  res.json({ ok: true, client, count: toSend.length, jobs: toSend });
});

// 📤 POST /consume
app.post("/consume", (req, res) => {
  const count = Number(req.body.count || req.query.count || 1);
  const client = (req.body.client || req.query.client || "unknown_client").trim();

  const available = Array.from(jobs.keys());
  if (available.length === 0) return res.status(204).end();

  const toSend = available.slice(0, count);
  toSend.forEach((id) => jobs.delete(id));

  updateClientActivity(client, toSend);
  console.log(`[consume:POST] client=${client} consumiu ${toSend.length} jobIds -> ${toSend.join(", ")}`);

  if (count === 1)
    return res.json({ ok: true, client, job: toSend[0] });

  res.json({ ok: true, client, count: toSend.length, jobs: toSend });
});

// 📄 Listar jobIds disponíveis
app.get("/jobs", (req, res) => {
  cleanupOldJobs();
  res.json({ ok: true, total: jobs.size, jobs: Array.from(jobs.keys()) });
});

// 🧾 Listar clientes ativos
app.get("/clients", (req, res) => {
  cleanupInactiveClients();
  const active = [];
  for (const [client, data] of consumers.entries()) {
    active.push({
      client,
      lastJob: data.lastJob,
      lastActive: new Date(data.lastActive).toISOString(),
      secondsSinceLast: Math.round((Date.now() - data.lastActive) / 1000),
      totalConsumed: data.totalConsumed,
    });
  }

  res.json({
    ok: true,
    totalActive: active.length,
    ttlSeconds: CLIENT_TTL_MS / 1000,
    clients: active.sort((a, b) => b.lastActive - a.lastActive),
  });
});

// 🩺 Status geral
app.get("/", (req, res) => {
  cleanupOldJobs();
  cleanupInactiveClients();
  res.json({
    ok: true,
    totalJobs: jobs.size,
    activeClients: consumers.size,
    ttlMinutesJobs: JOB_TTL_MS / 60000,
    ttlMinutesClients: CLIENT_TTL_MS / 60000,
    uptime: process.uptime().toFixed(1) + "s",
  });
});

// ===================== START =====================
app.listen(PORT, () => {
  console.log(`[MAIN_API] rodando em http://localhost:${PORT}`);
});
