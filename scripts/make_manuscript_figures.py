"""Manuscript figures for the NIL project. Run from the repository root:

    python scripts/make_manuscript_figures.py

Reads (read-only):
  Data/football_modeling_data.csv
  Data/private/evaluation/football_rosters/cfb_rosters_2015..2026.parquet
  Data/private/evaluation/basketball_values/mbb_player_value_2015..2026.parquet
  Data/private/basketball/division_i_player_team_season_2026.csv
Writes figures/fig1..fig6 as PDF (vector) and PNG (300 dpi), as plain-language bar charts for a general audience, plus figures/figure_data/*.csv.
"""
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.ticker as mt
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "Data"; EV = DATA / "private" / "evaluation"
OUT = ROOT / "figures"; (OUT / "figure_data").mkdir(parents=True, exist_ok=True)
YEARS = range(2015, 2027)
FB, BB, GREY, INK = "#2a78d6", "#eb6834", "#9a9a9a", "#222222"   # colorblind-checked pair
TEAL, MUTE, NAVY, SUB = "#147D80", "#B9C3CB", "#203C55", "#586977"   # slide palette
MONEY = mt.FuncFormatter(lambda v, _: f"${v/1e6:g}M" if v >= 1e6 else f"${v/1e3:g}K")
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5, "legend.fontsize": 9.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "lines.linewidth": 1.4, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 300, "figure.dpi": 150})
ONE, TWO = 3.5, 7.0  # single / double column width, inches


def save(fig, name):
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight")
    plt.close(fig)


def panel(ax, letter):
    ax.text(-0.14, 1.04, letter, transform=ax.transAxes, fontweight="bold", fontsize=10, va="bottom")


# ---------------------------------------------------------------- roster trends
def roster_trends():
    fr = {y: pd.read_parquet(EV / f"football_rosters/cfb_rosters_{y}.parquet",
                             columns=["athlete_id", "team_id", "division", "games_rostered"]) for y in YEARS}
    fbs = set(fr[2025].loc[fr[2025].division == "fbs", "team_id"])   # FBS membership as of 2025
    fr = {y: f[f.team_id.isin(fbs) & (f.games_rostered > 1)].drop_duplicates("athlete_id").rename(columns={"athlete_id": "pid"})
          for y, f in fr.items()}
    d1 = set(pd.read_csv(DATA / "private/basketball/division_i_player_team_season_2026.csv", usecols=["team_id"]).team_id)
    bb = {}
    for y in YEARS:
        b = pd.read_parquet(EV / f"basketball_values/mbb_player_value_{y}.parquet")
        b["team_id"] = pd.to_numeric(b.team_id, errors="coerce")
        bb[y] = (b[b.team_id.isin(d1) & (b["min"] > 0)].sort_values("min")
                 .drop_duplicates("player_id", keep="last").rename(columns={"player_id": "pid"}))
    rows = []
    for sport, data in (("Football (FBS)", fr), ("Basketball (D-I)", bb)):
        for y in YEARS:
            cur, r = data[y], {"sport": sport, "season": y, "players": len(data[y])}
            if y - 1 in data:
                j = cur.merge(data[y - 1][["pid", "team_id"]], on="pid", suffixes=("", "_prev"))
                r["transfer_in_share"] = (j.team_id != j.team_id_prev).sum() / len(cur)
            if y >= 2019:   # four seasons of look-back from 2015
                hist = pd.concat([data[k][["pid"]] for k in YEARS if k < y]).pid.value_counts()
                r["fifth_plus_share"] = (cur.pid.map(hist).fillna(0) >= 4).mean()
            rows.append(r)
    t = pd.DataFrame(rows); t.to_csv(OUT / "figure_data/roster_trends.csv", index=False)
    return t


def fig_trend(t, col, name, ylabel, covid=False):
    """Grouped bars by season (plain-language, bar-first)."""
    t = t[t[col].notna()]; seasons = sorted(t.season.unique()); xs = np.arange(len(seasons)); w = 0.4
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    if covid:
        lo, hi = seasons.index(2021) - 0.5, seasons.index(2025) + 0.5
        ax.axvspan(lo, hi, color=GREY, alpha=0.12, lw=0)
        ax.text(hi - 0.08, 0.97, "COVID extra-year\nseasons", transform=ax.get_xaxis_transform(), ha="right", va="top", fontsize=8.5, color=SUB)
    for k, (sport, c) in enumerate((("Football (FBS)", FB), ("Basketball (D-I)", BB))):
        d = t[t.sport == sport].set_index("season")[col].reindex(seasons) * 100
        ax.bar(xs + (k - 0.5) * w, d.values, width=w, color=c, label=sport.split(" (")[0])
    nil = seasons.index(2022) - 0.5
    ax.axvline(nil, color=NAVY, ls=(0, (3, 2)), lw=1)
    ax.text(nil - 0.1, 0.97, "NIL begins\n(July 2021)", transform=ax.get_xaxis_transform(), ha="right", va="top", fontsize=8.5, color=NAVY)
    ax.set_xticks(xs); ax.set_xticklabels([str(y) for y in seasons], rotation=45 if len(seasons) > 9 else 0)
    ax.set_ylabel(ylabel); ax.set_xlabel("Season")
    ax.yaxis.set_major_formatter(mt.PercentFormatter(decimals=0)); ax.set_ylim(0, (t[col].max() * 100) * 1.3)
    ax.yaxis.set_major_locator(mt.MaxNLocator(5, steps=[1, 2, 5, 10]))
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    save(fig, name)


