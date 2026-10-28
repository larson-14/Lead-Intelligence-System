"""Lead Intelligence CLI. Run with --as-of for reproducible historical evaluation."""
from __future__ import annotations
import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path
from scoring import ConfigurationError, load_rubric, score_lead, score_leads, fingerprint
from ingestion import read_leads
from messaging import load_seller, prepare_messages
from llm_client import LiteLLMClient, LLMError, enrich_with_llm, PROMPT_VERSION
from reporting import build_report, write_report

ROOT=Path(__file__).resolve().parent
LOGGER=logging.getLogger('lead_qualifier')


def load_dotenv(path: Path) -> None:
    if not path.exists():return
    try:
        for raw in path.read_text(encoding='utf-8-sig').splitlines():
            line=raw.strip()
            if not line or line.startswith('#') or '=' not in line:continue
            if line.startswith('export '):line=line[7:]
            key,value=line.split('=',1)
            key,value=key.strip(),value.strip()
            if len(value)>=2 and value[0]==value[-1] and value[0] in {'\"',"'"}:value=value[1:-1]
            if key:os.environ.setdefault(key,value)
    except (OSError,UnicodeError) as exc:
        raise ConfigurationError('Cannot read environment file') from exc


def _create_client_from_environment(seller: dict | None=None) -> LiteLLMClient | None:
    key=os.environ.get('LLM_API_KEY','').strip()
    model=os.environ.get('LLM_MODEL','').strip()
    if not key and not model:return None
    if not key or not model:raise ConfigurationError('Set both LLM_API_KEY and LLM_MODEL')
    return LiteLLMClient(key,model,os.environ.get('LLM_BASE_URL','').strip() or None,
        int(os.environ.get('LLM_TIMEOUT_SECONDS','45')),int(os.environ.get('LLM_MAX_RETRIES','2')),
        seller=seller,json_mode=os.environ.get('LLM_JSON_MODE','false').lower()=='true')


def parse_args(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'leads_full_scale_100.csv')
    p.add_argument('--output',type=Path,default=ROOT/'output_report.json')
    p.add_argument('--format',choices=['json','csv'])
    p.add_argument('--rubric',type=Path,default=ROOT/'rubric.json')
    p.add_argument('--seller',type=Path,default=ROOT/'seller.json')
    p.add_argument('--as-of',type=date.fromisoformat,default=None,help='YYYY-MM-DD; defaults to local current date')
    p.add_argument('--batch-size',type=int)
    p.add_argument('--limit',type=int,help='Smoke-test first N leads before full run')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--no-llm',action='store_true')
    mode.add_argument('--require-llm',action='store_true')
    p.add_argument('--dotenv',type=Path,default=ROOT/'.env')
    p.add_argument('--verbose',action='store_true')
    return p.parse_args(argv)


def main(argv=None) -> int:
    args=parse_args(argv)
    logging.basicConfig(level=logging.INFO,format='%(levelname)s: %(message)s')
    started=time.perf_counter()
    try:
        if not args.no_llm:load_dotenv(args.dotenv)
        rubric=load_rubric(args.rubric)
        seller=load_seller(args.seller)
        raw=read_leads(args.input)
        if args.limit is not None:
            if args.limit<1:raise ValueError('--limit must be positive')
            raw=raw[:args.limit]
        snapshot=args.as_of or date.today()
        results=score_leads(raw,rubric,snapshot)
        prepare_messages(results,seller)
        client=None if args.no_llm else _create_client_from_environment(seller)
        batch_size=args.batch_size if args.batch_size is not None else int(os.environ.get('LLM_BATCH_SIZE','10'))
        if batch_size<2:raise ValueError('Batch size must be at least 2')
        failures=enrich_with_llm(results,client,batch_size) if client else 0
        source_files=['lead_qualifier.py','scoring.py','ingestion.py','messaging.py','llm_client.py','reporting.py']
        manifest={'code_version':'2.0','code_hash':fingerprint({f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in source_files}),
            'input_file':args.input.name,'input_hash':hashlib.sha256(args.input.read_bytes()).hexdigest(),
            'input_limit':args.limit,'as_of':snapshot.isoformat(),'as_of_explicit':args.as_of is not None,
            'seller_version':seller['version'],'seller_hash':fingerprint(seller),'business_assumption':seller['assumption'],
            'model':client.model if client else None,'prompt_version':PROMPT_VERSION,'batch_size':batch_size,
            'elapsed_seconds':round(time.perf_counter()-started,3),
            'cost_usd':None,'cost_note':'Not estimated; use provider billing for actual cost.',
            'evaluation_note':'Policy scores, not conversion probabilities; no outcome labels supplied.'}
        metrics=client.batch_metrics if client else []
        manifest['total_tokens']=sum(m['total_tokens'] for m in metrics) if metrics and all(m['total_tokens'] is not None for m in metrics) else None
        report=build_report(results,rubric,client is not None,manifest,metrics)
        report['llm_failed_batches']=failures
        if args.require_llm and not client:report['llm_requirement_error']='LLM credentials not configured'
        output_format=args.format or ('csv' if args.output.suffix.lower()=='.csv' else 'json')
        if args.output.resolve() in {p.resolve() for p in (args.input,args.rubric,args.seller,args.dotenv)}:
            raise ValueError('Output must not overwrite input or configuration')
        write_report(report,args.output,output_format)
        if output_format=='csv':
            # Sidecar also preserves run metadata for zero-row CSV files.
            write_report({k:v for k,v in report.items() if k!='leads'},args.output.with_suffix('.manifest.json'),'json')
        LOGGER.info('Processed %s: %s qualified / %s rejected / %s review; LLM failed batches %s; %s',len(results),report['qualified_count'],report['rejected_count'],report['review_count'],failures,args.output.name)
        return 2 if args.require_llm and (not client or failures) else 0
    except (ConfigurationError,ValueError,OSError) as exc:
        LOGGER.error('%s',exc)
        return 2


if __name__=='__main__':
    sys.exit(main())
