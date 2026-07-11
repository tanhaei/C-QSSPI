#!/usr/bin/env python3
"""Generate every quantitative figure referenced by the CQSS-SPI manuscript."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "cqssspi-matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

from compute_qssspi import (
    DEFAULT_DATA,
    EPSILON,
    LAMBDA_Q,
    LAMBDA_S,
    compute_continuous_metrics,
    load_data,
)
from counterfactual_analysis import build_counterfactual_table


COLORS = {
    "raw": "#3B82F6",
    "quality": "#F59E0B",
    "full": "#DC2626",
    "observed": "#B91C1C",
    "scenario": "#2E8B57",
    "grid": "#D7DEE8",
    "ink": "#182230",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "axes.edgecolor": "#667085",
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


def _style_axis(ax: plt.Axes) -> None:
    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _save(fig: plt.Figure, output_dir: Path, stem: str, formats: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for extension in formats:
        path = output_dir / f"{stem}.{extension}"
        fig.savefig(path, dpi=300)
        paths.append(path)
    plt.close(fig)
    return paths


def figure_time_series(metrics: pd.DataFrame, output_dir: Path, formats: tuple[str, ...]) -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(metrics["Sprint"], metrics["SPI_s"], marker="o", linewidth=2.0, color=COLORS["raw"], label="Raw SPI")
    ax.plot(metrics["Sprint"], metrics["QSSPI_s"], marker="s", linewidth=2.0, color=COLORS["full"], label="QSSPI")
    ax.axhline(1.0, color="#667085", linestyle="--", linewidth=1.0, label="On-plan threshold")
    ax.set(xlabel="Sprint", ylabel="Index value", xticks=metrics["Sprint"])
    ax.set_ylim(0.87, 1.15)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    _style_axis(ax)
    fig.tight_layout()
    return _save(fig, output_dir, "time_series", formats)


def figure_scatter(metrics: pd.DataFrame, output_dir: Path, formats: tuple[str, ...]) -> list[Path]:
    fig, ax = plt.subplots(figsize=(6.8, 4.1))
    scatter = ax.scatter(
        metrics["A_s"],
        metrics["d_s_s"],
        c=metrics["G_s"],
        cmap="viridis",
        vmin=0,
        vmax=1,
        s=65,
        edgecolor="white",
        linewidth=0.8,
    )
    for row in metrics.itertuples(index=False):
        ax.annotate(str(int(row.Sprint)), (row.A_s, row.d_s_s), xytext=(4, 4), textcoords="offset points", fontsize=8)
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    colorbar.set_label("Security-gating intensity (G_s)")
    ax.set(xlabel="AI assistance intensity (A_s)", ylabel="Security-debt density (d_s)")
    ax.set_xlim(0.12, 0.88)
    ax.set_ylim(bottom=0)
    _style_axis(ax)
    fig.tight_layout()
    return _save(fig, output_dir, "scatter_ai_debt", formats)


def _short_scenario_labels(names: pd.Series) -> list[str]:
    mapping = {
        "Observed QSSPI_5": "Observed",
        "No security-gating increase (ablated)": "No gating\nincrease",
        "Stronger gating (scenario)": "Stronger\ngating",
        "Selective AI restriction (scenario)": "Selective AI\nrestriction",
        "Lower compression (scenario)": "Lower\ncompression",
    }
    return [mapping[str(name)] for name in names]


def _bar_values(ax: plt.Axes, bars: list, values: np.ndarray) -> None:
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.002, f"{value:.3f}", ha="center", va="bottom", fontsize=8)


def figure_counterfactual(scenarios: pd.DataFrame, output_dir: Path, formats: tuple[str, ...]) -> list[Path]:
    shown = scenarios[scenarios["Scenario"] != "No security-gating increase (ablated)"].reset_index(drop=True)
    values = shown["CQSSPI_exact"].to_numpy(dtype=float)
    colors = [COLORS["observed"]] + [COLORS["scenario"]] * (len(shown) - 1)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    bars = ax.bar(_short_scenario_labels(shown["Scenario"]), values, color=colors, width=0.65)
    _bar_values(ax, bars, values)
    ax.axhline(1.0, color="#667085", linestyle="--", linewidth=1.0, label="On-plan threshold")
    ax.set_ylabel("CQSSPI value")
    ax.set_ylim(0.92, 1.01)
    ax.legend(frameon=False, loc="upper left")
    _style_axis(ax)
    fig.tight_layout()
    return _save(fig, output_dir, "counterfactual_bar", formats)


def figure_ablation_penalties(metrics: pd.DataFrame, output_dir: Path, formats: tuple[str, ...]) -> list[Path]:
    fig, ax = plt.subplots(figsize=(7.4, 4.1))
    ax.plot(metrics["Sprint"], metrics["SPI_s"], marker="o", linewidth=2, color=COLORS["raw"], label="Raw SPI")
    ax.plot(
        metrics["Sprint"],
        metrics["QSSPI_q_s"],
        marker="^",
        linewidth=2,
        color=COLORS["quality"],
        label="Quality-only (SPI x QF)",
    )
    ax.plot(
        metrics["Sprint"],
        metrics["QSSPI_s"],
        marker="s",
        linewidth=2,
        color=COLORS["full"],
        label="Full QSSPI (SPI x QF x SF)",
    )
    ax.axhline(1.0, color="#667085", linestyle="--", linewidth=1.0, label="On-plan threshold")
    ax.set(xlabel="Sprint", ylabel="Index value", xticks=metrics["Sprint"])
    ax.set_ylim(0.87, 1.15)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    _style_axis(ax)
    fig.tight_layout()
    return _save(fig, output_dir, "ablation_penalties", formats)


def figure_ablation_causal(scenarios: pd.DataFrame, output_dir: Path, formats: tuple[str, ...]) -> list[Path]:
    values = scenarios["CQSSPI_exact"].to_numpy(dtype=float)
    colors = [COLORS["observed"], "#9CA3AF"] + [COLORS["scenario"]] * 3
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    bars = ax.bar(_short_scenario_labels(scenarios["Scenario"]), values, color=colors, width=0.64)
    _bar_values(ax, bars, values)
    ax.axhline(1.0, color="#667085", linestyle="--", linewidth=1.0)
    ax.set_ylabel("CQSSPI value")
    ax.set_ylim(0.92, 1.01)
    _style_axis(ax)
    fig.tight_layout()
    return _save(fig, output_dir, "ablation_causal", formats)


def _draw_node(ax: plt.Axes, xy: tuple[float, float], label: str, color: str, width: float = 0.12) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x - width / 2, y - 0.035),
        width,
        0.07,
        boxstyle="round,pad=0.008,rounding_size=0.012",
        facecolor=color,
        edgecolor="#52606D",
        linewidth=0.8,
    )
    ax.add_patch(patch)
    ax.text(x, y, label, ha="center", va="center", fontsize=8)


def figure_scm(output_dir: Path) -> list[Path]:
    """Draw the paper's hypothesized SCM; this is structural, not fitted."""
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    positions = {
        "A": (0.08, 0.86),
        "C": (0.22, 0.86),
        "G": (0.36, 0.86),
        "R": (0.50, 0.86),
        "X": (0.64, 0.86),
        "M": (0.78, 0.86),
        "T": (0.92, 0.86),
        "TD": (0.25, 0.48),
        "SD": (0.50, 0.48),
        "EV": (0.75, 0.48),
        "PV": (0.91, 0.48),
        "Q": (0.58, 0.14),
    }
    labels = {
        "A": "AI use (A)",
        "C": "Compression (C)",
        "G": "Gating (G)",
        "R": "Review (R)",
        "X": "Experience (X)",
        "M": "Criticality (M)",
        "T": "Testing (T)",
        "TD": "Technical debt",
        "SD": "Security debt",
        "EV": "Earned value",
        "PV": "Planned value",
        "Q": "QSSPI",
    }
    for key in ("A", "C", "G", "R", "X", "M", "T"):
        _draw_node(ax, positions[key], labels[key], "#E8F1FF", width=0.115)
    for key in ("TD", "SD", "EV"):
        _draw_node(ax, positions[key], labels[key], "#FFF3DB", width=0.16)
    _draw_node(ax, positions["PV"], labels["PV"], "#F2F4F7", width=0.14)
    _draw_node(ax, positions["Q"], labels["Q"], "#E5F6EC", width=0.16)

    edges = [
        ("A", "TD"), ("A", "SD"), ("A", "EV"),
        ("C", "TD"), ("C", "SD"), ("C", "EV"),
        ("G", "SD"),
        ("R", "TD"), ("R", "SD"),
        ("X", "TD"), ("X", "SD"), ("X", "EV"),
        ("M", "TD"), ("M", "SD"), ("M", "EV"),
        ("T", "EV"),
        ("TD", "Q"), ("SD", "Q"), ("EV", "Q"), ("PV", "Q"),
    ]
    for source, target in edges:
        ax.annotate(
            "",
            xy=positions[target],
            xytext=positions[source],
            arrowprops={"arrowstyle": "->", "color": "#7B8794", "linewidth": 0.65, "shrinkA": 20, "shrinkB": 22},
            zorder=0,
        )
    ax.text(0.5, 0.97, "Hypothesized structural causal model for field estimation", ha="center", va="top", fontsize=11)
    fig.tight_layout()
    return _save(fig, output_dir, "scm_graph", ("pdf",))


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
    paths.extend(figure_time_series(metrics, output_dir, formats))
    paths.extend(figure_scatter(metrics, output_dir, formats))
    paths.extend(figure_counterfactual(scenarios, output_dir, formats))
    paths.extend(figure_ablation_penalties(metrics, output_dir, formats))
    paths.extend(figure_ablation_causal(scenarios, output_dir, formats))
    paths.extend(figure_scm(output_dir))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the CQSS-SPI manuscript figures.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "figures")
    parser.add_argument("--lambda-q", type=float, default=LAMBDA_Q)
    parser.add_argument("--lambda-s", type=float, default=LAMBDA_S)
    parser.add_argument("--epsilon", type=float, default=EPSILON)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    df = load_data(args.data)
    paths = generate_all_figures(df, args.output_dir, args.lambda_q, args.lambda_s, args.epsilon)
    print("Generated manuscript figures:")
    for path in paths:
        print(f"- {path}")


if __name__ == "__main__":
    main()
