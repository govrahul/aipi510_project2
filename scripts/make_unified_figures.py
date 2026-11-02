"""One model for both sports: basketball (new 100-player Instagram sample) and football (partner sample).

Run from the repository root:  python scripts/make_unified_figures.py

Same specification in each sport (plain-language bar charts, figures 7-11):
    ln(NIL value) ~ ln(1 + Instagram followers) + last-season performance percentile
                    + no-college-stats-last-season flag + years in college
Performance is ranked within each sport: basketball = points per game in 2025-26 (ESPN box scores),
football = PPA per play (partner pull; unverified, zeros treated as missing). Players with no prior college
stats (mostly freshmen) get percentile 0 and flag 1. HC3 robust errors.

Reads (read-only): Data/curated/basketball_instagram_100.csv, Data/football_modeling_data.csv,
  Data/private/basketball/player_team_season_2026.csv, figures/figure_data/roster_trends.csv
Writes: figures/fig7..fig11 (PDF + PNG), figures/figure_data/unified_*.csv/json,
  figures/figure_data/unified_model_diagnostics.json (assumption checks, effect sizes, post hoc tests)
"""
from pathlib import Path
import itertools, json
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.ticker as mt
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import jarque_bera
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "Data"; OUT = ROOT / "figures"; FD = OUT / "figure_data"
FB, BB, TEAL, MUTE, NAVY, SUB, GREY = "#2a78d6", "#eb6834", "#147D80", "#B9C3CB", "#203C55", "#586977", "#9a9a9a"
SPORT_C = {"Basketball": BB, "Football": FB}
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"], "font.size": 10,
    "axes.labelsize": 10, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "legend.fontsize": 9.5, "axes.spines.top": False,
    "axes.spines.right": False, "axes.linewidth": 0.7, "pdf.fonttype": 42, "savefig.dpi": 300})
MONEY = mt.FuncFormatter(lambda v, _: f"${v/1e6:g}M" if v >= 1e6 else f"${v/1e3:g}K")
YR = {"Freshman": 1, "Sophomore": 2, "Junior": 3, "Redshirt Junior": 3, "Senior": 4, "Graduate": 5}
SPEC = "ln_nil ~ ln_f + perf + no_stats + year"
GROUPS = {"Instagram followers": ["ln_f"], "Last-season performance": ["perf", "no_stats"], "Years in college": ["year"]}


def save(fig, name):
    fig.tight_layout()
    for ext in ("pdf", "png"): fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)


def load():
    b = pd.read_csv(DATA / "curated/basketball_instagram_100.csv")
    box = (pd.read_csv(DATA / "private/basketball/player_team_season_2026.csv", usecols=["athlete_id", "Points_Per_Game", "Games"])
           .sort_values("Games", ascending=False).drop_duplicates("athlete_id"))   # mid-season movers: keep the team with most games
    b = b.merge(box, left_on="ESPN_Athlete_ID_Candidate", right_on="athlete_id", how="left", validate="m:1")
    B = pd.DataFrame(dict(sport="Basketball", nil=b.NIL_Valuation_USD, followers=b.Instagram_Followers, year=b.Grade.map(YR),
                          perf_raw=b.Points_Per_Game, top=b.Quartile.eq("Q4_Highest")))
    f = pd.read_csv(DATA / "football_modeling_data.csv")
    F = pd.DataFrame(dict(sport="Football", nil=f.Valuation, followers=f["Instagram Followers"], year=f.Grade.map(YR),
                          perf_raw=f.PPA_Per_Play.where(f.PPA_Per_Play != 0), top=f["Valuation Tier"].eq("Top_25")))
    d = pd.concat([B, F], ignore_index=True)
    d["year"] = d.year.fillna(d.groupby("sport").year.transform("median"))   # one basketball player has no listed class
    d["ln_nil"], d["ln_f"] = np.log(d.nil), np.log1p(d.followers)
    d["no_stats"] = d.perf_raw.isna().astype(int)
    d["perf"] = d.groupby("sport").perf_raw.rank(pct=True).fillna(0) * 100
    return d


