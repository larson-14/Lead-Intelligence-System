"""Actionable queues and atomic report exports."""
import csv
import json
import os
import tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from scoring import fingerprint


def build_report(results: list[dict], rubric: dict, llm_enabled: bool, manifest: dict | None=None, metrics: list | None=None) -> dict:
    counts=Counter(x['decision'] for x in results)
    qualified=sorted((x for x in results if x['outreach_ready']),key=lambda x:x['priority_rank'])
    review=sorted((x for x in results if x['decision']=='review'),key=lambda x:(-x['score_bounds']['upper'],x['fingerprint'],x['source_row']))
    rejections=Counter(f for x in results if x['decision']=='rejected' for f,s in x['factor_scores'].items() if s is not None and s<5)
    statuses=Counter(x['llm_status'] for x in results)
    samples=[]
    seen=set()
    for x in qualified:
        if x['message_variant'] not in seen:
            samples.append(x);seen.add(x['message_variant'])
    for x in qualified:
        if len(samples)>=5:break
        if x not in samples:samples.append(x)
    return {'generated_at':datetime.now(timezone.utc).isoformat(),'total_processed':len(results),
        'qualified_count':counts['qualified'],'qualified_percent':round(100*counts['qualified']/len(results),2) if results else 0,
        'rejected_count':counts['rejected'],'review_count':counts['review'],
        'review_percent':round(100*counts['review']/len(results),2) if results else 0,
        'common_rejection_reasons':dict(rejections),'llm_enrichment_enabled':llm_enabled,
        'llm_status_counts':dict(statuses),'llm_failed_batches':0,
        'llm_success_percent':round(100*statuses['success']/len(results),2) if results and llm_enabled else None,
        'priority_queue':[x['lead_id'] for x in qualified],'review_queue':[x['lead_id'] for x in review],
        'sample_outreach_messages':[{'lead_id':x['lead_id'],'company':x['company'],'variant':x['message_variant'],'message':x['outreach_message'],'origin':x['message_origin']} for x in samples[:5]],
        'rubric':rubric,'manifest':{'rubric_version':rubric['version'],'rubric_hash':fingerprint(rubric),**(manifest or {})},
        'batch_metrics':metrics or [],'leads':results}


def write_report(report: dict, path: Path, output_format: str) -> None:
    if output_format not in {'json','csv'}:
        raise ValueError('Unsupported output format')
    temp=None
    try:
        path.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',newline='',dir=path.parent,prefix='.'+path.name+'.',suffix='.tmp',delete=False) as f:
            temp=Path(f.name)
            if output_format=='json':
                json.dump(report,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
            else:
                aggregate=('total_processed','qualified_count','qualified_percent','rejected_count','review_count','common_rejection_reasons','llm_failed_batches','llm_status_counts','manifest')
                columns=list(report['leads'][0]) if report['leads'] else ['lead_id','decision','score']
                writer=csv.DictWriter(f,fieldnames=columns+list(aggregate))
                writer.writeheader()
                for x in report['leads']:
                    row={**x,**{k:report[k] for k in aggregate}}
                    for k,v in row.items():
                        if isinstance(v,(dict,list)):row[k]=json.dumps(v,ensure_ascii=False,allow_nan=False)
                        elif isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')):row[k]="'"+v
                    writer.writerow(row)
            f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    except OSError as exc:
        raise ValueError('Cannot atomically write report: '+path.name) from exc
    finally:
        if temp is not None and temp.exists():temp.unlink()
