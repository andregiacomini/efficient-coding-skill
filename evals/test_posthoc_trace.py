"""Post-hoc rules tested synthetically; no agent, Docker or benchmark edits."""
import unittest
from pathlib import Path
import importlib.util
import json
import tempfile
import sys
sys.path.insert(0,str(Path(__file__).parent))
import posthoc_trace as p


class ClassifierTests(unittest.TestCase):
    def classify(self,command,code=0,output=''):
        ops,unknown=p.shell_operations(command,exit_code=code,output=output,test_entrypoints=['tests/runtests.py'])
        return ops,unknown

    def test_successful_pure_and_chain_proves_every_invocation(self):
        ops,u=self.classify("pwd && git status --short && rg -n symbol django && cat django/a.py")
        self.assertEqual(u,[]);self.assertEqual(sum(o['repository_search'] for o in ops),1)
        self.assertEqual(ops[-1]['read_requests'][0]['path'],'django/a.py')

    def test_failed_unknown_and_chain_not_guessed(self):
        ops,u=self.classify('some-program && pytest',1)
        self.assertTrue(u);self.assertEqual(ops[-1]['coverage'],'conditional-execution')

    def test_literal_false_skips_and_literal_true_executes(self):
        ops,u=self.classify('false && pytest',1)
        self.assertEqual(u,[]);self.assertEqual(ops[-1]['category'],'skipped command')
        ops,u=self.classify('true && pytest',1)
        self.assertEqual(u,[]);self.assertEqual(ops[-1]['category'],'test execution')

    def test_or_fallback_and_mixed_list_not_guessed_from_final_exit(self):
        ops,u=self.classify('rg missing src && pytest || true',0)
        self.assertEqual(ops[1]['coverage'],'conditional-execution')
        self.assertTrue(u)
        _,u=self.classify('git status && pytest; echo done',0)
        self.assertTrue(u)

    def test_quoted_operators_are_arguments_not_shell_control(self):
        ops,u=self.classify("rg '&&' src; rg 'a|b' src")
        self.assertEqual(len(ops),2);self.assertEqual(u,[])

    def test_black_check_version_and_failed_load_have_no_explicit_reads(self):
        for command,category,code,output in [
          ('black --check --line-length 88 django/a.py','format validation',0,''),
          ('python -m black --check django/a.py','format validation',1,'No module named black'),
          ('python -m black --version','formatter availability',1,'No module named black'),
          ('python -m black django/a.py','failed formatting attempt',1,'No module named black')]:
            ops,u=self.classify(command,code,output)
            self.assertEqual(u,[]);self.assertEqual(ops[0]['category'],category);self.assertEqual(ops[0]['read_requests'],[])
        ops,u=self.classify('black --check --line-length 88 django/a.py')
        self.assertEqual(ops[0]['validation_targets'],['django/a.py'])

    def test_other_segment_error_does_not_prove_formatter_failed_to_edit(self):
        _,u=self.classify('python -m black django/a.py; python -m black --version',1,'No module named black')
        self.assertTrue(u)

    def test_successful_format_write_outcome_unknown(self):
        ops,u=self.classify('python -m black django/a.py',0,'All done!')
        self.assertTrue(u);self.assertEqual(ops[0]['coverage'],'format-edit-outcome-unknown')

    def test_literal_bad_sed_parse_error_is_failed_attempt_not_read(self):
        ops,u=self.classify("cat django/a.py; sed -n '1, seventy p' tests/a.py",1,"sed: -e expression #1, char 4: unexpected `,'")
        self.assertEqual(u,[]);self.assertEqual(ops[-1]['category'],'failed inspection');self.assertEqual(ops[-1]['read_requests'],[])
        _,u=self.classify("sed -n '1, seventy p' tests/a.py",1,'')
        self.assertTrue(u)
        _,u=self.classify("sed -n '1, seventy p' tests/a.py; echo done",0,"sed: -e expression #1: unexpected")
        self.assertTrue(u)

    def test_numeric_spaces_and_multiple_e_ranges(self):
        ops,u=self.classify("sed -n -e '1, 2p' -e '7,9p' django/a.py")
        self.assertEqual(u,[]);self.assertEqual(ops[0]['read_requests'][0]['ranges'],[[1,2],[7,9]])

    def test_compound_and_inline_probe_recover_scoped_operations(self):
        ops,u=self.classify("git status && python -c \"print(open('django/a.py').read())\"",0)
        self.assertEqual(u,[]);self.assertEqual(ops[-1]['read_requests'][0]['path'],'django/a.py')
        ops,u=self.classify('rg symbol src; cat src/a.py; python tests/runtests.py prefetch_related')
        self.assertEqual(u,[]);self.assertEqual([o['category'] for o in ops],['search','file inspection','test execution'])


TARGETS=['prefetch_related.tests.C.test_a','prefetch_related.tests.C.test_b']
OUTPUT='test_a (prefetch_related.tests.C) ... ok\ntest_b (prefetch_related.tests.C) ... ok\nRan 2 tests in 0.01s\n\nOK\n'

