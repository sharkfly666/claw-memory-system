PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS documents (
  doc_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  source_path TEXT,
  title TEXT,
  entity TEXT,
  key TEXT,
  aliases TEXT,
  tags TEXT,
  text TEXT NOT NULL,
  scope TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT,
  updated_at TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
  doc_id UNINDEXED,
  title,
  entity,
  key,
  aliases,
  tags,
  text,
  tokenize = 'unicode61'
);

CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_key ON documents(key);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at);
