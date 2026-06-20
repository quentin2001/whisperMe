import sqlite3, json

db_path = r"e:\Projects\whisperMe\whisperMe.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Get tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print("Tables:", [t[0] for t in tables])

c.execute("SELECT id, url, status FROM tasks LIMIT 5")
rows = c.fetchall()
for r in rows:
    url_short = (r[1] or "")[:60]
    print(f"Task: {r[0][:20]}... | Status: {r[2]} | URL: {url_short}")
print()

# For ALL completed tasks, check transcript speaker distribution
c.execute("SELECT id, transcript, speaker_mappings, speaker_embeddings FROM tasks WHERE status='completed'")
rows = c.fetchall()
for row in rows:
    tid = row[0]
    transcript = json.loads(row[1]) if row[1] else []
    mappings = json.loads(row[2]) if row[2] else {}
    embeddings = json.loads(row[3]) if row[3] else {}
    speakers = set(seg.get("speaker", "?") for seg in transcript)
    print(f"=== Task: {tid[:30]} ===")
    print(f"  Transcript segments: {len(transcript)}")
    print(f"  Unique speakers in transcript: {speakers}")
    print(f"  Speaker mappings: {json.dumps(mappings, ensure_ascii=False)}")
    print(f"  Speaker embeddings keys: {list(embeddings.keys())}")
    if embeddings:
        print(f"  Embedding dimensions: {dict((k, len(v)) for k,v in embeddings.items())}")
    print()

if not rows:
    print("No completed tasks found")

conn.close()