# ---------------------------------------------------------------- football NIL sample
def nil_sample():
    m = pd.read_csv(DATA / "football_modeling_data.csv")
    m["log_v"], m["log_f"] = np.log(m.Valuation), np.log(m["Instagram Followers"])
    m["stars"], m["ppa"] = m["Star Rating"], m.PPA_Per_Play.where(m.PPA_Per_Play != 0)
    m["class_year"] = m.Grade.map({"Freshman": 1, "Sophomore": 2, "Junior": 3, "Senior": 4})
    return m


def _median_bars(groups, labels, title_note, xlabel, name, color=TEAL, figsize=(6.4, 3.0)):
    meds = [g.median() for g in groups]; xs = np.arange(len(groups))
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(xs, meds, width=0.6, color=color)
    for x, v, g in zip(xs, meds, groups):
        ax.text(x, v, f"${v/1e3:,.0f}K", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=NAVY)
    ax.set_xticks(xs); ax.set_xticklabels([f"{l}\n({len(g)} players)" for l, g in zip(labels, groups)])
    ax.yaxis.set_major_formatter(MONEY); ax.set_ylim(0, max(meds) * 1.22)
    ax.set_ylabel("Typical (median) NIL value"); ax.set_xlabel(xlabel)
    ax.text(0.0, 1.02, title_note, transform=ax.transAxes, fontsize=9, color=SUB, va="bottom")
    save(fig, name); return meds


def fig_followers(m):
    """Fig 3: follower effect (% more value for twice the followers) in each version of the model."""
    specs = [
        ("Partner’s model", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m, "HC1"),
        ("Partner’s model\n+ star rating", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + stars + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m, "HC3"),
        ("Followers\nonly", "Log_Valuation ~ Log_Instagram", m, "HC3"),
        ("Without the\n1M-follower player", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + stars + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m[m["Instagram Followers"] < 1e6], "HC3"),
        ("Without the 25\ntop-valued players", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + stars + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m[m["Valuation Tier"] != "Top_25"], "HC3"),
    ]
    rows = []
    for lab, f, d, cov in specs:
        r = smf.ols(f, d).fit(cov_type=cov); lo, hi = r.conf_int().loc["Log_Instagram"]
        rows.append(dict(model=lab.replace("\n", " "), n=int(r.nobs), beta=r.params["Log_Instagram"], ci_low=lo, ci_high=hi, p=r.pvalues["Log_Instagram"]))
    s = pd.DataFrame(rows); s.to_csv(OUT / "figure_data/follower_elasticity.csv", index=False)
    pct = lambda b: 100 * (2 ** b - 1)
    fig, ax = plt.subplots(figsize=(7.4, 3.0)); xs = np.arange(len(s))
    v = pct(s.beta); lo = pct(s.ci_low); hi = pct(s.ci_high)
    ax.bar(xs, v, width=0.6, color=[TEAL if p < 0.05 else MUTE for p in s.p])
    ax.errorbar(xs, v, yerr=[v - lo, hi - v], fmt="none", ecolor=NAVY, elinewidth=1, capsize=3)
    for x, val, p, h in zip(xs, v, s.p, hi):
        ax.text(x, h + 1, f"+{val:.0f}%", ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=TEAL if p < 0.05 else NAVY)
    ax.axhline(0, color=NAVY, lw=0.8)
    ax.set_xticks(xs); ax.set_xticklabels([l for l, *_ in specs], fontsize=9)
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda y, _: f"{y:+.0f}%" if y else "0%")); ax.set_ylim(-5, hi.max() + 9)
    ax.set_ylabel("Higher NIL value for\ntwice the followers")
    ax.text(0.0, 1.02, "Lines show the 95% range; grey = not statistically significant", transform=ax.transAxes, fontsize=9, color=SUB, va="bottom")
    save(fig, "fig3_followers_vs_valuation")