def r2(g, terms):
    return smf.ols("ln_nil ~ " + (" + ".join(terms) if terms else "1"), g).fit().rsquared


def dominance(g):
    """General dominance: each factor's average added R-squared over all subsets of the other factors."""
    names, out = list(GROUPS), {}
    for k in names:
        others = [n for n in names if n != k]; per_size = []
        for size in range(len(others) + 1):
            per_size.append(np.mean([r2(g, sum((GROUPS[n] for n in sub), []) + GROUPS[k]) - r2(g, sum((GROUPS[n] for n in sub), []))
                                     for sub in itertools.combinations(others, size)]))
        out[k] = float(np.mean(per_size))
    return out


def analyse(d):
    res, rng = {}, np.random.default_rng(510)
    for s, g in d.groupby("sport"):
        r = smf.ols(SPEC, g).fit(cov_type="HC3"); lo, hi = r.conf_int().loc["ln_f"]
        dom = dominance(g); tot = sum(dom.values())
        boot = []
        for _ in range(1000):
            gb = g.sample(len(g), replace=True, random_state=int(rng.integers(1e9)))
            db = dominance(gb); boot.append({k: v / sum(db.values()) * 100 for k, v in db.items()})
        boot = pd.DataFrame(boot)
        sub = g[~g.top]; rs = smf.ols(SPEC, sub).fit(cov_type="HC3"); slo, shi = rs.conf_int().loc["ln_f"]
        res[s] = dict(n=int(r.nobs), r2=r.rsquared, beta_followers=r.params.ln_f, ci=[lo, hi], p_followers=r.pvalues.ln_f,
                      doubling_pct=100 * (2 ** r.params.ln_f - 1), doubling_ci=[100 * (2 ** lo - 1), 100 * (2 ** hi - 1)],
                      coefs={k: float(v) for k, v in r.params.items()}, pvalues={k: float(v) for k, v in r.pvalues.items()},
                      share_of_explained={k: v / tot * 100 for k, v in dom.items()},
                      share_ci={k: [float(boot[k].quantile(.025)), float(boot[k].quantile(.975))] for k in dom},
                      without_top_quarter=dict(n=int(rs.nobs), beta=rs.params.ln_f, p=rs.pvalues.ln_f,
                                               doubling_pct=100 * (2 ** rs.params.ln_f - 1),
                                               doubling_ci=[100 * (2 ** slo - 1), 100 * (2 ** shi - 1)]),
                      median_followers=float(g.followers.median()), median_nil=float(g.nil.median()),
                      with_prior_stats=int((g.no_stats == 0).sum()))
    pooled = smf.ols("ln_nil ~ (ln_f + perf + no_stats + year) * C(sport)", d).fit(cov_type="HC3")
    res["sport_difference_in_follower_slope"] = dict(estimate=pooled.params["ln_f:C(sport)[T.Football]"],
                                                     p=pooled.pvalues["ln_f:C(sport)[T.Football]"])
    (FD / "unified_model_results.json").write_text(json.dumps(res, indent=2, default=float) + "\n")
    return res


def holm_pairs(groups):
    """Post hoc for a Kruskal-Wallis test: every pair by Mann-Whitney U, Holm-adjusted."""
    names = list(groups); pairs = list(itertools.combinations(names, 2))
    raw = [stats.mannwhitneyu(groups[a], groups[b], alternative="two-sided").pvalue for a, b in pairs]
    adj = multipletests(raw, method="holm")[1]
    return [dict(pair=f"{a} vs {b}", p_raw=float(r), p_holm=float(h)) for (a, b), r, h in zip(pairs, raw, adj)]


