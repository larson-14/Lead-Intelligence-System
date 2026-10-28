"""Seller-approved message templates and configuration."""
from pathlib import Path
from scoring import read_json, ConfigurationError


def load_seller(path: Path) -> dict:
    seller=read_json(path)
    for k in ('version','assumption','name','product','value_proposition','voice','cta'):
        if not isinstance(seller.get(k),str) or not seller[k].strip():
            raise ConfigurationError('Seller configuration requires '+k)
    if not isinstance(seller.get('approved_claims'),list) or not all(isinstance(x,str) and x.strip() for x in seller['approved_claims']) or seller['value_proposition'] not in seller['approved_claims']:
        raise ConfigurationError('Value proposition must be an approved claim')
    return seller


def message_variants(lead: dict, seller: dict) -> dict[str,str]:
    first=lead['name'].split()[0] if lead['name'] else 'there'
    context=f"{lead['company']} in {lead['industry']}"
    intro=f"Hi {first}, {seller['name']} offers {seller['product']} to {seller['value_proposition']}."
    variants={
        'educational':f"{intro} Would this be relevant to {context}? {seller['cta']}",
        'discovery':f"Hi {first}, I'm reaching out about {context}. How does your team handle qualification and follow-up today? {seller['name']} can help {seller['value_proposition']}. {seller['cta']}"}
    if lead['source'].casefold()=='inbound demo request':
        variants['demo']=f"Hi {first}, thanks for the demo request from {lead['company']}. We can walk through how {seller['name']} helps {seller['value_proposition']} and discuss its relevance to your {lead['industry']} team. {seller['cta']}"
    if lead['source'].casefold()=='referral':
        variants['referral']=f"Hi {first}, {lead['company']} reached us through a referral. {seller['name']} helps {seller['value_proposition']}. Would this be relevant to your team in {lead['industry']}? {seller['cta']}"
    return variants


def prepare_messages(leads: list[dict], seller: dict) -> None:
    for x in leads:
        if not x['outreach_ready']:
            continue
        variants=message_variants(x,seller)
        preferred='demo' if 'demo' in variants else 'referral' if 'referral' in variants else ('educational' if int(x['fingerprint'][:2],16)%2==0 else 'discovery')
        x.update(outreach_message=variants[preferred],message_variant=preferred,message_origin='local_template',message_validation='approved_template')
