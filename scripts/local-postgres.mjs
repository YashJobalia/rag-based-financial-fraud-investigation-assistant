import EmbeddedPostgres from 'embedded-postgres';
import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import { resolve } from 'node:path';

// Local development only. Passwords are generated, never printed, and kept in ignored files.
// Reuse an installed Microsoft runtime on Windows without changing system PATH or installing services.
if (process.platform === 'win32') {
  const edgeRoot = `${process.env['ProgramFiles(x86)']}/Microsoft/Edge/Application`;
  if (existsSync(edgeRoot)) {
    const runtime = readdirSync(edgeRoot).map(name => `${edgeRoot}/${name}`)
      .find(path => existsSync(`${path}/msvcp140.dll`) && existsSync(`${path}/vcruntime140.dll`));
    if (runtime) process.env.PATH = `${runtime};${process.env.PATH}`;
  }
}
mkdirSync('.local', { recursive: true });
const credentialPath = resolve('.local/database.json');
const credentials = existsSync(credentialPath)
  ? JSON.parse(readFileSync(credentialPath, 'utf8'))
  : { admin: randomBytes(24).toString('hex'), app: randomBytes(24).toString('hex') };
if (!existsSync(credentialPath)) writeFileSync(credentialPath, JSON.stringify(credentials), { mode: 0o600 });
const pg = new EmbeddedPostgres({
  databaseDir: resolve('.local/postgres'), user: 'postgres', password: credentials.admin,
  port: 55432, persistent: true, authMethod: 'scram-sha-256',
  postgresFlags: ['-h', '127.0.0.1'],
  onLog: () => {}, onError: () => {},
});
if (!existsSync('.local/postgres/PG_VERSION')) await pg.initialise();
await pg.start();
const client = pg.getPgClient();
await client.connect();
if (!(await client.query("SELECT 1 FROM pg_database WHERE datname='fraud_investigation'")).rowCount) {
  await pg.createDatabase('fraud_investigation');
}
await client.end();
if (!existsSync('backend/.env')) {
  writeFileSync('backend/.env', [
    `DATABASE_URL=postgresql://ffia_app:${credentials.app}@127.0.0.1:55432/fraud_investigation`,
    `ADMIN_DATABASE_URL=postgresql://postgres:${credentials.admin}@127.0.0.1:55432/fraud_investigation`,
    `AUTH_SECRET=${randomBytes(32).toString('hex')}`,
    'ENABLE_PUBLIC_DEMO=true', 'ENABLE_LIVE_GENERATION=false',
    'OPENAI_API_KEY=', 'OPENAI_CHAT_MODEL=gpt-4.1-mini',
    'OPENAI_EMBEDDING_MODEL=text-embedding-3-small', '',
  ].join('\n'), { mode: 0o600 });
  console.log('Created ignored backend/.env. No existing environment file was overwritten.');
}
console.log('Local PostgreSQL ready on 127.0.0.1:55432. Ctrl+C stops it; data persists.');
let closing = false;
async function shutdown() { if (!closing) { closing = true; await pg.stop(); process.exit(0); } }
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
setInterval(() => {}, 60_000);
