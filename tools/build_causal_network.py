"""Build the shared graph and reproducible empirical validation snapshots."""
import argparse
import hashlib
import json
import platform
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def macro_details():
    # Read the existing authored literal, never infer edges from visual ordering.
    script = "const fs=require('fs'),vm=require('vm'); const s=fs.readFileSync(process.argv[1],'utf8'); const m=s.match(/const details = (\\{[\\s\\S]*?\\n      \\});/); if(!m) throw Error('Macro details not found'); process.stdout.write(JSON.stringify(vm.runInNewContext('('+m[1]+')',Object.create(null),{timeout:1000})));"
    text = subprocess.check_output(['node', '-e', script, str(ROOT / 'design/causal-investment-dashboard.html')])
    return json.loads(text)


def graph_data(portal, details, relations):
    nodes, edges = {}, []
    def node(id, label, kind, **extra):
        nodes[id] = dict(id=id, label=label, kind=kind, **extra)
    def edge(source, target, kind, **extra):
        edges.append(dict(id=f'{kind}:{source}:{target}', source=source, target=target, kind=kind, **extra))
    for s in portal['macro']:
        node('scenario:'+s['id'], s['title'], 'scenario', href='macro.html?scenario='+s['id'], description=s['summary'])
        for key in s['node_ids']:
            d = details[key]
            node(key, d[0], 'variable', description=d[1], lag=d[2], conditions=d[4], limits=d[5],
                 href=f'macro.html?scenario={s["id"]}&node={key}', group=s['id'])
            edge('scenario:'+s['id'], key, 'membership')
    for a, b, sign in relations['paths']:
        edge(a, b, 'hypothesis', sign=sign, mechanism='기존 조건부 전달 경로. 노드 설명의 조건과 한계를 함께 확인.', validation='unmeasured')
    for a, b, sign, reason in relations['bridges']:
        edge(a, b, 'hypothesis', sign=sign, mechanism=reason, bridge=True, validation='unmeasured')
    # Optional authored notes preserve source-specific conditions on reused paths.
    hypotheses = {e['id']: e for e in edges if e['kind'] == 'hypothesis'}
    for key, note in relations.get('hypothesis_notes', {}).items():
        if key not in hypotheses or not isinstance(note, str) or not note.strip():
            raise ValueError(f'잘못된 가설 근거 참조: {key}')
        hypotheses[key]['mechanism'] = note
    ids = set(nodes)
    if any(e['source'] not in ids or e['target'] not in ids for e in edges):
        raise ValueError('인과 원본의 노드가 누락됐습니다.')
    if len({e['id'] for e in edges}) != len(edges):
        raise ValueError('중복 관계 ID')
    return nodes, edges


def empirical(policy):
    """Keep the lab macro-only until comparable macro series are explicitly registered.

    The previous stock-price family was outside this screen's scope.  Existing FRED
    files are not silently substituted for a different macro variable or frequency.
    """
    from network_analysis import validate_policy
    validate_policy(policy)
    return [], {}, {}, {'python': platform.python_version(), 'mode': 'macro-series-not-yet-registered'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--policy', type=Path, default=ROOT/'data/causal/policy.json')
    p.add_argument('--as-of', default=date.today().isoformat())
    args = p.parse_args()
    policy = read_json(args.policy)
    snapshot = (ROOT/'dist/portal-data.js').read_text(encoding='utf-8')
    portal = json.loads(snapshot.split('=', 1)[1].rstrip(';\n'))['data']
    relations = read_json(ROOT/'data/causal/relations.json')
    nodes, edges = graph_data(portal, macro_details(), relations)
    results, sources, hashes, environment = empirical(policy)
    for r in results:
        edges.append(r)
    for key, src in sources.items():
        if key in nodes:
            nodes[key]['data_source'] = src
    for path in [ROOT/'tools/network_analysis.py', ROOT/'tools/build_causal_network.py', ROOT/'data/causal/policy.json',
                 ROOT/'data/causal/relations.json', ROOT/'design/causal-investment-dashboard.html']:
        hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    manifest = {'as_of': args.as_of, 'policy': policy, 'inputs': hashes, 'environment': environment,
                'scope': 'macro-only', 'macro_count': len(portal['macro']), 'variable_count': sum(len(s['node_ids']) for s in portal['macro']),
                'portal_hash': digest(snapshot.encode('utf-8'))}
    run_id = digest(json.dumps(manifest, sort_keys=True).encode())[:20]
    payload = {'run_id': run_id, 'manifest': manifest, 'nodes': list(nodes.values()), 'edges': edges,
               'results': results, 'sources': sources}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, allow_nan=False)
    runs = ROOT/'data/causal/runs'; runs.mkdir(parents=True, exist_ok=True)
    path = runs/f'{run_id}.json'
    if path.exists() and path.read_text(encoding='utf-8') != raw:
        raise RuntimeError('동일 실행 ID의 결과가 달라졌습니다.')
    path.write_text(raw, encoding='utf-8')
    from site_shell import render_nav
    from dist_names import dist_page
    page = (ROOT/'tools/causal_network_template.html').read_text(encoding='utf-8')
    page = page.replace('<!--__SITE_NAV__-->', render_nav('macro'))
    page = page.replace('/*__NETWORK_DATA__*/null', raw.replace('</', '<\\/'))
    page = page.replace('/*__CYTOSCAPE__*/', (ROOT/'tools/vendor/cytoscape-3.33.1.min.js').read_text(encoding='utf-8'))
    (ROOT/'dist'/dist_page('causal-network')).write_text(page, encoding='utf-8')
    print(f'인과망: 거시 {len(portal["macro"])}개 경로 · {len(nodes)} 노드, {len(edges)} 연결, 등록된 시차 검증 {len(results)}건 · {run_id}')


if __name__ == '__main__':
    main()
