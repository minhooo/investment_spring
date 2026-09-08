"""Build the shared graph and reproducible empirical validation snapshots."""
import argparse
import csv
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
    for theme in portal['taxonomy']['themes']:
        node('theme:'+theme['id'], theme['label'], 'theme', description='탐색용 분류. 테마 소속은 인과 근거가 아닙니다.')
    for issue in portal['taxonomy']['issues']:
        node('issue:'+issue['id'], issue['label'], 'theme', description='공통 사건 유형. 이 유형만으로 수익률을 예측하지 않습니다.')
    for s in portal['macro']:
        node('scenario:'+s['id'], s['title'], 'scenario', href='macro.html?scenario='+s['id'], description=s['summary'])
        for theme in s['theme_ids']:
            edge('theme:'+theme, 'scenario:'+s['id'], 'membership')
        for key in s['node_ids']:
            d = details[key]
            node(key, d[0], 'variable', description=d[1], lag=d[2], conditions=d[4], limits=d[5],
                 href=f'macro.html?scenario={s["id"]}&node={key}', group=s['id'])
            edge('scenario:'+s['id'], key, 'membership')
    for a, b, sign in relations['paths']:
        edge(a, b, 'hypothesis', sign=sign, mechanism='기존 조건부 전달 경로. 노드 설명의 조건과 한계를 함께 확인.', validation='unmeasured')
    for a, b, sign, reason in relations['bridges']:
        edge(a, b, 'hypothesis', sign=sign, mechanism=reason, bridge=True, validation='unmeasured')
    for case in portal['cases']:
        sid = 'stock:'+case['code']
        node(sid, case['name']+' 주가', 'security', code=case['code'], description='동일 종목의 여러 사례가 공유하는 가격 변수.')
        node(case['id'], case['name']+' · '+case['title'], 'case', description=case['summary'],
             href=case['dashboard_href'], code=case['code'], event_date=case['event_date'])
        edge(sid, case['id'], 'membership')
        for theme in case['theme_ids']:
            edge('theme:'+theme, case['id'], 'membership')
        for issue in case.get('issue_ids', [case['issue_id']]):
            edge('issue:'+issue, case['id'], 'membership')
    for id, label in [('series:brent', '브렌트유 현물'), ('series:fx', '원/달러 환율')]:
        node(id, label, 'series', description='FRED의 현물·환율 관측값. 현재 수정본 기반 탐색 분석.')
    edge('series:brent', 'crude-oil-price', 'measurement', mechanism='브렌트 현물은 국제유가의 관측 지표 중 하나.')
    edge('series:fx', 'dollar', 'measurement', mechanism='원/달러 환율은 달러 순공급 자체가 아니라 외환수급의 불완전한 대리변수.')
    ids = set(nodes)
    if any(e['source'] not in ids or e['target'] not in ids for e in edges):
        raise ValueError('인과 원본의 노드가 누락됐습니다.')
    if len({e['id'] for e in edges}) != len(edges):
        raise ValueError('중복 관계 ID')
    return nodes, edges


def empirical(portal, policy, cutoff):
    import numpy as np
    import pandas as pd
    import scipy
    import statsmodels
    from network_analysis import weekly_returns, analyse_pair, finalize, validate_policy
    validate_policy(policy)
    levels, markets, hashes, sources = {}, {}, {}, {}
    stock_themes = {}
    overrides = read_json(ROOT/'data/causal/series_overrides.json')
    cases = {c['code']: c for c in portal['cases']}
    for c in portal['cases']:
        stock_themes.setdefault(c['code'], set()).update(c['theme_ids'])
    for code, c in cases.items():
        files = sorted((ROOT/'data/prices').glob(code+'_*.csv'))
        if code in overrides:
            files = [ROOT/'data/prices'/overrides[code]['file']]
        if not files:
            continue
        # Current archive has one canonical price file per security.
        if len(files) > 1:
            raise ValueError(f'가격 원본 중복: {code}. 명시적 데이터 매핑 필요.')
        path = files[0]; df = pd.read_csv(path, parse_dates=['date']).set_index('date')
        hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
        levels['stock:'+code] = weekly_returns(df.close, cutoff, policy)
        markets['stock:'+code] = weekly_returns(df.bm_close, cutoff, policy)
        sources['stock:'+code] = {'source': '저장된 수정주가 CSV · 네이버 금융', 'file': path.name,
                                 'end': df.index.max().date().isoformat(), 'vintage': 'latest-revised, not point-in-time'}
    for key, sid in [('brent', 'DCOILBRENTEU'), ('fx', 'DEXKOUS')]:
        path = ROOT/'data/macro'/f'{sid}.csv'
        if not path.exists():
            continue
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        levels['series:'+key] = weekly_returns(df.iloc[:, 0], cutoff, policy)
        hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
        sources['series:'+key] = {'source': 'FRED · '+sid, 'url': 'https://fred.stlouisfed.org/series/'+sid,
                                  'end': df.index.max().date().isoformat(), 'vintage': 'latest-revised, not point-in-time'}
    results = []
    # Predefined family: two macro proxies → all stocks; shared-theme stock pairs.
    # No outcome-based selection and no duplicate tests for two cases of one stock.
    for target in sorted(markets):
        candidates = [s for s in ('series:brent', 'series:fx') if s in levels]
        candidates += [s for s in sorted(markets) if s != target and
                       stock_themes[s.split(':')[1]] & stock_themes[target.split(':')[1]]]
        for source in candidates:
            r = analyse_pair(levels[source], levels[target], markets[target], policy)
            r.update(id='empirical:'+source+':'+target, source=source, target=target, kind='empirical',
                     market_control='대상 종목 벤치마크의 과거 수익률')
            results.append(r)
    finalize(results, policy)
    environment = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
                   'scipy': scipy.__version__, 'statsmodels': statsmodels.__version__}
    return results, sources, hashes, environment


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
    results, sources, hashes, environment = empirical(portal, policy, args.as_of)
    for r in results:
        edges.append(r)
    for key, src in sources.items():
        if key in nodes:
            nodes[key]['data_source'] = src
    for path in [ROOT/'tools/network_analysis.py', ROOT/'tools/build_causal_network.py', ROOT/'data/causal/series_overrides.json',
                 ROOT/'data/causal/relations.json', ROOT/'design/causal-investment-dashboard.html']:
        hashes[path.relative_to(ROOT).as_posix()] = digest(path.read_bytes())
    manifest = {'as_of': args.as_of, 'policy': policy, 'inputs': hashes, 'environment': environment,
                'case_count': len(portal['cases']), 'macro_count': len(portal['macro']),
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
    print(f'인과망: {len(nodes)} 노드, {len(edges)} 연결, {len(results)} 시차 검증, 후보 {sum(r["decision"] == "candidate" for r in results)} · {run_id}')


if __name__ == '__main__':
    main()
