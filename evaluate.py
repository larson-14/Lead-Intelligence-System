"""Evaluate independent business labels; never derive labels from rubric scores.

Labels CSV: fingerprint,qualified (0 or 1). Evaluate only a complete, independently
labeled report cohort. Unknown/review decisions count as abstentions, not negatives.
"""
import argparse
import csv
import json
import math
from pathlib import Path


def evaluate(report: dict, labels: dict[str,int], k: int=10) -> dict:
    if k<1:raise ValueError('k must be positive')
    leads=report['leads']
    ids=[x['fingerprint'] for x in leads]
    if len(ids)!=len(set(ids)):raise ValueError('Deduplicate the evaluation cohort first')
    if set(ids)!=set(labels):raise ValueError('Label every record in the exact evaluation cohort; do not evaluate a selected subset')
    if any(type(x) is not int or x not in (0,1) for x in labels.values()):raise ValueError('Labels must be binary integers')
    predicted=[x for x in leads if x['decision']=='qualified']
    tp=sum(labels[x['fingerprint']] for x in predicted)
    positives=sum(labels.values())
    rejected=[x for x in leads if x['decision']=='rejected']
    reviews=[x for x in leads if x['decision']=='review']
    top=sorted(predicted,key=lambda x:x['priority_rank'])[:k]
    def wilson(successes, total):
        if not total:return None
        z=1.96;p=successes/total;den=1+z*z/total
        mid=(p+z*z/(2*total))/den
        half=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
        return [max(0,mid-half),min(1,mid+half)]
    return {'precision_95pct_wilson_interval':wilson(tp,len(predicted)), 'cohort_size':len(leads),'positive_labels':positives,'qualified_predictions':len(predicted),
        'precision':tp/len(predicted) if predicted else None,
        'recall_of_all_positives':tp/positives if positives else None,
        'false_rejections':sum(labels[x['fingerprint']] for x in rejected),
        'positives_in_review':sum(labels[x['fingerprint']] for x in reviews),
        'review_coverage':len(reviews)/len(leads) if leads else 0,
        'precision_at_k':sum(labels[x['fingerprint']] for x in top)/len(top) if top else None,
        'requested_k':k,'actual_top_count':len(top),
        'note':'Descriptive cohort metrics only. Independent labels, fixed outcome horizon, temporal/company separation and rejection audits are required. Small cohorts do not establish generalization.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--k',type=int,default=10);p.add_argument('--output',type=Path,default=Path('evaluation_report.json'));a=p.parse_args()
    with a.labels.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    labels={}
    for x in rows:
        if x['fingerprint'] in labels:raise ValueError('Duplicate label')
        labels[x['fingerprint']]=int(x['qualified'])
    result=evaluate(json.loads(a.report.read_text(encoding='utf-8')),labels,a.k)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
