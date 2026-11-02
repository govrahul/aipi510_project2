"""Manuscript figures for the NIL project. Run from the repository root:

    python scripts/make_manuscript_figures.py

Reads (read-only):
  Data/football_modeling_data.csv
  Data/private/evaluation/football_rosters/cfb_rosters_2015..2026.parquet
  Data/private/evaluation/basketball_values/mbb_player_value_2015..2026.parquet
  Data/private/basketball/division_i_player_team_season_2026.csv
Writes figures/fig1..fig4 as PDF (vector) and PNG (300 dpi), plus figures/figure_data/*.csv.
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
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
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
    fig, ax = plt.subplots(figsize=(ONE, 2.5))
    for sport, c, mk in (("Basketball (D-I)", BB, "s"), ("Football (FBS)", FB, "o")):
        d = t[(t.sport == sport) & t[col].notna()]
        ax.plot(d.season, d[col] * 100, color=c, marker=mk, ms=3.5, label=sport)
    if covid:
        ax.axvspan(2020.5, 2025.5, color=GREY, alpha=0.12, lw=0); ax.set_ylim(0, 17)
        ax.text(2023, 16.6, "COVID extra-year cohorts on rosters", ha="center", va="top", fontsize=6.5, color=INK)
    ax.axvline(2021.5, color=INK, ls=(0, (2, 2)), lw=0.7)
    ax.text(2021.4, 5.5 if covid else ax.get_ylim()[1] * 0.97, "NIL\n(Jul 2021)", ha="right", va="top", fontsize=6.5, color=INK)
    ax.set_xlim(2015.5 if not covid else 2018.5, 2026.5); ax.xaxis.set_major_locator(mt.MultipleLocator(2 if not covid else 1))
    if covid: ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel(ylabel); ax.set_xlabel("Season (basketball: year season ends)")
    ax.yaxis.set_major_formatter(mt.PercentFormatter(decimals=0)); ax.set_ylim(bottom=0)
    ax.legend(frameon=False, loc=(0.42, 0.04) if covid else "center left")
    save(fig, name)


# ---------------------------------------------------------------- football NIL sample
def nil_sample():
    m = pd.read_csv(DATA / "football_modeling_data.csv")
    m["log_v"], m["log_f"] = np.log(m.Valuation), np.log(m["Instagram Followers"])
    m["stars"], m["ppa"] = m["Star Rating"], m.PPA_Per_Play.where(m.PPA_Per_Play != 0)
    m["class_year"] = m.Grade.map({"Freshman": 1, "Sophomore": 2, "Junior": 3, "Senior": 4})
    return m


def fig_followers(m):
    specs = [
        ("Partner model (HC1)", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m, "HC1"),
        ("+ stars main effect", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + stars + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m, "HC3"),
        ("Followers only", "Log_Valuation ~ Log_Instagram", m, "HC3"),
        ("Excl. 1M-follower outlier", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + stars + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m[m["Instagram Followers"] < 1e6], "HC3"),
        ("Excl. top valuation tier", "Log_Valuation ~ Log_Instagram + PPA_Per_Play + stars + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position", m[m["Valuation Tier"] != "Top_25"], "HC3"),
    ]
    rows = []
    for lab, f, d, cov in specs:
        r = smf.ols(f, d).fit(cov_type=cov); lo, hi = r.conf_int().loc["Log_Instagram"]
        rows.append(dict(model=lab, n=int(r.nobs), beta=r.params["Log_Instagram"], ci_low=lo, ci_high=hi, p=r.pvalues["Log_Instagram"]))
    s = pd.DataFrame(rows); s.to_csv(OUT / "figure_data/follower_elasticity.csv", index=False)

    fig, ax = plt.subplots(1, 2, figsize=(TWO, 2.8), gridspec_kw={"width_ratios": [1, 1.15]})
    top = m["Valuation Tier"] == "Top_25"
    ax[0].scatter(m.loc[~top, "Instagram Followers"], m.loc[~top, "Valuation"], s=12, facecolor="white", edgecolor=FB, lw=0.8, label="Middle/bottom tiers (n=75)")
    ax[0].scatter(m.loc[top, "Instagram Followers"], m.loc[top, "Valuation"], s=12, color=BB, lw=0, label="Top tier (n=25)")
    xs = np.linspace(m.log_f.min(), m.log_f.max(), 50)
    for d, c, ls, lab in ((m, INK, "-", "Fit, all players"), (m[~top], FB, "--", "Fit, excl. top tier")):
        b = np.polyfit(d.log_f, d.log_v, 1); ax[0].plot(np.exp(xs), np.exp(np.polyval(b, xs)), color=c, ls=ls, lw=1, label=lab)
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v/1e6:g}M" if v >= 1e6 else f"${v/1e3:g}K"))
    ax[0].yaxis.set_minor_formatter(mt.NullFormatter()); ax[0].set_yticks([3.5e5, 5e5, 1e6, 2e6, 5e6])
    ax[0].xaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v/1e6:g}M" if v >= 1e6 else f"{v/1e3:g}K"))
    ax[0].set_xlabel("Instagram followers (log scale)"); ax[0].set_ylabel("NIL valuation (log scale)")
    ax[0].set_ylim(3e5, 3.2e7); ax[0].legend(frameon=False, loc="upper left", fontsize=6.3, handletextpad=0.4, borderaxespad=0.2); panel(ax[0], "a")
    y = np.arange(len(s))[::-1]
    ax[1].errorbar(s.beta, y, xerr=[s.beta - s.ci_low, s.ci_high - s.beta], fmt="o", ms=3.5, color=INK, ecolor=INK, elinewidth=0.9, capsize=2)
    ax[1].axvline(0, color=GREY, lw=0.7)
    ax[1].set_yticks(y); ax[1].set_yticklabels([f"{a} (n={n})" for a, n in zip(s.model, s.n)])
    for yy, (b, p) in zip(y, zip(s.beta, s.p)): ax[1].text(0.52, yy, f"{b:.2f}" + ("*" if p < 0.05 else ""), va="center", fontsize=7)
    ax[1].set_xlim(-0.1, 0.58); ax[1].set_xlabel("Elasticity of valuation w.r.t. followers (95% CI)"); panel(ax[1], "b")
    save(fig, "fig3_followers_vs_valuation")


def fig_stars(m):
    rng = np.random.default_rng(510)
    preds = {"Instagram followers": "log_f", "PPA per play\n(zeros as missing)": "ppa", "Class year": "class_year", "Recruiting stars": "stars"}
    rows = []
    for lab, c in preds.items():
        d = m[["log_v", c]].dropna(); rho = stats.spearmanr(d.log_v, d[c])[0]
        boot = [stats.spearmanr(*d.sample(len(d), replace=True, random_state=int(rng.integers(1e9))).T.values)[0] for _ in range(2000)]
        rows.append(dict(predictor=lab.replace("\n", " "), n=len(d), rho=rho, ci_low=np.nanpercentile(boot, 2.5), ci_high=np.nanpercentile(boot, 97.5)))
    r = pd.DataFrame(rows); r.to_csv(OUT / "figure_data/spearman_with_valuation.csv", index=False)
    fig, ax = plt.subplots(1, 2, figsize=(TWO, 2.6), gridspec_kw={"width_ratios": [1, 1.1]})
    lev = [3, 4, 5]; data = [m.loc[m.stars == s, "Valuation"] for s in lev]
    ax[0].boxplot(data, positions=range(3), widths=0.5, showfliers=False, medianprops=dict(color=BB, lw=1.4),
                  boxprops=dict(lw=0.7), whiskerprops=dict(lw=0.7), capprops=dict(lw=0.7))
    for k, d in enumerate(data):
        ax[0].scatter(rng.normal(k, 0.07, len(d)), d, s=7, color=FB, alpha=0.7, lw=0, zorder=3)
    ax[0].set_xticks(range(3)); ax[0].set_xticklabels([f"{s}-star\n(n={len(d)})" for s, d in zip(lev, data)])
    ax[0].set_yscale("log"); ax[0].yaxis.set_minor_formatter(mt.NullFormatter()); ax[0].set_yticks([3.5e5, 5e5, 1e6, 2e6, 5e6])
    ax[0].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v/1e6:g}M" if v >= 1e6 else f"${v/1e3:g}K"))
    ax[0].set_ylabel("NIL valuation (log scale)"); ax[0].set_xlabel("High-school recruiting stars"); panel(ax[0], "a")
    y = np.arange(len(r))[::-1]
    ax[1].barh(y, r.rho, color=[FB, FB, FB, BB], height=0.55)
    ax[1].errorbar(r.rho, y, xerr=[r.rho - r.ci_low, r.ci_high - r.rho], fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
    ax[1].axvline(0, color=GREY, lw=0.7); ax[1].set_yticks(y); ax[1].set_yticklabels([f"{p} (n={n})" for p, n in zip(r.predictor, r.n)])
    ax[1].set_xlabel("Spearman ρ with NIL valuation (95% bootstrap CI)"); ax[1].set_xlim(-0.3, 0.8); panel(ax[1], "b")
    save(fig, "fig4_recruiting_stars")
    # stars main-effect comparison table
    base = "Log_Valuation ~ Log_Instagram + PPA_Per_Play + Freshman_Flag + Freshman_X_Stars + Power_4_Dummy + Premium_Position"
    a, b = smf.ols(base, m).fit(cov_type="HC3"), smf.ols(base + " + stars", m).fit(cov_type="HC3")
    pd.DataFrame({"partner_model": a.params, "partner_p": a.pvalues, "with_stars_main_effect": b.params, "with_stars_p": b.pvalues}).round(4)\
        .to_csv(OUT / "figure_data/stars_main_effect_models.csv")


if __name__ == "__main__":
    t = roster_trends()
    fig_trend(t, "transfer_in_share", "fig1_transfer_share", "Roster share from another team")
    fig_trend(t, "fifth_plus_share", "fig2_fifth_year_share", "Roster share in 5th+ college season", covid=True)
    m = nil_sample(); fig_followers(m); fig_stars(m)
    print("Wrote", sorted(p.name for p in OUT.glob("fig*")))
