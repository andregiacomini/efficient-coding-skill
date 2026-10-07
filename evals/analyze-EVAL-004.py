#!/usr/bin/env python3
"""Uniform post-hoc EVAL-004 analysis; never executes a coding agent or grader."""
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from datetime import datetime,timezone
import posthoc_trace

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('frozen_runner',Path(__file__).with_name('run-eval.py'))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

NUMERIC=['total_tokens','input_tokens','cached_input_tokens','output_tokens','duration_seconds','tool_calls',
 'repository_search_commands','total_file_reads','repository_file_reads','unique_files_inspected','repeated_file_reads','test_runs',
 'files_modified','skill_loading_events','time_until_first_edit_seconds','time_until_first_targeted_success_seconds',
 'searches_before_first_edit','unique_repository_files_before_first_edit','tool_items_before_first_edit',
 'post_first_success_tool_calls','post_first_success_searches','post_first_success_file_reads','post_first_success_test_executions',
 'last_edit_time_seconds','last_test_time_seconds','last_validation_time_seconds','edits_after_first_targeted_success',
 'edits_after_last_test_execution','edits_after_last_validation','tool_calls_between_first_success_and_final_edit','tool_calls_after_final_edit']
BOOLEAN=['final_edit_revalidated','repository_edited_after_last_test','production_edited_after_last_test','test_edited_after_last_test',
 'validation_after_final_production_edit','validation_after_final_test_file_edit','final_production_edit_revalidated','final_test_file_edit_revalidated']
PAIRED=['total_tokens','duration_seconds','post_first_success_tool_calls','post_first_success_searches','post_first_success_file_reads','post_first_success_test_executions']


def aggregate(rows):
    groups={arm:[r for r in rows if r['condition']==arm and r.get('infrastructure_failure') is None] for arm in h.conditions()}
    result={'eval_id':'EVAL-004','analysis_schema_version':5,'analysis_revision':'5.0','status':'COMPLETE' if len(rows)==9 else 'PARTIAL',
            'primary_comparison':'V1 -> V2','conditions':{},'paired_comparisons':{},'runs':rows,'statistical_significance_claimed':False}
    for arm,group in groups.items():
        out={'runs':len(group),'successful_runs':sum(r.get('success') is True for r in group),'success_rate':sum(r.get('success') is True for r in group)/len(group) if group else None,'metrics':{},'indicators':{}}
        for key in NUMERIC:
            values=[r[key] for r in group if type(r.get(key)) in (int,float)]
            out['metrics'][key]={'n_available':len(values),'mean':statistics.mean(values) if values else None,'median':statistics.median(values) if values else None}
        for key in BOOLEAN:
            values=[r[key] for r in group if type(r.get(key)) is bool]
            out['indicators'][key]={'true':sum(values),'false':len(values)-sum(values),'unavailable':len(group)-len(values),'rate_true':sum(values)/len(values) if values else None}
        result['conditions'][arm]=out
    for left,right in [('V1','V2'),('B','V1'),('B','V2')]:
        pairs=[]
        for i in range(1,4):
            a=next((r for r in groups[left] if r['run_id'].endswith(str(i))),None)
            b=next((r for r in groups[right] if r['run_id'].endswith(str(i))),None)
            if not a or not b:continue
            diffs={key:(b[key]-a[key])/a[key]*100 if type(a.get(key)) in (int,float) and a[key]>0 and type(b.get(key)) in (int,float) else None for key in PAIRED}
            pairs.append({'left':a['run_id'],'right':b['run_id'],'percentage_changes':diffs})
        result['paired_comparisons'][left+' -> '+right]=pairs
    return result


