#!/usr/bin/env python3
"""Generate every quantitative figure referenced by the CQSS-SPI manuscript.

All plotted quantities are derived from the manuscript equations through
``compute_continuous_metrics`` and ``build_counterfactual_table``.  No figure
contains a hard-coded publication constant, so a figure can never drift away
from Tables 7-9 the way the pre-correction figure set did.

Each figure has a ``build_*`` function that returns the Matplotlib figure
without writing it to disk.  ``tests/test_reproduction.py`` uses those builders
to read back the values actually drawn on the axes and compare them with the
published tables.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cqssspi-matplotlib"))

# Matplotlib writes a creation timestamp into PDF/EPS output.  Pinning
# SOURCE_DATE_EPOCH makes repeated exports byte-identical, so continuous
# integration can diff the committed figures against a fresh rebuild.
# Export a different value before running to override.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1700000000")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

from compute_qssspi import (
    DEFAULT_DATA,
    DISPLAY_DECIMALS,
    EPSILON,
    LAMBDA_Q,
    LAMBDA_S,
    compute_continuous_metrics,
    load_data,
)
from counterfactual_analysis import ABLATED_SCENARIO, OBSERVED_SCENARIO, build_counterfactual_table

# Manuscript figure palette (Matplotlib tab10 for series, darker fills for bars).
COLORS = {
    "raw": "#1f77b4",
    "quality": "#ff7f0e",
    "full": "#d62728",
    "observed": "#c0392b",
    "ablated": "#c0392b",
    "scenario": "#2e8b57",
    "threshold": "#333333",
    "grid": "#c9c9c9",
    "ink": "#1a1a1a",
}

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.labelsize": 9.5,
        "axes.edgecolor": "#4d4d4d",
        "axes.linewidth": 0.8,
        "xtick.color": COLORS["ink"],
        "ytick.color": COLORS["ink"],
        "text.color": COLORS["ink"],
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    }
)


def _style_axis(ax: plt.Axes, axis: str = "both") -> None:
    ax.grid(axis=axis, color=COLORS["grid"], linewidth=0.6)
    ax.set_axisbelow(True)


def _save(fig: plt.Figure, output_dir: Path, stem: str, formats: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for extension in formats:
        path = output_dir / f"{stem}.{extension}"
        fig.savefig(path, dpi=300)
        if path.stat().st_size == 0:
            raise RuntimeError(f"Figure export produced an empty file: {path}")
        paths.append(path)
    plt.close(fig)
    return paths


def _bar_labels(ax: plt.Axes, bars, values: np.ndarray) -> None:
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.0025,
            f"{value:.{DISPLAY_DECIMALS}f}",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )


def _scenario_labels(names: pd.Series) -> list[str]:
    mapping = {
        OBSERVED_SCENARIO: "Observed\nQSSPI",
        ABLATED_SCENARIO: "No security\ngating increase\n(ablated)",
        "Stronger gating (scenario)": "Stronger\ngating",
        "Selective AI restriction (scenario)": "Selective AI\nrestriction",
        "Lower compression (scenario)": "Lower\ncompression",
    }
    return [mapping[str(name)] for name in names]


# --------------------------------------------------------------------------
# Figure builders (return the figure; no disk writes)
# --------------------------------------------------------------------------
def build_time_series(metrics: pd.DataFrame) -> plt.Figure:
    """Manuscript Figure 2: raw SPI against the debt-adjusted QSSPI."""
    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.plot(
        metrics["Sprint"], metrics["SPI_s"], marker="o", markersize=5.5,
        linewidth=1.6, color=COLORS["raw"], label=r"$SPI_s$",
    )
    ax.plot(
        metrics["Sprint"], metrics["QSSPI_s"], marker="s", markersize=5.0,
        linewidth=1.6, color=COLORS["quality"], label=r"$QSSPI_s$",
    )
    ax.axhline(1.0, color=COLORS["raw"], linestyle="--", linewidth=0.9)
    ax.set_title("Time Series of Raw SPI and Quality-/Security-Sensitive QSSPI")
    ax.set(xlabel="Sprint", ylabel="Schedule Performance Index", xticks=metrics["Sprint"])
    ax.set_ylim(0.885, 1.145)
    ax.legend(loc="upper right", frameon=True, framealpha=1.0, edgecolor="#b0b0b0")
    _style_axis(ax)
    fig.tight_layout()
    return fig


def build_scatter(metrics: pd.DataFrame) -> plt.Figure:
    """Manuscript Figure 3: AI assistance intensity against security-debt density."""
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    gating_levels = sorted(metrics["G_s"].unique())
    cmap = plt.get_cmap("viridis")
    handles: list[Line2D] = []
    for level in gating_levels:
        subset = metrics[metrics["G_s"] == level]
        color = cmap(float(level))
        ax.scatter(
            subset["A_s"], subset["d_s_s"], s=80, color=color,
            edgecolor="#333333", linewidth=0.7, zorder=3,
        )
        handles.append(
            Line2D([], [], marker="o", linestyle="none", markersize=7,
                   markerfacecolor=color, markeredgecolor="#333333", label=f"{level:g}")
        )
    for row in metrics.itertuples(index=False):
        ax.annotate(
            str(int(row.Sprint)), (row.A_s, row.d_s_s),
            xytext=(6, 4), textcoords="offset points", fontsize=8,
        )
    ax.set_title(r"AI Assistance Intensity vs. Security Debt Density (colored by $G_s$)")
    ax.set(xlabel=r"AI Assistance Intensity ($A_s$)", ylabel=r"Security Debt Density ($d^s_s$)")
    ax.set_xlim(0.12, 0.90)
    ax.set_ylim(0.0, 0.155)
    ax.legend(
        handles=handles, title=r"Gating Intensity $G_s$", loc="upper left",
        frameon=True, framealpha=1.0, edgecolor="#b0b0b0", fontsize=8,
    )
    _style_axis(ax)
    fig.tight_layout()
    return fig


def build_counterfactual(scenarios: pd.DataFrame) -> plt.Figure:
    """Manuscript Figure 4: Sprint 5 sensitivity scenarios (ablated bar omitted)."""
    shown = scenarios[scenarios["Scenario"] != ABLATED_SCENARIO].reset_index(drop=True)
    values = shown["CQSSPI_exact"].to_numpy(dtype=float)
    colors = [COLORS["observed"]] + [COLORS["scenario"]] * (len(shown) - 1)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    bars = ax.bar(_scenario_labels(shown["Scenario"]), values, color=colors, width=0.62)
    _bar_labels(ax, bars, values)
    ax.axhline(1.0, color=COLORS["threshold"], linestyle="--", linewidth=0.9,
               label="On-plan threshold")
    ax.set_title("Counterfactual CQSSPI under Alternative Interventions (Sprint 5)")
    ax.set_ylabel("CQSSPI (Sprint 5)")
    ax.set_ylim(0.90, 1.02)
    ax.legend(loc="upper right", frameon=True, framealpha=1.0, edgecolor="#b0b0b0")
    _style_axis(ax, axis="y")
    fig.tight_layout()
    return fig


def build_ablation_penalties(metrics: pd.DataFrame) -> plt.Figure:
    """Manuscript Figure 5: progressive effect of the quality and security penalties."""
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.plot(metrics["Sprint"], metrics["SPI_s"], marker="o", markersize=5.5,
            linewidth=1.6, color=COLORS["raw"], label="Raw SPI")
    ax.plot(metrics["Sprint"], metrics["QSSPI_q_s"], marker="s", markersize=5.0,
            linewidth=1.6, color=COLORS["quality"], label=r"Quality-only (SPI $\times$ QF)")
    ax.plot(metrics["Sprint"], metrics["QSSPI_s"], marker="^", markersize=5.5,
            linewidth=1.6, color=COLORS["full"],
            label=r"Full QSSPI (SPI $\times$ QF $\times$ SF)")
    ax.axhline(1.0, color=COLORS["threshold"], linestyle="--", linewidth=0.9,
               label="On-plan threshold")
    ax.set_title("Ablation Study: Progressive Effect of Quality and Security Penalties")
    ax.set(xlabel="Sprint", ylabel="Schedule Performance Index", xticks=metrics["Sprint"])
    ax.set_ylim(0.885, 1.15)
    # The caption states that the legend sits outside the plotting area.
    ax.legend(
        title="Metric Variant", loc="upper center", bbox_to_anchor=(0.5, -0.16),
        ncol=2, frameon=True, framealpha=1.0, edgecolor="#b0b0b0", fontsize=8.5,
    )
    _style_axis(ax)
    fig.tight_layout()
    return fig


def build_ablation_causal(scenarios: pd.DataFrame) -> plt.Figure:
    """Manuscript Figure 6: causal-layer ablation including the null intervention."""
    values = scenarios["CQSSPI_exact"].to_numpy(dtype=float)
    colors = [COLORS["observed"], COLORS["ablated"]] + [COLORS["scenario"]] * (len(scenarios) - 2)
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    bars = ax.bar(_scenario_labels(scenarios["Scenario"]), values, color=colors, width=0.62)
    _bar_labels(ax, bars, values)
    ax.axhline(1.0, color=COLORS["threshold"], linestyle="--", linewidth=0.9,
               label="On-plan threshold")
    ax.set_title("Ablation of Causal Layer: Counterfactual Gains from Governance Interventions")
    ax.set_ylabel("CQSSPI (Sprint 5)")
    ax.set_ylim(0.90, 1.04)
    ax.legend(loc="upper right", frameon=True, framealpha=1.0, edgecolor="#b0b0b0")
    _style_axis(ax, axis="y")
    fig.tight_layout()
    return fig


SCM_MERMAID_SOURCE = Path(__file__).resolve().parents[1] / "figures" / "scm_graph.mmd"


def parse_mermaid_scm(path: Path | None = None) -> tuple[tuple[tuple[str, str], ...], dict[str, list[int]]]:
    """Parse the Mermaid source of Figure 1.

    Returns the ordered edge list and the link indices each ``linkStyle`` rule
    targets, so the test suite can check the diagram against Equations 22-25 and
    confirm that every edge is styled exactly once.
    """
    import re

    text = (path or SCM_MERMAID_SOURCE).read_text(encoding="utf-8")
    # Drop the YAML front matter and any Mermaid comments.
    if text.lstrip().startswith("---"):
        text = text.split("---", 2)[-1]
    lines = [line.split("%%")[0] for line in text.splitlines()]

    def node_id(token: str) -> str:
        return re.split(r"[\[({\"]", token, maxsplit=1)[0].strip()

    def strip_labels(token: str) -> str:
        """Replace ``ID["some & label"]`` with ``ID``.

        Node labels legitimately contain ``&`` (for example ``&amp;``), so they
        must be removed before targets are split on the ``&`` chaining operator.
        """
        return re.sub(r"""\s*[\[({]\s*"[^"]*"\s*[\])}]|\s*[\[({][^\])}]*[\])}]""", "", token)

    edges: list[tuple[str, str]] = []
    link_styles: dict[str, list[int]] = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("linkStyle"):
            body = stripped[len("linkStyle"):].strip()
            indices, _, rule = body.partition(" ")
            link_styles[rule.strip()] = [int(i) for i in indices.split(",")]
            continue
        if "-->" not in stripped:
            continue
        source, _, targets = stripped.partition("-->")
        source_id = node_id(strip_labels(source))
        for target in strip_labels(targets).split("&"):
            edges.append((source_id, node_id(target)))
    return tuple(edges), link_styles


# Edge set of the hypothesized SCM.  This is the single source of truth for the
# Matplotlib rendering and is asserted against both the manuscript equations and
# the Mermaid source of Figure 1 in the test suite.
SCM_EDGES: tuple[tuple[str, str], ...] = (
    ("A", "TD"), ("A", "SD"), ("A", "EV"),
    ("C", "TD"), ("C", "SD"), ("C", "EV"),
    ("G", "SD"),
    ("R", "TD"), ("R", "SD"),
    ("X", "TD"), ("X", "SD"), ("X", "EV"),
    ("M", "TD"), ("M", "SD"), ("M", "EV"),
    ("T", "EV"),
    ("TD", "Q"), ("SD", "Q"), ("EV", "Q"), ("PV", "Q"),
)


def build_scm() -> plt.Figure:
    """Manuscript Figure 1: hypothesized SCM implied by Equations 23-25.

    The testing-intensity node ``T`` is included because Equations 21 and 25
    place ``T_s`` in the earned-value mechanism.
    """
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    positions = {
        "A": (0.085, 0.80), "C": (0.238, 0.80), "G": (0.391, 0.80), "R": (0.544, 0.80),
        "X": (0.697, 0.80), "M": (0.850, 0.80), "T": (0.960, 0.80),
        "TD": (0.215, 0.44), "SD": (0.455, 0.44), "EV": (0.695, 0.44), "PV": (0.910, 0.44),
        "Q": (0.500, 0.10),
    }
    labels = {
        "A": r"AI Assistance" "\n" r"$A_s$", "C": "Schedule\nCompression\n$C_s$",
        "G": "Security\nGating\n$G_s$", "R": "Review\nIntensity\n$R_s$",
        "X": "Experience\nMix\n$X_s$", "M": "Module\nCriticality\n$M_s$",
        "T": "Testing\nIntensity\n$T_s$",
        "TD": r"$\Delta$ Technical Debt" "\n" r"$\Delta TD_s$",
        "SD": r"$\Delta$ Security Debt" "\n" r"$\Delta SD_s$",
        "EV": "Earned Value\n$EV_s$", "PV": "Planned Value\n$PV_s$",
        "Q": "CQSSPI\nQuality- & Security-Sensitive SPI",
    }
    widths = {k: 0.125 for k in ("A", "C", "G", "R", "X", "M", "T")}
    widths.update({"TD": 0.20, "SD": 0.20, "EV": 0.17, "PV": 0.15, "Q": 0.34})
    heights = {k: 0.11 for k in positions}
    heights["Q"] = 0.10

    # Grouping panels
    for x0, y0, w, h, text in (
        (0.012, 0.725, 0.976, 0.155, "Exogenous & Governance Variables"),
        (0.100, 0.370, 0.700, 0.145, "Mediators"),
    ):
        ax.add_patch(
            FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.004,rounding_size=0.01",
                           facecolor="#fbfbfb", edgecolor="#cfcfcf", linewidth=0.8, zorder=0)
        )
        ax.text(x0 + w / 2, y0 + h - 0.012, text, ha="center", va="top",
                fontsize=7.5, color="#707070", zorder=1)

    face = {
        **{k: "#e8f1ff" for k in ("A", "C", "T")},
        "G": "#e5f6ec", "R": "#e5f6ec",
        "X": "#f2f4f7", "M": "#fff3db",
        "TD": "#fff3db", "SD": "#ffe9e6", "EV": "#e5f6ec",
        "PV": "#f2f4f7", "Q": "#eef2ff",
    }
    for key, (x, y) in positions.items():
        w, h = widths[key], heights[key]
        ax.add_patch(
            FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                           boxstyle="round,pad=0.006,rounding_size=0.012",
                           facecolor=face[key], edgecolor="#5b6570", linewidth=0.9, zorder=2)
        )
        ax.text(x, y, labels[key], ha="center", va="center",
                fontsize=7.2 if key != "Q" else 8.0,
                fontweight="bold" if key == "Q" else "normal", zorder=3)

    edge_color = {"A": "#1f77b4", "C": "#e07b39", "G": "#2e8b57", "R": "#2e8b57",
                  "X": "#1f77b4", "M": "#e07b39", "T": "#1f77b4",
                  "TD": "#c0392b", "SD": "#c0392b", "EV": "#2e8b57", "PV": "#6b7280"}
    for source, target in SCM_EDGES:
        ax.annotate(
            "", xy=positions[target], xytext=positions[source],
            arrowprops={"arrowstyle": "-|>", "color": edge_color[source],
                        "linewidth": 0.7, "alpha": 0.75,
                        "shrinkA": 26, "shrinkB": 26,
                        "connectionstyle": "arc3,rad=0.06"},
            zorder=1,
        )
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------
# Save wrappers
# --------------------------------------------------------------------------
def generate_all_figures(
    df: pd.DataFrame,
    output_dir: Path,
    lambda_q: float = LAMBDA_Q,
    lambda_s: float = LAMBDA_S,
    epsilon: float = EPSILON,
    formats: tuple[str, ...] = ("pdf", "eps"),
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = compute_continuous_metrics(df, lambda_q, lambda_s, epsilon)
    scenarios = build_counterfactual_table(df, lambda_q, lambda_s, epsilon)

    paths: list[Path] = []
    paths.extend(_save(build_scm(), output_dir, "scm_graph", formats))
    paths.extend(_save(build_time_series(metrics), output_dir, "time_series", formats))
    paths.extend(_save(build_scatter(metrics), output_dir, "scatter_ai_debt", formats))
    paths.extend(_save(build_counterfactual(scenarios), output_dir, "counterfactual_bar", formats))
    paths.extend(_save(build_ablation_penalties(metrics), output_dir, "ablation_penalties", formats))
    paths.extend(_save(build_ablation_causal(scenarios), output_dir, "ablation_causal", formats))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the CQSS-SPI manuscript figures.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "figures")
    parser.add_argument("--lambda-q", type=float, default=LAMBDA_Q)
    parser.add_argument("--lambda-s", type=float, default=LAMBDA_S)
    parser.add_argument("--epsilon", type=float, default=EPSILON)
    parser.add_argument("--formats", nargs="+", default=["pdf", "eps"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    paths = generate_all_figures(
        df, args.output_dir, args.lambda_q, args.lambda_s, args.epsilon, tuple(args.formats)
    )
    print("Generated manuscript figures:")
    for path in paths:
        print(f"- {path} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
