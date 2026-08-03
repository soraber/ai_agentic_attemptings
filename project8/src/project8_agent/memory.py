from __future__ import annotations
import re,sqlite3,time
from pathlib import Path
from typing import Any
from .schemas import MemoryAnswer,MemoryEvent,MemoryQuery


FACT_PATTERN=re.compile(r"^(FACT|CORRECT)\s+([A-Za-z0-9_]+)=(.+)$")


def tokens(text:str)->set[str]: return set(re.findall(r"[a-z0-9_]+",text.lower()))


class MemoryStore:
    def __init__(self,path:str|Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._setup()
    def connect(self):
        connection=sqlite3.connect(self.path); connection.row_factory=sqlite3.Row; return connection
    def _setup(self):
        with self.connect() as c:
            c.executescript("""CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY,session_id TEXT,timestamp TEXT,speaker TEXT,text TEXT); CREATE TABLE IF NOT EXISTS facts(fact_id INTEGER PRIMARY KEY AUTOINCREMENT,key TEXT,value TEXT,source_event_id TEXT,valid_from TEXT,superseded_at TEXT,superseded_by TEXT); CREATE TABLE IF NOT EXISTS tombstones(event_id TEXT PRIMARY KEY,deleted_at REAL);""")
    def reset(self):
        with self.connect() as c: c.execute("DELETE FROM events"); c.execute("DELETE FROM facts"); c.execute("DELETE FROM tombstones")
    def ingest(self,event:MemoryEvent):
        with self.connect() as c:
            c.execute("INSERT OR REPLACE INTO events VALUES(?,?,?,?,?)",(event.event_id,event.session_id,event.timestamp,event.speaker,event.text))
            match=FACT_PATTERN.match(event.text)
            if match:
                mode,key,value=match.groups()
                if mode=="CORRECT": c.execute("UPDATE facts SET superseded_at=?,superseded_by=? WHERE key=? AND superseded_at IS NULL",(event.timestamp,event.event_id,key))
                c.execute("INSERT INTO facts(key,value,source_event_id,valid_from) VALUES(?,?,?,?)",(key,value,event.event_id,event.timestamp))
    def delete_event(self,event_id:str):
        with self.connect() as c:
            c.execute("DELETE FROM facts WHERE source_event_id=?",(event_id,)); c.execute("DELETE FROM events WHERE event_id=?",(event_id,)); c.execute("INSERT OR REPLACE INTO tombstones VALUES(?,?)",(event_id,time.time()))
    def deletion_verified(self,event_id:str)->bool:
        with self.connect() as c:
            return c.execute("SELECT COUNT(*) FROM events WHERE event_id=?",(event_id,)).fetchone()[0]==0 and c.execute("SELECT COUNT(*) FROM facts WHERE source_event_id=?",(event_id,)).fetchone()[0]==0 and c.execute("SELECT COUNT(*) FROM tombstones WHERE event_id=?",(event_id,)).fetchone()[0]==1
    def recent(self,limit:int)->list[sqlite3.Row]:
        with self.connect() as c: return c.execute("SELECT * FROM events ORDER BY timestamp DESC,event_id DESC LIMIT ?",(limit,)).fetchall()
    def episodic(self,question:str,top_k:int)->list[sqlite3.Row]:
        query=tokens(question)
        with self.connect() as c: rows=c.execute("SELECT * FROM events ORDER BY timestamp DESC").fetchall()
        scored=[]
        for row in rows:
            event_tokens=tokens(row["text"].replace("_"," ")); union=query|event_tokens; score=len(query&event_tokens)/len(union) if union else 0; scored.append((score,row["timestamp"],row))
        return [row for score,_,row in sorted(scored,key=lambda item:(item[0],item[1]),reverse=True)[:top_k] if score>0]
    def active_facts(self,key:str,as_of:str|None=None)->list[sqlite3.Row]:
        with self.connect() as c:
            if as_of is None: return c.execute("SELECT * FROM facts WHERE key=? AND superseded_at IS NULL ORDER BY valid_from DESC",(key,)).fetchall()
            return c.execute("SELECT * FROM facts WHERE key=? AND valid_from<=? AND (superseded_at IS NULL OR superseded_at>?) ORDER BY valid_from DESC",(key,as_of,as_of)).fetchall()
    def consolidate(self,max_words:int=60)->str:
        with self.connect() as c: rows=c.execute("SELECT key,value FROM facts WHERE superseded_at IS NULL ORDER BY key,value").fetchall()
        words=("; ".join(f"{row['key']}={row['value']}" for row in rows)).split(); return " ".join(words[:max_words])
    def answer(self,query:MemoryQuery,system:str,window_size:int=6,top_k:int=5)->MemoryAnswer:
        started=time.perf_counter(); rows=[]; conflict=False; answer=None; evidence=[]
        if system=="window": rows=self.recent(window_size)
        elif system=="episodic": rows=self.episodic(query.question,top_k)
        else:
            facts=self.active_facts(query.fact_key or "") if query.fact_key else []
            values={row["value"] for row in facts}
            if len(values)>1: conflict=True
            elif len(values)==1: answer=next(iter(values)); evidence=[row["source_event_id"] for row in facts]
            rows=self.episodic(query.question,top_k)
        if system in {"window","episodic"} and query.fact_key:
            matches=[]
            for row in rows:
                parsed=FACT_PATTERN.match(row["text"])
                if parsed and parsed.group(2)==query.fact_key: matches.append((row,parsed.group(3)))
            if matches: answer=matches[0][1]; evidence=[matches[0][0]["event_id"]]
        context_tokens=sum(len(row["text"].split()) for row in rows)
        abstained=answer is None or conflict
        return MemoryAnswer(query_id=query.query_id,system=system,answer=None if conflict else answer,evidence_ids=evidence,abstained=abstained,conflict=conflict,context_tokens=context_tokens,latency_ms=(time.perf_counter()-started)*1000)
    def stats(self)->dict[str,int]:
        with self.connect() as c: return {name:c.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] for name in ["events","facts","tombstones"]}