class CompletionTests(unittest.TestCase):
    def analyze(self,events):
        items=[];completed={};times={}
        for index,event in enumerate(events):
            start=index*2+1;end=start+1
            item=dict(event,id=str(index));items.append((start,item));completed[str(index)]=end
            times[start]=start/10;times[end]=end/10
        return p.analyze_actions(items,times,source_roots=['django'],test_entrypoints=['tests/runtests.py'],regression_test_ids=TARGETS,completion_by_id=completed)
    def edit(self,path):return {'type':'file_change','status':'completed','changes':[{'path':path}]}
    def validation(self,scope='prefetch_related',code=0):return {'type':'command_execution','command':'python tests/runtests.py '+scope,'exit_code':code,'aggregated_output':OUTPUT if code==0 else 'Ran 2 tests in 0.01s\nFAILED (failures=1)'}

    def test_final_test_edit_after_tests_and_git_check_is_false(self):
        m,t=self.analyze([self.edit('django/a.py'),self.validation(),self.edit('tests/prefetch_related/tests.py'),{'type':'command_execution','command':'git diff --check; git status --short','exit_code':0}])
        self.assertFalse(m['final_edit_revalidated']);self.assertTrue(m['test_edited_after_last_test'])
        self.assertFalse(m['production_edited_after_last_test']);self.assertTrue(m['final_production_edit_revalidated'])
        self.assertEqual(m['edits_after_first_targeted_success'],1);self.assertEqual(m['edits_after_last_validation'],1)
        self.assertEqual(m['tool_calls_after_final_edit'],1);self.assertEqual(m['last_edit_time_seconds'],0.6)

    def test_passing_full_module_after_later_production_edit_is_true(self):
        m,t=self.analyze([self.edit('django/a.py'),self.validation(),self.edit('django/a.py'),self.validation()])
        self.assertTrue(m['final_edit_revalidated']);self.assertTrue(m['validation_after_final_production_edit'])
        self.assertEqual(m['edits_after_last_validation'],0)

    def test_failed_test_after_final_edit_attempts_but_does_not_revalidate(self):
        m,_=self.analyze([self.edit('django/a.py'),self.validation(),self.edit('django/a.py'),self.validation(code=1)])
        self.assertTrue(m['validation_after_final_production_edit']);self.assertFalse(m['final_edit_revalidated'])

    def test_formatter_does_not_revalidate_test_behavior(self):
        m,_=self.analyze([self.edit('django/a.py'),self.validation(),self.edit('tests/prefetch_related/tests.py'),{'type':'command_execution','command':'black --check tests/prefetch_related/tests.py','exit_code':0}])
        self.assertFalse(m['final_edit_revalidated']);self.assertEqual(m['last_validation_kind'],'format')
        self.assertEqual(m['edits_after_last_validation'],0)

    def test_targeted_subset_after_arbitrary_test_file_edit_is_unavailable(self):
        m,_=self.analyze([self.edit('tests/prefetch_related/tests.py'),self.validation('prefetch_related.tests.C')])
        self.assertIsNone(m['final_edit_revalidated'])

    def test_documentation_only_edit_and_missing_tests_are_unavailable(self):
        m,_=self.analyze([self.edit('docs/a.txt')])
        self.assertIsNone(m['final_edit_revalidated']);self.assertIsNone(m['repository_edited_after_last_test'])

    def test_unknown_writer_is_not_assumed_harmless(self):
        m,_=self.analyze([self.edit('django/a.py'),self.validation(),{'type':'command_execution','command':'unknown-program','exit_code':0}])
        self.assertIsNone(m['final_edit_revalidated']);self.assertFalse(m['completion_edit_coverage_complete'])

    def test_overlapping_test_started_before_edit_completion_is_not_revalidation(self):
        edits={'id':'edit','type':'file_change','status':'completed','changes':[{'path':'django/a.py'}]}
        test=dict(self.validation(),id='test')
        m,_=p.analyze_actions([(1,edits),(2,test)],{1:.1,2:.2,3:.3,4:.4},source_roots=['django'],test_entrypoints=['tests/runtests.py'],regression_test_ids=TARGETS,completion_by_id={'edit':3,'test':4})
        self.assertIsNone(m['final_edit_revalidated'])

    def test_failed_structured_edit_is_not_counted(self):
        edit=self.edit('django/a.py');edit['status']='failed'
        m,_=self.analyze([self.edit('django/a.py'),self.validation(),edit])
        self.assertTrue(m['final_edit_revalidated']);self.assertEqual(m['edits_after_first_targeted_success'],0)


class PosthocReportTests(unittest.TestCase):
    def module(self):
        spec=importlib.util.spec_from_file_location('posthoc_report',Path(__file__).with_name('analyze-EVAL-004.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_boolean_false_and_unknown_have_different_denominators(self):
        from unittest.mock import patch
        module=self.module()
        rows=[{'run_id':'V2-1','condition':'V2','success':True,'final_edit_revalidated':False},
              {'run_id':'V2-2','condition':'V2','success':True,'final_edit_revalidated':None}]
        with patch.multiple(module.h,EVAL_ID='EVAL-004',CONDITIONS={'B':{},'V1':{},'V2':{}}):
            result=module.aggregate(rows)
        indicator=result['conditions']['V2']['indicators']['final_edit_revalidated']
        self.assertEqual(indicator,{'true':0,'false':1,'unavailable':1,'rate_true':0.0})
        self.assertIsNone(result['conditions']['V2']['metrics']['total_tokens']['median'])

    def test_zero_percentage_denominator_and_benchmark_failure_remain_explicit(self):
        from unittest.mock import patch
        module=self.module()
        rows=[{'run_id':'V1-1','condition':'V1','success':False,'total_tokens':100,'post_first_success_file_reads':0},
              {'run_id':'V2-1','condition':'V2','success':True,'total_tokens':150,'post_first_success_file_reads':0}]
        with patch.multiple(module.h,EVAL_ID='EVAL-004',CONDITIONS={'B':{},'V1':{},'V2':{}}):
            result=module.aggregate(rows)
        self.assertEqual(result['conditions']['V1']['runs'],1)
        self.assertEqual(result['conditions']['V1']['success_rate'],0)
        pair=result['paired_comparisons']['V1 -> V2'][0]
        self.assertEqual(pair['percentage_changes']['total_tokens'],50)
        self.assertIsNone(pair['percentage_changes']['post_first_success_file_reads'])


if __name__=='__main__':unittest.main()