def report(data):
    def show(v):return 'N/D' if v is None else f'{v:.3f}' if type(v) is float else str(v)
    lines=['# EVAL-004 post-hoc report — '+data['status'],'','Primary comparison: v0.1 → v0.2. Three repetitions provide no significance claim.','',
           '| Run | Success | Tokens | Seconds | Tools | Searches | Reads | Tests | Final edit revalidated |',
           '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for r in data['runs']:
        lines.append('| '+' | '.join(show(r.get(k)) for k in ['run_id','success','total_tokens','duration_seconds','tool_calls','repository_search_commands','total_file_reads','test_runs','final_edit_revalidated'])+' |')
    lines+=['','| Aggregate | B | V1 | V2 |','| --- | ---: | ---: | ---: |']
    for key in ['runs','successful_runs','success_rate']:
        lines.append('| '+key+' | '+' | '.join(show(data['conditions'][a][key]) for a in h.conditions())+' |')
    for key in NUMERIC:
        for stat in ('mean','median'):
            lines.append('| '+stat+' '+key+' | '+' | '.join(show(data['conditions'][a]['metrics'][key][stat]) for a in h.conditions())+' |')
    lines+=['','| Indicator (true / false / unavailable; proportion true) | B | V1 | V2 |','| --- | --- | --- | --- |']
    for key in BOOLEAN:
        values=[]
        for arm in h.conditions():
            v=data['conditions'][arm]['indicators'][key];values.append(f'{v["true"]} / {v["false"]} / {v["unavailable"]}; '+show(v['rate_true']))
        lines.append('| '+key+' | '+' | '.join(values)+' |')
    for comparison,pairs in data['paired_comparisons'].items():
        lines+=['','## '+comparison+(' (primary)' if comparison=='V1 -> V2' else ''),'',
          '| Pair | Tokens Δ% | Duration Δ% | Post tools Δ% | Post searches Δ% | Post reads Δ% | Post tests Δ% |',
          '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for pair in pairs:lines.append('| '+pair['left']+' / '+pair['right']+' | '+' | '.join(show(pair['percentage_changes'][k]) for k in PAIRED)+' |')
    lines+=['','Counts/time/indicator definitions: [EVAL-004-posthoc.md](../../EVAL-004-posthoc.md).',
             'Available-value sample counts are in posthoc-aggregate.json. A zero denominator yields N/D.',
             'Repeated reads, post-success activity and unrevalidated final edits are observations, not automatic defects/waste.',
             'External grader success is separate from solver-side final-edit revalidation.','']
    h.save(h.RESULTS/'posthoc-report.md','\n'.join(lines))


def main():
    h.configure('EVAL-004');h.verify_harness_inputs();h.workspace_checkpoint('posthoc-before')
    rows=[];recovered={};raw_hashes={};archive=h.RESULTS/'instrumentation-v4'
    h.analyze_actions=posthoc_trace.analyze_actions
    for run in h.ORDER:
        directory=h.RESULTS/run;path=directory/'summary.json'
        if not path.exists():continue
        summary=json.loads(path.read_text())
        if summary.get('infrastructure_failure'):raise h.InfrastructureError('Stop analysis of infrastructure failure: '+run)
        for name in ('summary.json','trajectory.json'):
            dest=archive/run/name
            if not dest.exists():h.save(dest,(directory/name).read_bytes())
        previous=json.loads((archive/run/'summary.json').read_text())
        raw={str(p.relative_to(ROOT)):h.digest(p) for p in directory.iterdir() if p.name not in ('summary.json','trajectory.json')}
        metrics,details=h.parse_trace(directory/'codex.jsonl')
        if not details['trace_completed']:raise h.InfrastructureError('Incomplete raw trace: '+run)
        for key in ('input_tokens','cached_input_tokens','output_tokens','total_tokens','tool_calls'):
            if metrics[key]!=previous[key]:raise h.InfrastructureError('Native metric changed: '+run+' '+key)
        summary.update(metrics)
        h.save_json(path,summary);h.save_json(directory/'trajectory.json',details['trajectory'])
        for n,sha in raw.items():
            if h.digest(ROOT/n)!=sha:raise h.InfrastructureError('Raw artifact changed: '+n)
        raw_hashes.update(raw);rows.append(summary)
        recovered[run]={key:metrics[key] for key in metrics if key in previous and previous[key] is None and metrics[key] is not None}
        print(run,'recovered:',json.dumps(recovered[run]),'final_edit_revalidated:',summary['final_edit_revalidated'],flush=True)
    data=aggregate(rows);h.save_json(h.RESULTS/'posthoc-aggregate.json',data);report(data)
    h.report() # Frozen native report includes the reprocessed common metrics.
    h.workspace_checkpoint('posthoc-after')
    payload={'eval_id':'EVAL-004','analysis_schema_version':5,'analysis_revision':'5.0','updated_at':datetime.now(timezone.utc).isoformat(),
       'run_ids':[r['run_id'] for r in rows],'recovered_metrics':recovered,'raw_artifact_sha256':raw_hashes,
       'analysis_input_sha256':{str(p.relative_to(ROOT)):h.digest(p) for p in [Path(__file__).resolve(),ROOT/'evals/posthoc_trace.py',ROOT/'evals/test_posthoc_trace.py',ROOT/'evals/EVAL-004-posthoc.md']},
       'frozen_config_sha256':h.digest(h.BENCHMARK_CONFIG),'original_execution_parser_sha256':h.digest(ROOT/'evals/trace_analysis.py'),
       'execution_environment_unchanged':True,'raw_artifacts_unchanged':True,'first_triplet_not_rerun':True}
    h.save_json(h.RESULTS/'posthoc-manifest.json',payload)
    return 0


if __name__=='__main__':sys.exit(main())
