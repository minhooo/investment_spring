"""Auditable exploratory lagged prediction; never identifies structural causality.

Weekly log returns, fixed lag order, market-lag controls, train-only HAC Wald
test, BH across the entire candidate family, expanding out-of-sample folds.
No imputation, random splits, p-value lag shopping or threshold optimisation.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.multitest import multipletests


def validate_policy(p):
    if p.get('frequency') != 'W-FRI':
        raise ValueError('현재는 W-FRI만 지원합니다.')
    for key, lo, hi in [('lags', 1, 8), ('min_observations', 60, 10000), ('folds', 3, 10)]:
        if not isinstance(p[key], int) or not lo <= p[key] <= hi:
            raise ValueError(f'{key}: 정수 {lo}–{hi} 필요')
    for key, lo, hi in [('train_fraction', .5, .8), ('stationarity_alpha', .001, .1),
                        ('fdr_q', .001, .2), ('min_rmse_gain', 0, .5),
                        ('min_positive_folds', .5, 1), ('min_sign_stability', .5, 1)]:
        if not np.isfinite(p[key]) or not lo <= p[key] <= hi:
            raise ValueError(f'{key}: {lo}–{hi} 필요')
    if not isinstance(p['max_gap_days'], int) or not 7 <= p['max_gap_days'] <= 14:
        raise ValueError('max_gap_days: 7–14 정수 필요')
    if not p.get('version') or not p.get('reason'):
        raise ValueError('version과 reason이 필요합니다.')


def weekly_returns(series, cutoff, policy):
    s = pd.to_numeric(series, errors='coerce').sort_index()
    s = s[~s.index.duplicated(keep='last')]
    s = s.where(s > 0)
    # Last complete Friday only; an unfinished current week is never used.
    cutoff = pd.Timestamp(cutoff)
    last_friday = cutoff - pd.Timedelta(days=(cutoff.weekday() - 4) % 7)
    s = s.loc[:last_friday]
    levels = s.resample(policy['frequency']).last()
    dates = pd.Series(s.index.where(s.notna()), index=s.index).resample(policy['frequency']).last()
    ret = np.log(levels).diff()
    ret = ret.where((dates - dates.shift()).dt.days <= policy['max_gap_days'])
    return (ret * 100).replace([np.inf, -np.inf], np.nan)


def design_frame(source, target, market, lags):
    # Calendar joins BEFORE shifts/dropna: missing weeks never become adjacent.
    raw = pd.concat({'x': source, 'y': target, 'market': market}, axis=1, sort=True).sort_index()
    raw = raw.reindex(pd.date_range(raw.index.min(), raw.index.max(), freq='W-FRI'))
    cols = {'y': raw.y}
    for j in range(1, lags + 1):
        cols[f'y{j}'] = raw.y.shift(j)
        cols[f'm{j}'] = raw.market.shift(j)
        cols[f'x{j}'] = raw.x.shift(j)
    return pd.DataFrame(cols).replace([np.inf, -np.inf], np.nan).dropna()


def analyse_pair(source, target, market, policy):
    k = policy['lags']
    frame = design_frame(source, target, market, k)
    result = {'n': len(frame), 'lag_weeks': k, 'status': 'insufficient', 'q_value': None}
    if len(frame) < policy['min_observations']:
        result['reason'] = '공통 관측치 부족'
        return result
    n0 = int(len(frame) * policy['train_fraction'])
    if len(frame) - n0 < policy['folds'] * 5:
        result['reason'] = '검증 구간 부족'
        return result
    base = ['const'] + [c for c in frame if c.startswith(('y', 'm')) and c != 'y']
    full = base + [f'x{j}' for j in range(1, k + 1)]
    frame['const'] = 1.
    train = frame.iloc[:n0]
    result.update(start=frame.index[0].date().isoformat(), end=frame.index[-1].date().isoformat(),
                  train_end=train.index[-1].date().isoformat(), test_start=frame.index[n0].date().isoformat())
    if np.linalg.matrix_rank(train[full]) < len(full):
        result['reason'] = '공선성 또는 상수 계열'
        return result
    try:
        adf = {name: float(adfuller(values.dropna(), autolag='AIC', result_object=False)[1])
               for name, values in {'source': source.loc[:train.index[-1]],
                                     'target': target.loc[:train.index[-1]],
                                     'market': market.loc[:train.index[-1]]}.items()}
        result['adf_p'] = adf
        if max(adf.values()) > policy['stationarity_alpha']:
            result['status'] = 'nonstationary'
            result['reason'] = '훈련 구간 정상성 점검 미통과'
            return result
        fit = sm.OLS(train.y, train[full]).fit(cov_type='HAC', cov_kwds={'maxlags': k})
        restriction = np.zeros((k, len(full)))
        restriction[:, -k:] = np.eye(k)
        result['p_value'] = float(fit.wald_test(restriction, scalar=True).pvalue)
        # Sum of distributed-lag coefficients, not a structural impulse response.
        c = np.zeros(len(full)); c[-k:] = 1
        ci = fit.t_test(c).conf_int()[0]
        result['effect'] = float(fit.params.iloc[-k:].sum())
        result['effect_ci'] = [float(ci[0]), float(ci[1])]
        result['effect_unit'] = '원인 주간 로그수익률 1%p당 대상 %p, 시차계수 합 (구조적 충격반응 아님)'
        result['coefficients'] = {f'x{j}': float(fit.params[f'x{j}']) for j in range(1, k + 1)}
        folds, err0, err1, signs = [], [], [], []
        for positions in np.array_split(np.arange(n0, len(frame)), policy['folds']):
            train_fold = frame.iloc[:positions[0]]
            test = frame.iloc[positions]
            b = sm.OLS(train_fold.y, train_fold[base]).fit()
            f = sm.OLS(train_fold.y, train_fold[full]).fit()
            e0 = (test.y - b.predict(test[base])).to_numpy() ** 2
            e1 = (test.y - f.predict(test[full])).to_numpy() ** 2
            gain = 1 - np.sqrt(e1.mean()) / max(np.sqrt(e0.mean()), 1e-12)
            effect = float(f.params.iloc[-k:].sum())
            signs.append(np.sign(effect))
            err0.extend(e0); err1.extend(e1)
            folds.append({'train_end': train_fold.index[-1].date().isoformat(),
                          'start': test.index[0].date().isoformat(), 'end': test.index[-1].date().isoformat(),
                          'n': len(test), 'rmse_gain': float(gain), 'effect': effect})
        result.update(status='tested', folds=folds,
                      rmse_base=float(np.sqrt(np.mean(err0))), rmse_full=float(np.sqrt(np.mean(err1))),
                      rmse_gain=float(1 - np.sqrt(np.mean(err1)) / max(np.sqrt(np.mean(err0)), 1e-12)),
                      positive_folds=float(np.mean([f['rmse_gain'] > 0 for f in folds])),
                      sign_stability=float(np.mean(np.asarray(signs) == np.sign(result['effect']))),
                      reason='과거→미래 순차 검증. 현재 수정본 자료의 탐색 분석이며 당시 투자성과 아님.')
    except (ValueError, np.linalg.LinAlgError) as exc:
        result.update(status='error', reason=f'계산 제외: {type(exc).__name__}')
    return result


def classify(r, p):
    if r.get('status') != 'tested':
        return r.get('status', 'unmeasured')
    checks = [r['q_value'] <= p['fdr_q'], r['rmse_gain'] >= p['min_rmse_gain'],
              r['positive_folds'] >= p['min_positive_folds'], r['sign_stability'] >= p['min_sign_stability']]
    return 'candidate' if all(checks) else 'not_supported'


def finalize(results, policy):
    # Include excluded hypotheses conservatively with p=1 in the fixed family.
    ps = [r.get('p_value', 1.) for r in results]
    qs = multipletests(ps, method='fdr_bh')[1] if ps else []
    for r, q in zip(results, qs):
        if r['status'] == 'tested':
            r['q_value'] = float(q)
        r['decision'] = classify(r, policy)
    return results