def fig_stars(m):
    """Fig 4: typical NIL value by recruiting star rating."""
    lev = [3, 4, 5]; data = [m.loc[m.stars == s, "Valuation"] for s in lev]
    kw = stats.kruskal(*data).pvalue
    _median_bars(data, [f"{s}-star" for s in lev], f"Groups differ (p = {kw:.3f}), but value does not rise with stars", "High-school recruiting rating",
                 "fig4_recruiting_stars", color=[MUTE, MUTE, MUTE], figsize=(5.4, 3.0))
    rows = []
    for lab, c in {"Instagram followers": "log_f", "PPA per play (zeros as missing)": "ppa", "Class year": "class_year", "Recruiting stars": "stars"}.items():
        d = m[["log_v", c]].dropna(); rho, p = stats.spearmanr(d.log_v, d[c]); rows.append(dict(predictor=lab, n=len(d), rho=rho, p=p))
    pd.DataFrame(rows).to_csv(OUT / "figure_data/spearman_with_valuation.csv", index=False)
    base = "Log_Valuation ~ Log_Instagram + PPA_Per_Play + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position"
    a, b = smf.ols(base, m).fit(cov_type="HC3"), smf.ols(base + " + stars", m).fit(cov_type="HC3")
    pd.DataFrame({"partner_model": a.params, "partner_p": a.pvalues, "with_stars_main_effect": b.params, "with_stars_p": b.pvalues}).round(4)\
        .to_csv(OUT / "figure_data/stars_main_effect_models.csv")


def fig_follower_quartiles(m):
    """Fig 5: typical NIL value by Instagram follower group (four equal-size groups)."""
    q = pd.qcut(m["Instagram Followers"], 4, labels=False)
    data = [m.loc[q == k, "Valuation"] for k in range(4)]
    rng_lab = [(m.loc[q == k, "Instagram Followers"].min(), m.loc[q == k, "Instagram Followers"].max()) for k in range(4)]
    fmt = lambda v: f"{v/1e6:g}M" if v >= 1e6 else f"{v/1e3:.1f}K".replace(".0K", "K")
    kw = stats.kruskal(*data).pvalue
    names = ["Fewest", "Fewer", "More", "Most"]
    meds = _median_bars(data, [f"{n}\n{fmt(lo)}–{fmt(hi)}" for n, (lo, hi) in zip(names, rng_lab)],
                        "Statistically significant difference (p < 0.001)" if kw < 0.001 else f"p = {kw:.3f}",
                        "Instagram followers (four equal-size groups)", "fig5_follower_quartiles", figsize=(6.4, 3.0))
    pd.DataFrame({"group": names, "followers_min": [a for a, _ in rng_lab], "followers_max": [b for _, b in rng_lab],
                  "n": [len(d) for d in data], "median_valuation": meds, "kruskal_p_all_groups": kw})\
        .to_csv(OUT / "figure_data/valuation_by_follower_quartile.csv", index=False)


# Chip centres (inches from the slide's left edge) of the model-explainer slide, so each bar
# sits directly above its piece of the equation when the PNG is placed full-width on a 13.33 in slide.
SLIDE_W, CHIP_X = 13.333, {"Followers": 3.14, "Stars": 4.735, "Freshman": 6.18, "Stars × Freshman": 7.975,
                          "Position group": 9.995, "Noise": 11.715}


