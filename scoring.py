"""Validated policy and deterministic scoring. No provider dependency."""
from __future__ import annotations
import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any, TypedDict

FIELDS = ('name', 'company', 'company_size', 'industry', 'source', 'last_interaction_date')
FACTORS = ('company_size', 'industry_fit', 'source_intent', 'recency')
MISSING = {'', 'na', 'n/a', 'null', 'none', 'unknown'}

class ConfigurationError(ValueError):
    pass

class Lead(TypedDict):
    name: str
    company: str
    company_size: str
    industry: str
    source: str
    last_interaction_date: str

class Rubric(TypedDict):
    version: str
    description: str
    weights: dict[str, float]
    company_size_bands: list[dict[str, Any]]
    recency_bands: list[dict[str, Any]]
    industry_scores: dict[str, float]
    source_scores: dict[str, float]
    thresholds: dict[str, float]
    priority_thresholds: dict[str, float]
    minimum_fit_score: float

class Decision(TypedDict, total=False):
    lead_id: str
    score: float
    decision: str
    fit_decision: str
    outreach_ready: bool
    review_flags: list[str]
    factor_scores: dict[str, float | None]
    outreach_message: str | None


def fingerprint(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(f'Cannot load JSON configuration: {path.name}') from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f'{path.name} must contain an object')
    return data


def number(value: Any, label: str, low=1, high=10) -> float:
    # Reject strings and bools instead of accepting values that later crash scoring.
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ConfigurationError(f'{label} must be a finite number in [{low}, {high}]')
    return float(value)


def validate_bands(bands: Any, label: str, start: int) -> None:
    if not isinstance(bands, list) or not bands:
        raise ConfigurationError(f'{label} must be a nonempty array')
    expected = start
    for i, band in enumerate(bands):
        if not isinstance(band, dict) or not isinstance(band.get('name'), str) or not band['name'].strip():
            raise ConfigurationError(f'{label} needs named bands')
        lo, hi = band.get('min'), band.get('max')
        if type(lo) is not int or lo != expected:
            raise ConfigurationError(f'{label} must be ordered, contiguous and nonoverlapping')
        if hi is None:
            if i != len(bands)-1:
                raise ConfigurationError(f'{label}: only last band may be unbounded')
        elif type(hi) is not int or hi < lo:
            raise ConfigurationError(f'{label}: invalid maximum')
        band['score'] = number(band.get('score'), label+'.score')
        expected = hi+1 if hi is not None else None
    if bands[-1].get('max') is not None:
        raise ConfigurationError(f'{label} must cover all values')


def load_rubric(path: Path) -> Rubric:
    r = read_json(path)
    for key in ('version', 'description'):
        if not isinstance(r.get(key), str) or not r[key].strip():
            raise ConfigurationError(f'Missing rubric {key}')
    weights = r.get('weights')
    if not isinstance(weights, dict) or set(weights) != set(FACTORS):
        raise ConfigurationError('Exactly four policy factors are required')
    r['weights'] = {k:number(v, 'weights.'+k, 0, 1) for k,v in weights.items()}
    if any(v == 0 for v in r['weights'].values()) or not math.isclose(sum(r['weights'].values()),1,abs_tol=1e-9):
        raise ConfigurationError('Positive factor weights must sum to 1')
    validate_bands(r.get('company_size_bands'),'company_size_bands',1)
    validate_bands(r.get('recency_bands'),'recency_bands',0)
    for key in ('industry_scores','source_scores'):
        if not isinstance(r.get(key),dict) or not r[key]:
            raise ConfigurationError(f'{key} must be a nonempty object')
        seen=set()
        for k,v in r[key].items():
            if not isinstance(k,str) or not k.strip() or k.strip().casefold() in seen:
                raise ConfigurationError(f'{key} contains empty or normalized duplicate keys')
            seen.add(k.strip().casefold())
            r[key][k] = number(v,key+'.'+k)
    for key, names in [('thresholds',('qualified','rejected')),('priority_thresholds',('high','medium'))]:
        if not isinstance(r.get(key),dict) or set(r[key]) != set(names):
            raise ConfigurationError(f'Invalid {key}')
        r[key]={k:number(v,key+'.'+k) for k,v in r[key].items()}
    if r['thresholds']['rejected'] >= r['thresholds']['qualified']:
        raise ConfigurationError('Rejected threshold must be below qualified')
    if not r['thresholds']['qualified'] <= r['priority_thresholds']['medium'] <= r['priority_thresholds']['high']:
        raise ConfigurationError('Priority thresholds must be >= qualification threshold and ordered')
    r['minimum_fit_score']=number(r.get('minimum_fit_score'),'minimum_fit_score')
    return r


def normalize(value: str) -> str:
    value=value.strip()
    return '' if value.casefold() in MISSING or value.casefold().startswith('unknown ') else value


def parse_size(value: str) -> int | None:
    if not re.fullmatch(r'(?:[1-9][0-9]*|[1-9][0-9]{0,2}(?:,[0-9]{3})+)',value):
        return None
    return int(value.replace(',',''))


def band_score(value: int, bands: list[dict]) -> tuple[float,str]:
    for b in bands:
        if value >= b['min'] and (b['max'] is None or value <= b['max']):
            return b['score'], b['name']
    raise ConfigurationError('Uncovered band value')


def mapping_score(value: str, mapping: dict) -> float | None:
    return {k.strip().casefold():v for k,v in mapping.items()}.get(value.casefold())


