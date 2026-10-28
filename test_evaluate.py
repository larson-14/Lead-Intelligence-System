import unittest
from evaluate import evaluate

class EvaluationTests(unittest.TestCase):
    def test_independent_labels_and_abstentions(self):
        report={'leads':[{'fingerprint':'a','decision':'qualified','priority_rank':1},{'fingerprint':'b','decision':'qualified','priority_rank':2},{'fingerprint':'c','decision':'review','priority_rank':None},{'fingerprint':'d','decision':'rejected','priority_rank':None}]}
        r=evaluate(report,{'a':1,'b':0,'c':1,'d':1},1)
        self.assertEqual(r['precision'],.5);self.assertEqual(r['recall_of_all_positives'],1/3);self.assertEqual(r['false_rejections'],1);self.assertEqual(r['precision_at_k'],1);self.assertEqual(r['review_coverage'],.25)
    def test_partial_labels_rejected(self):
        with self.assertRaises(ValueError):evaluate({'leads':[{'fingerprint':'a'}]}, {})
    def test_duplicate_cohort_rejected(self):
        with self.assertRaises(ValueError):evaluate({'leads':[{'fingerprint':'a'},{'fingerprint':'a'}]}, {'a':1})
