"""Reproducible offline tests, fixture reports, and explicitly simulated provider run."""
import contextlib
import csv
import io
import json
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import lead_qualifier as cli
import llm_client
from messaging import load_seller
from reporting import write_report

ROOT=Path(__file__).parent


def fake_completion(**kwargs):
    payload=json.loads(kwargs['messages'][1]['content'])
    items=[]
    for x in payload['leads']:
        variants=x['allowed_variants']
        choice='demo' if 'demo' in variants else 'referral' if 'referral' in variants else next(iter(variants),None)
        items.append({'lead_id':x['lead_id'],'evidence_factors':['company_size','industry_fit','source_intent','recency'],'variant':choice})
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({'leads':items})))],usage=SimpleNamespace(total_tokens=0))


def main():
    directory=ROOT/'validation';directory.mkdir(exist_ok=True)
    buffer=io.StringIO()
    started=time.perf_counter()
    tests=unittest.defaultTestLoader.discover(str(ROOT),pattern='test_*.py')
    result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(tests)
    (directory/'unit_tests.txt').write_text(buffer.getvalue(),encoding='utf-8')
    summary={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'test_seconds':round(time.perf_counter()-started,3),'datasets':[]}
    if not result.wasSuccessful():
        print(buffer.getvalue());return 1
    for filename,out in [('leads_training.csv','training_report.json'),('leads_testing.csv','testing_report.json'),('leads_full_scale_100.csv','output_report.json')]:
        code=cli.main(['--no-llm','--input',str(ROOT/filename),'--output',str(ROOT/out),'--as-of','2024-01-20'])
        if code:raise RuntimeError('Fixture CLI failed')
        r=json.loads((ROOT/out).read_text(encoding='utf-8'))
        summary['datasets'].append({'file':filename,**{k:r[k] for k in ['total_processed','qualified_count','rejected_count','review_count']},'elapsed_seconds':r['manifest']['elapsed_seconds'],'distinct_scores':len({x['score'] for x in r['leads']})})
        assert len(r['leads'])==r['total_processed']
        assert all(x['review_flags'] for x in r['leads'] if x['decision']=='review')
        assert all(x['outreach_message'] is None for x in r['leads'] if not x['outreach_ready'])
    full=json.loads((ROOT/'output_report.json').read_text(encoding='utf-8'))
    write_report(full,ROOT/'output_report.csv','csv')
    write_report({k:v for k,v in full.items() if k!='leads'},ROOT/'output_report.manifest.json','json')
    with (directory/'labels_template.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['fingerprint','qualified'])
        w.writerows((x['fingerprint'],'') for x in full['leads'])
    client=llm_client.LiteLLMClient('simulated-key','SIMULATED/provider',seller=load_seller(ROOT/'seller.json'))
    with patch('lead_qualifier.load_dotenv'),patch('lead_qualifier._create_client_from_environment',return_value=client),patch('llm_client.completion',side_effect=fake_completion):
        code=cli.main(['--require-llm','--as-of','2024-01-20','--output',str(directory/'simulated_full_scale_report.json')])
    r=json.loads((directory/'simulated_full_scale_report.json').read_text(encoding='utf-8'))
    assert code==0 and r['llm_status_counts']=={'success':100} and len(r['batch_metrics'])==10
    assert [(x['fingerprint'],x['score'],x['decision']) for x in r['leads']]==[(x['fingerprint'],x['score'],x['decision']) for x in full['leads']]
    summary['simulated_provider']={'clearly_simulated':True,'leads':100,'batches':10,'successful_items':100,'strict_exit_code':code,'score_decision_parity':True}
    summary['message_variants']=sorted({x['message_variant'] for x in r['leads'] if x['outreach_ready']})
    summary['live_provider']='See smoke_report.json; simulation is not evidence of live API success.'
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2));return 0

if __name__=='__main__':sys.exit(main())