def diagnostics(d):
    """Assumption checks and effect sizes for the shared model, plus post hoc tests for the group comparisons."""
    out = {}
    for s, g in d.groupby("sport"):
        ols = smf.ols(SPEC, g).fit(); X = ols.model.exog; infl = ols.get_influence()
        reduced = smf.ols("ln_nil ~ perf + no_stats + year", g).fit()
        f2 = (ols.rsquared - reduced.rsquared) / (1 - ols.rsquared)
        q = pd.qcut(g.followers.rank(method="first"), 4, labels=["Fewest", "Fewer", "More", "Most"])
        grp = {k: g.nil[q == k].values for k in ["Fewest", "Fewer", "More", "Most"]}
        kw = stats.kruskal(*grp.values())
        out[s] = dict(
            breusch_pagan_p=float(het_breuschpagan(ols.resid, X)[1]), jarque_bera_p=float(jarque_bera(ols.resid)[1]),
            max_vif=float(max(variance_inflation_factor(X, i) for i in range(1, X.shape[1]))),
            cooks_over_4_n=int((infl.cooks_distance[0] > 4 / len(g)).sum()), max_leverage=float(infl.hat_matrix_diag.max()),
            partial_f2_followers=float(f2), r2_without_followers=float(reduced.rsquared), adj_r2=float(ols.rsquared_adj),
            spearman_followers_nil=float(stats.spearmanr(g.followers, g.nil)[0]),
            follower_groups_kruskal=dict(H=float(kw.statistic), p=float(kw.pvalue),
                                         epsilon_sq=float(kw.statistic / (len(g) - 1)), posthoc=holm_pairs(grp)))
    m = pd.read_csv(DATA / "football_modeling_data.csv")
    st = {f"{k}-star": m.Valuation[m["Star Rating"] == k].values for k in (3, 4, 5)}
    kw = stats.kruskal(*st.values())
    out["Football stars"] = dict(n={k: len(v) for k, v in st.items()}, median={k: float(np.median(v)) for k, v in st.items()},
                                 H=float(kw.statistic), p=float(kw.pvalue), epsilon_sq=float(kw.statistic / (len(m) - 1)), posthoc=holm_pairs(st))
    (FD / "unified_model_diagnostics.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def follower_effect_fig(res):
    fig, ax = plt.subplots(figsize=(4.6, 3.4)); xs = np.arange(2)
    sp = ["Basketball", "Football"]; v = [res[s]["doubling_pct"] for s in sp]; ci = [res[s]["doubling_ci"] for s in sp]
    ax.bar(xs, v, width=0.55, color=[SPORT_C[s] for s in sp])
    ax.errorbar(xs, v, yerr=[[a - c[0] for a, c in zip(v, ci)], [c[1] - a for a, c in zip(v, ci)]], fmt="none", ecolor=NAVY, capsize=4, lw=1)
    for x, a, c in zip(xs, v, ci): ax.text(x, c[1] + 2, f"+{a:.0f}%", ha="center", va="bottom", fontsize=12, fontweight="bold", color=NAVY)
    ax.set_xticks(xs); ax.set_xticklabels(sp); ax.set_ylim(0, max(c[1] for c in ci) + 14)
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda y, _: f"+{y:.0f}%" if y else "0%"))
    ax.set_ylabel("Higher NIL value for twice the followers\n(same model in both sports)")
    ax.text(0, 1.02, "Lines show the 95% range", transform=ax.transAxes, fontsize=8.5, color=SUB)
    save(fig, "fig9_follower_effect_by_sport")


