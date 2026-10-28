"""CSV intake preserves row provenance and flags malformed records."""
import csv
from pathlib import Path
from scoring import FIELDS


def read_leads(path: Path) -> list[dict[str,str]]:
    try:
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f,strict=True)
            headers=reader.fieldnames or []
            if len(headers)!=len(set(headers)):
                raise ValueError('CSV contains duplicate column names')
            if not set(FIELDS) <= set(headers):
                raise ValueError('CSV missing columns: '+', '.join(sorted(set(FIELDS)-set(headers))))
            leads=[]
            for row in reader:
                item={k:(v or '').strip() for k,v in row.items() if k is not None}
                if None in row or any(v is None for v in row.values()):
                    item['_row_error']='malformed CSV row: field count differs from header'
                leads.append(item)
            return leads
    except (OSError,UnicodeError,csv.Error) as exc:
        raise ValueError('Unable to read CSV: '+type(exc).__name__) from exc
