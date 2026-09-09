"""Scope regression tests for the macro-only causal network payload."""
import json
import unittest
from pathlib import Path

from build_causal_network import ROOT, graph_data, macro_details, read_json


class MacroOnlyScopeTests(unittest.TestCase):
    def test_graph_excludes_case_explorer_entities(self):
        snapshot = (ROOT / 'dist' / 'portal-data.js').read_text(encoding='utf-8')
        portal = json.loads(snapshot.split('=', 1)[1].rstrip(';\n'))['data']
        nodes, edges = graph_data(portal, macro_details(), read_json(ROOT / 'data' / 'causal' / 'relations.json'))

        self.assertEqual({node['kind'] for node in nodes.values()}, {'scenario', 'variable'})
        self.assertEqual(len([node for node in nodes.values() if node['kind'] == 'scenario']), len(portal['macro']))
        self.assertFalse(any(key.startswith(('case-', 'stock:', 'theme:', 'issue:', 'series:')) for key in nodes))
        self.assertFalse(any(edge['kind'] == 'empirical' for edge in edges))

        bond = nodes['fixed-rate-bond-price']
        self.assertIn('고정금리', bond['label'])
        self.assertIn('재투자 위험', ' '.join(bond['limits']))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'lt-rate'
            and edge['target'] == 'fixed-rate-bond-price'
            and edge['sign'] == '-'
            for edge in edges
        ))

        cross_listing = nodes['us-cross-listing-access']
        self.assertIn('ADR', cross_listing['label'])
        self.assertIn('원주 가격', ' '.join(cross_listing['limits']))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'equity-required-return'
            and edge['target'] == 'equity-multiple'
            and edge['sign'] == '-'
            and edge.get('bridge')
            for edge in edges
        ))

        lng_risk = nodes['hormuz-lng-disruption-risk']
        self.assertIn('LNG', lng_risk['label'])
        self.assertIn('2024년', ' '.join(lng_risk['limits']))
        europe_gas = nodes['europe-gas-price']
        self.assertIn('TTF', europe_gas['label'])
        self.assertIn('130%', ' '.join(europe_gas['limits']))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'europe-gas-price'
            and edge['target'] == 'power-price'
            and edge['sign'] == '+'
            and edge.get('bridge')
            for edge in edges
        ))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'power-price'
            and edge['target'] == 'ai'
            and edge['sign'] == '-'
            and edge.get('bridge')
            for edge in edges
        ))

        buyback = nodes['buyback-authorization']
        self.assertIn('이사회 결의', buyback['label'])
        self.assertIn('실제 체결이 아니', ' '.join(buyback['limits']))
        completion = nodes['buyback-program-completion']
        self.assertIn('11월 19일', ' '.join(completion['limits']))
        self.assertIn('급락', ' '.join(completion['limits']))
        post_use = nodes['buyback-post-use']
        self.assertIn('임직원 보상', post_use['label'])
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'buyback-flow-intensity'
            and edge['target'] == 'issuer-price-support-pressure'
            and edge['sign'] == 'conditional'
            for edge in edges
        ))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'buyback-program-completion'
            and edge['target'] == 'buyback-flow-intensity'
            and edge['sign'] == '-'
            for edge in edges
        ))

        small_firm = nodes['small-firm-debt-service-pressure']
        self.assertIn('이자비용', small_firm['label'])
        self.assertIn('비상장 중소기업', ' '.join(small_firm['limits']))
        russell = nodes['russell2000-relative-downside-pressure']
        self.assertIn('Russell 2000', russell['label'])
        self.assertIn('보장 수익', ' '.join(russell['limits']))
        self.assertIn('자동 소멸', ' '.join(russell['limits']))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'refinancing'
            and edge['target'] == 'small-firm-debt-service-pressure'
            and edge['sign'] == '+'
            for edge in edges
        ))
        self.assertTrue(any(
            edge['kind'] == 'hypothesis'
            and edge['source'] == 'small-firm-investment-earnings-pressure'
            and edge['target'] == 'russell2000-relative-downside-pressure'
            and edge['sign'] == 'conditional'
            for edge in edges
        ))

    def test_demo_canvas_keeps_direction_sign_and_focus_contract(self):
        template = (ROOT / 'tools' / 'causal_network_template.html').read_text(encoding='utf-8')

        self.assertIn('const DEMO = {', template)
        self.assertIn("'target-arrow-shape':'triangle'", template)
        self.assertIn("selector:'edge[sign=\"-\"]'", template)
        self.assertIn("selector:'node.upstream'", template)
        self.assertIn("selector:'node.downstream'", template)
        self.assertIn("selector:'.dimmed'", template)
        self.assertIn('function walk(startId,direction)', template)
        self.assertIn('function renderInspector(id,openPanel=true)', template)
        self.assertIn('function centerNode(id)', template)
        self.assertIn('data-focus-node="true"', template)
        self.assertIn('가상 현재 값', template)
        self.assertIn('이 값이 뜻하는 것', template)
        self.assertIn("unit:'KRW/USD'", template)
        self.assertIn("cadence:'월간'", template)
        self.assertIn("cy.on('mouseover','edge'", template)
        self.assertIn("cy.on('tap','edge'", template)
        self.assertIn('function renderEdgeInspector(id,openPanel=true)', template)
        self.assertIn('function selectEdge(id,openPanel=true)', template)
        self.assertIn("selector:'edge.edge-selected'", template)
        self.assertIn("selector:'node.edge-endpoint'", template)
        self.assertIn('touchTapThreshold:18', template)
        self.assertIn('전달 메커니즘', template)
        self.assertIn('성립 조건', template)
        self.assertIn('완충·반대 요인', template)
        self.assertIn('가상 전달 시차', template)
        self.assertIn("mechanism:'", template)
        self.assertIn("counterforce:'", template)
        self.assertIn("url.searchParams.set('edge',id)", template)
        self.assertIn('id="path-form"', template)
        self.assertIn('id="path-from"', template)
        self.assertIn('id="path-to"', template)
        self.assertIn('function findDirectedPath(from,to)', template)
        self.assertIn('function renderPathInspector(path,openPanel=true)', template)
        self.assertIn('function selectPath(from,to,openPanel=true)', template)
        self.assertIn('function setPathStep(index,focusGraph=true)', template)
        self.assertIn('function fitPath()', template)
        self.assertIn("selector:'edge.path-edge'", template)
        self.assertIn("selector:'edge.path-step-active'", template)
        self.assertIn("url.searchParams.set('from',from)", template)
        self.assertIn("url.searchParams.set('to',to)", template)
        self.assertIn('globalThis.__macroCanvasSelectPath', template)
        self.assertIn('globalThis.__macroCanvasDiagnostics', template)
        self.assertIn("layout:{name:'preset'", template)


if __name__ == '__main__':
    unittest.main()