def importance_fig(res):
    names = list(GROUPS)[::-1]; fig, ax = plt.subplots(figsize=(6.0, 3.4)); y = np.arange(len(names)); h = 0.36
    for k, s in enumerate(["Football", "Basketball"]):
        v = [res[s]["share_of_explained"][n] for n in names]; ci = [res[s]["share_ci"][n] for n in names]
        yy = y + (k - 0.5) * h
        ax.barh(yy, v, height=h, color=SPORT_C[s], label=f"{s} (model explains {res[s]['r2']*100:.0f}% overall)")
        ax.errorbar(v, yy, xerr=[[a - c[0] for a, c in zip(v, ci)], [c[1] - a for a, c in zip(v, ci)]], fmt="none", ecolor=NAVY, capsize=2.5, lw=0.9)
        for a, c, yv in zip(v, ci, yy): ax.text(c[1] + 1.5, yv, f"{a:.0f}%", va="center", fontsize=9.5, fontweight="bold", color=NAVY)
    ax.set_yticks(y); ax.set_yticklabels(names); ax.set_xlim(0, 112); ax.xaxis.set_major_formatter(mt.PercentFormatter(decimals=0))
    ax.set_xlabel("Share of the model’s explained differences in NIL value")
    h_, l_ = ax.get_legend_handles_labels(); ax.legend(h_[::-1], l_[::-1], frameon=False, loc="upper center", bbox_to_anchor=(0.4, -0.2), ncol=1, fontsize=8.5)
    ax.text(0, 1.02, "Lines show the 95% bootstrap range", transform=ax.transAxes, fontsize=8.5, color=SUB)
    save(fig, "fig10_feature_importance")


def top_market_fig(res):
    sp = ["Basketball", "Football"]; fig, ax = plt.subplots(figsize=(6.4, 3.3)); xs = np.arange(2); w = 0.36
    for k, (lab, key, col) in enumerate([("All 100 players", None, None), ("Leaving out the top-valued 25", "without_top_quarter", None)]):
        v = [res[s]["doubling_pct"] if key is None else res[s][key]["doubling_pct"] for s in sp]
        ci = [res[s]["doubling_ci"] if key is None else res[s][key]["doubling_ci"] for s in sp]
        xx = xs + (k - 0.5) * w
        ax.bar(xx, v, width=w, color=[SPORT_C[s] for s in sp], alpha=1 if key is None else 0.35, label=lab,
               edgecolor=[SPORT_C[s] for s in sp], linewidth=1)
        ax.errorbar(xx, v, yerr=[[a - c[0] for a, c in zip(v, ci)], [c[1] - a for a, c in zip(v, ci)]], fmt="none", ecolor=NAVY, capsize=3, lw=0.9)
        for x, a, c in zip(xx, v, ci): ax.text(x, c[1] + 2, f"{a:+.0f}%", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=NAVY)
    ax.axhline(0, color=NAVY, lw=0.8); ax.set_xticks(xs); ax.set_xticklabels(sp)
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda y, _: f"{y:+.0f}%" if y else "0%"))
    ax.set_ylabel("Higher NIL value for\ntwice the followers"); ax.set_ylim(-25, 85)
    from matplotlib.patches import Patch
    ax.legend([Patch(color=GREY), Patch(facecolor=GREY, alpha=0.35, edgecolor=GREY)], ["All 100 players", "Leaving out the top-valued 25"], frameon=False, loc="upper right")
    ax.text(0, 1.02, "Lines show the 95% range", transform=ax.transAxes, fontsize=8.5, color=SUB)
    save(fig, "fig11_follower_effect_top_market")