def fig_feature_effects(m):
    """Fig 6: each term of the position-groups model (HC3) as % change in valuation, 95% CI,
    drawn as vertical bars aligned to the model-explainer slide (transparent background)."""
    def pg(p):
        p = str(p).upper()
        if p == "QB": return "Quarterback"
        if p in ["WR", "RB", "FB", "TE"]: return "Skill offense"
        if p in ["OL", "OT", "OG", "C", "OC", "IOL"]: return "Offensive line"
        return "Defense"
    d = m.copy(); d["PG"] = d.Position.map(pg); d["Log_Valuation"] = np.log(d.Valuation)
    d["x"] = np.log1p(d["Instagram Followers"]); d["Stars_C"] = d["Star Rating"] - d["Star Rating"].mean()
    r = smf.ols("Log_Valuation ~ x + Stars_C * Freshman_Flag + C(PG, Treatment('Defense'))", d).fit(cov_type="HC3")
    P = "C(PG, Treatment('Defense'))[T.{}]"
    terms = [  # label, model term, scale, chip, offset within chip, short label
        ("Twice the Instagram followers", "x", np.log(2), "Followers", 0, ""),
        ("+1 recruiting star (non-freshmen)", "Stars_C", 1, "Stars", 0, ""),
        ("Freshman (at average stars)", "Freshman_Flag", 1, "Freshman", 0, ""),
        ("Extra per star for freshmen", "Stars_C:Freshman_Flag", 1, "Stars × Freshman", 0, ""),
        ("Quarterback (vs defense)", P.format("Quarterback"), 1, "Position group", -0.45, "QB"),
        ("Offensive line (vs defense)", P.format("Offensive line"), 1, "Position group", 0, "Line"),
        ("Skill offense (vs defense)", P.format("Skill offense"), 1, "Position group", 0.45, "Skill"),
    ]
    pct = lambda v, sc: 100 * (np.exp(v * sc) - 1)
    rows = []
    for lab, t, sc, chip, off, short in terms:
        b, se, p = r.params[t], r.bse[t], r.pvalues[t]
        rows.append(dict(feature=lab, pct=pct(b, sc), ci_low=pct(b - 1.96 * se, sc), ci_high=pct(b + 1.96 * se, sc), p=p,
                         log_coef=b, scale=sc, x=CHIP_X[chip] + off, short=short, width=0.55 if not short else 0.36))
    e = pd.DataFrame(rows); e.drop(columns=["x", "short", "width"]).to_csv(OUT / "figure_data/feature_effects_position_groups_hc3.csv", index=False)

    TEAL, MUTE, LO, HI, TOP = "#147D80", "#B9C3CB", -60, 140, 168
    with plt.rc_context({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"]}):
        fig = plt.figure(figsize=(SLIDE_W, 2.0)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
        ax.set_xlim(0, SLIDE_W); ax.set_ylim(LO - 30, TOP + 22)
        for v in (-50, 0, 50, 100):
            ax.plot([2.3, 12.45], [v, v], color="#203C55" if v == 0 else "#D9E0E5", lw=0.9 if v == 0 else 0.6, zorder=0)
            ax.text(2.22, v, f"{v:+d}%" if v else "0%", ha="right", va="center", fontsize=9, color="#586977")
        ax.text(1.395, 45, "% change in\nestimated\nNIL value", ha="center", va="center", fontsize=10, color="#203C55", fontweight="bold")
        for _, q in e.iterrows():
            col = TEAL if q.p < 0.05 else MUTE
            ax.bar(q.x, q.pct, width=q.width, color=col, zorder=2)
            hi = min(q.ci_high, HI)
            ax.plot([q.x, q.x], [max(q.ci_low, LO), hi], color="#203C55", lw=1, zorder=3)
            for yv in (max(q.ci_low, LO), hi) if q.ci_high <= HI else (max(q.ci_low, LO),):
                ax.plot([q.x - 0.06, q.x + 0.06], [yv, yv], color="#203C55", lw=1, zorder=3)
            if q.ci_high > HI:
                ax.annotate("", (q.x, HI + 6), (q.x, HI - 4), arrowprops=dict(arrowstyle="-|>", color="#203C55", lw=1), zorder=3)
                ax.text(q.x + 0.1, HI - 2, f"to +{q.ci_high:.0f}%", fontsize=7.5, color="#586977", va="center")
            ptxt = "p < 0.001" if q.p < 0.001 else f"p = {q.p:.2f}" if q.p >= 0.1 else f"p = {q.p:.3f}"
            fs = 8.5 if q.short else 10.5
            ax.text(q.x, TOP, f"{q.pct:+.0f}%", ha="center", va="bottom", fontsize=fs + 1.5, fontweight="bold", color=TEAL if q.p < 0.05 else "#203C55")
            ax.text(q.x, TOP - 3, ptxt, ha="center", va="top", fontsize=fs - 1.5, color="#586977")
            if q.short: ax.text(q.x, LO - 4, q.short, ha="center", va="top", fontsize=8.5, color="#203C55")
        ax.text(CHIP_X["Noise"], 45, f"R² = {r.rsquared:.2f}\n{100 * (1 - r.rsquared):.0f}% of the variation\nis left unexplained",
                ha="center", va="center", fontsize=9, color="#586977")
        for ext in ("pdf", "png"):
            fig.savefig(OUT / f"fig6_feature_effects.{ext}", transparent=True, dpi=300)
        plt.close(fig)
    return e


if __name__ == "__main__":
    t = roster_trends()
    fig_trend(t, "transfer_in_share", "fig1_transfer_share", "Players who transferred in\n(% of roster)")
    fig_trend(t, "fifth_plus_share", "fig2_fifth_year_share", "Players in their 5th+ college season\n(% of roster)", covid=True)
    m = nil_sample(); fig_followers(m); fig_stars(m); fig_follower_quartiles(m); fig_feature_effects(m)
    print("Wrote", sorted(p.name for p in OUT.glob("fig*")))