def score_lead(raw_lead: dict[str,str], row_number: int, rubric: Rubric, as_of: date | None = None) -> dict:
    as_of = as_of or date.today()
    lead={f:normalize(raw_lead.get(f,'') or '') for f in FIELDS}
    scores: dict[str,float|None]={f:None for f in FACTORS}
    reasons={}
    flags=[]
    size=parse_size(lead['company_size'])
    if size is not None:
        scores['company_size'],band=band_score(size,rubric['company_size_bands'])
        reasons['company_size']=f'{size} employees; policy band: {band}'
    else:
        flags.append('missing or invalid company size')
    for factor,field,mapping in [('industry_fit','industry','industry_scores'),('source_intent','source','source_scores')]:
        scores[factor]=mapping_score(lead[field],rubric[mapping])
        if scores[factor] is None:
            flags.append(f'missing or unmapped {field}')
        else:
            reasons[factor]=f"Explicit policy mapping: {lead[field]} (proxy, not confirmed buying intent)"
    age=None
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',lead['last_interaction_date']):
            raise ValueError('invalid ISO date')
        age=(as_of-date.fromisoformat(lead['last_interaction_date'])).days
        if age < 0:
            raise ValueError('future date')
        scores['recency'],band=band_score(age,rubric['recency_bands'])
        reasons['recency']=f'{age} days before {as_of.isoformat()}; policy band: {band}'
    except ValueError:
        flags.append('missing, invalid or future interaction date')
    if raw_lead.get('_row_error'):
        flags.append(raw_lead['_row_error'])
    for f,s in scores.items():
        reasons[f]=reasons.get(f,'Unknown evidence: possible factor score [1, 10]') + (f'; score {s}/10' if s is not None else '')
    lower=math.fsum(rubric['weights'][f]*(s if s is not None else 1) for f,s in scores.items())
    upper=math.fsum(rubric['weights'][f]*(s if s is not None else 10) for f,s in scores.items())
    midpoint=(lower+upper)/2
    complete=all(s is not None for s in scores.values()) and not raw_lead.get('_row_error')
    if not complete:
        fit='review'
    elif lower <= rubric['thresholds']['rejected']:
        fit='rejected'
    elif lower >= rubric['thresholds']['qualified'] and all(scores[f] >= rubric['minimum_fit_score'] for f in ('company_size','industry_fit')):
        fit='qualified'
    else:
        fit='review'
        flags.append('borderline score or insufficient target-customer fit')
    contact_flags=[f'missing or unknown {f}' for f in ('name','company') if not lead[f]]
    # Do not allow obvious instructions/control text into a send-ready draft.
    if any(re.search(r'ignore\s+.*instructions|system\s*:|<script|[\r\n]',v,re.I) for v in lead.values()):
        contact_flags.append('suspicious input text; human validation required')
    decision='review' if fit=='qualified' and contact_flags else fit
    flags.extend(contact_flags)
    ready=decision=='qualified'
    priority=None
    if fit=='qualified':
        priority='high' if lower >= rubric['priority_thresholds']['high'] else 'medium' if lower >= rubric['priority_thresholds']['medium'] else 'low'
    reasoning=' '.join(reasons.values())+f' Weighted score bounds [{lower:.2f}, {upper:.2f}]; fit: {fit}; decision: {decision}.'
    if flags:
        reasoning+=' Review notes: '+'; '.join(flags)+'.'
    stable=fingerprint({k:v.casefold() for k,v in lead.items()})
    return {**lead,'lead_id':f'L{row_number:04d}','source_row':row_number+1,'fingerprint':stable,
        'company_size_numeric':size,'interaction_age_days':age,'as_of':as_of.isoformat(),
        'factor_scores':scores,'factor_reasons':reasons,'score':round(midpoint,2),'score_is_estimate':not complete,
        'score_bounds':{'lower':round(lower,2),'upper':round(upper,2)},'ranking_score':lower,
        'evidence_coverage':round(sum(rubric['weights'][f] for f,s in scores.items() if s is not None),4),
        'fit_decision':fit,'decision':decision,'outreach_ready':ready,'data_quality_flags':contact_flags,
        'priority':priority,'priority_rank':None,'review_flags':flags,'reasoning':reasoning,
        'recommended_action':'draft outreach for approval' if ready else 'enrich contact details' if fit=='qualified' else 'review evidence and fit' if decision=='review' else 'archive; include in periodic rejection audit',
        'llm_status':'disabled','llm_error':None,'llm_explanation':None,'outreach_message':None,
        'message_origin':None,'message_validation':'not_applicable','message_variant':None}


def score_leads(raw_leads: list[dict[str,str]], rubric: Rubric, as_of: date | None = None) -> list[dict]:
    results=[score_lead(x,i,rubric,as_of) for i,x in enumerate(raw_leads,1)]
    counts={}
    for x in results:
        counts[x['fingerprint']]=counts.get(x['fingerprint'],0)+1
        x['duplicate_occurrence']=counts[x['fingerprint']]
        if x['duplicate_occurrence']>1:
            x.update(decision='review',outreach_ready=False,priority=None,recommended_action='merge duplicate before outreach')
            x['review_flags'].append('duplicate input record')
            x['reasoning']+=' Duplicate record: final decision review; merge before outreach.'
    qualified=sorted((x for x in results if x['outreach_ready']),key=lambda x:(-x['ranking_score'],-x['factor_scores']['source_intent'],x['company'].casefold(),x['fingerprint'],x['source_row']))
    for rank,x in enumerate(qualified,1):
        x['priority_rank']=rank
    return results