def transfer_rate_fig(t):
    """Fig 7: share of roster players who transferred in, by season, both sports (grouped bars)."""
    t = t[t.transfer_in_share.notna()]; seasons = sorted(t.season.unique()); xs = np.arange(len(seasons)); w = 0.4
    fig, ax = plt.subplots(figsize=(10.5, 3.4))
    for k, sp in enumerate(["Basketball", "Football"]):
        v = t[t.sport.str.startswith(sp)].set_index("season").transfer_in_share.reindex(seasons) * 100
        ax.bar(xs + (k - 0.5) * w, v.values, width=w, color=SPORT_C[sp], label=sp)
        ax.text(xs[-1] + (k - 0.5) * w, v.values[-1] + 0.5, f"{v.values[-1]:.0f}%", ha="center", va="bottom", fontsize=10, fontweight="bold", color=NAVY)
        ax.text(xs[0] + (k - 0.5) * w, v.values[0] + 0.5, f"{v.values[0]:.0f}%", ha="center", va="bottom", fontsize=9, color=NAVY)
    nil = seasons.index(2022) - 0.5; ax.axvline(nil, color=NAVY, ls=(0, (3, 2)), lw=1)
    ax.text(nil - 0.1, 0.97, "NIL begins\n(July 2021)", transform=ax.get_xaxis_transform(), ha="right", va="top", fontsize=9, color=NAVY)
    ax.set_xticks(xs); ax.set_xticklabels([str(y) for y in seasons]); ax.set_xlabel("Season (2026 football is mid-season)")
    ax.set_ylabel("Players who transferred in\n(% of roster)"); ax.yaxis.set_major_formatter(mt.PercentFormatter(decimals=0)); ax.set_ylim(0, 31)
    ax.legend(frameon=False, loc="upper left")
    save(fig, "fig7_transfer_rate_by_sport")


def nil_by_followers_both_fig(d):
    """Fig 8: typical NIL value by follower group (quarters within each sport), both sports (grouped bars)."""
    fmt = lambda v: f"{v/1e6:g}M" if v >= 1e6 else (f"{v/1e3:.1f}K".replace(".0K", "K") if v >= 1e3 else f"{v:.0f}")
    fig, ax = plt.subplots(figsize=(10.5, 3.6)); xs = np.arange(4); w = 0.4; rows = []; ranges = {}
    for k, sp in enumerate(["Basketball", "Football"]):
        g = d[d.sport == sp]; q = pd.qcut(g.followers, 4, labels=False)
        meds = [g.nil[q == i].median() for i in range(4)]; ranges[sp] = [(g.followers[q == i].min(), g.followers[q == i].max()) for i in range(4)]
        ax.bar(xs + (k - 0.5) * w, meds, width=w, color=SPORT_C[sp], label=sp + (" (all price levels)" if sp == "Basketball" else " (top 1,000 only: $350K+)"))
        for x, v in zip(xs + (k - 0.5) * w, meds): ax.text(x, v, f"${v/1e3:,.0f}K", ha="center", va="bottom", fontsize=9.5, fontweight="bold", color=NAVY)
        rows += [dict(sport=sp, group=i + 1, followers_min=ranges[sp][i][0], followers_max=ranges[sp][i][1], median_nil=meds[i]) for i in range(4)]
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{n}\nBasketball {fmt(ranges['Basketball'][i][0])}–{fmt(ranges['Basketball'][i][1])}\nFootball {fmt(ranges['Football'][i][0])}–{fmt(ranges['Football'][i][1])}"
                        for i, n in enumerate(["Fewest followers", "Fewer", "More", "Most followers"])], fontsize=8.8)
    ax.yaxis.set_major_formatter(MONEY); ax.set_ylim(0, 820e3); ax.set_ylabel("Typical (median) NIL value")
    ax.legend(frameon=False, loc="upper left")
    pd.DataFrame(rows).to_csv(FD / "nil_by_follower_group_by_sport.csv", index=False)
    save(fig, "fig8_nil_by_follower_group_by_sport")


if __name__ == "__main__":
    d = load()
    t = pd.read_csv(FD / "roster_trends.csv")
    import sys
    cache = FD / "unified_model_results.json"
    res = json.loads(cache.read_text()) if "--cached" in sys.argv and cache.exists() else analyse(d)   # --cached skips the 1,000-draw bootstrap
    diagnostics(d)
    transfer_rate_fig(t); nil_by_followers_both_fig(d)
    follower_effect_fig(res); importance_fig(res); top_market_fig(res)
    print(json.dumps({s: {k: res[s][k] for k in ("n", "r2", "doubling_pct", "p_followers", "share_of_explained")} for s in ("Basketball", "Football")}, indent=1, default=float))
