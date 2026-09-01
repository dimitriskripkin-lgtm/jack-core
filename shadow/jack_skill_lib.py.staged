import sqlite3, json, os, time

DB=os.path.expanduser('~/jack/jack_skills.db')

def _con():
    c=sqlite3.connect(DB)
    c.execute('''CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT,
        plan_json TEXT,
        state TEXT DEFAULT 'CANDIDATE',
        executions INTEGER DEFAULT 0,
        successes INTEGER DEFAULT 0,
        created_ts INTEGER,
        last_ts INTEGER)''')
    c.commit()
    return c

STATES=['CANDIDATE','TESTING','VERIFIED','PROMOTED','DEPRECATED','REJECTED']

def save(name, plan, description='', state='CANDIDATE'):
    c=_con()
    try:
        c.execute('INSERT OR REPLACE INTO skills (name,description,plan_json,state,executions,successes,created_ts,last_ts) VALUES (?,?,?,?,0,0,?,?)',(name,description,json.dumps(plan,ensure_ascii=False),state,int(time.time()),int(time.time())))
        c.commit()
        return 'Skill gespeichert: '+name+' ['+state+']'
    except Exception as e: return 'Fehler: '+str(e)[:100]
    finally: c.close()

def record_run(name, success):
    c=_con()
    try:
        row=c.execute('SELECT executions,successes,state FROM skills WHERE name=?',(name,)).fetchone()
        if not row: return
        execs=row[0]+1; succ=row[1]+(1 if success else 0); state=row[2]
        if state=='CANDIDATE' and succ>=1: state='TESTING'
        if state=='TESTING' and succ>=3: state='VERIFIED'
        c.execute('UPDATE skills SET executions=?,successes=?,state=?,last_ts=? WHERE name=?',(execs,succ,state,int(time.time()),name))
        c.commit()
    finally: c.close()

def get(name):
    c=_con()
    try:
        row=c.execute('SELECT name,description,plan_json,state,executions,successes FROM skills WHERE name=?',(name,)).fetchone()
        if not row: return None
        return {'name':row[0],'description':row[1],'plan':json.loads(row[2]),'state':row[3],'executions':row[4],'successes':row[5]}
    finally: c.close()

def list_all():
    c=_con()
    try:
        rows=c.execute('SELECT name,state,executions,successes,description FROM skills ORDER BY state,name').fetchall()
        return [{'name':r[0],'state':r[1],'executions':r[2],'successes':r[3],'description':r[4]} for r in rows]
    finally: c.close()

def promote(name):
    c=_con()
    try:
        c.execute("UPDATE skills SET state='PROMOTED' WHERE name=?",(name,))
        c.commit()
        return 'Promoted: '+name
    finally: c.close()

def deprecate(name):
    c=_con()
    try:
        c.execute("UPDATE skills SET state='DEPRECATED' WHERE name=?",(name,))
        c.commit()
        return 'Deprecated: '+name
    finally: c.close()
