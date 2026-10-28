"""Build a secret-free submission from an explicit allowlist."""
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent
FILES=[
 'lead_qualifier.py','scoring.py','ingestion.py','messaging.py','llm_client.py','reporting.py',
 'evaluate.py','validate_project.py','build_submission.py','test_lead_qualifier.py','test_evaluate.py',
 'rubric.json','seller.json','requirements.txt','.env.example','README.md','OPERATIONS.md',
 'EVALUATION.md','REQUIREMENTS_ALIGNMENT.md','VALIDATION_RESULTS.md','IMPROVEMENT_PLAN.md',
 'leads.csv','leads_training.csv','leads_testing.csv','leads_full_scale_100.csv',
 'output_report.json','output_report.csv','output_report.manifest.json','training_report.json','testing_report.json',
 'smoke_report.json','live_full_scale_report.json','validation/summary.json','validation/unit_tests.txt',
 'validation/labels_template.csv','validation/benchmark.json']


def main():
    for name in FILES:
        if not (ROOT/name).is_file():raise FileNotFoundError(name)
    target=ROOT/'lead_intelligence_submission.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:archive.write(ROOT/name,name)
    with zipfile.ZipFile(target) as archive:
        names=archive.namelist()
        assert set(names)==set(FILES)
        assert '.env' not in names and not any('.venv/' in n or '__pycache__' in n for n in names)
        assert archive.testzip() is None
    print(f'Created {target.name}: {len(FILES)} allowlisted files; no credentials or environment directory.')

if __name__=='__main__':main()
