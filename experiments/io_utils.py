"""Read saved numerical results; report and figures never invent measurements."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def read_csv(name):
    with (ROOT/'data'/name).open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        for key,value in row.items():
            if value=='':
                row[key]=None
            else:
                try:
                    row[key]=int(value)
                except ValueError:
                    try:
                        row[key]=float(value)
                    except ValueError:
                        pass
    return rows


def read_json(name):
    return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))


def load_results():
    rows=read_csv('summary.csv')
    byid={r['id']:r for r in rows}
    aliases={alias:byid[s['id']] for s in read_json('configurations.json') for alias in s['aliases']}
    return rows,byid,aliases
