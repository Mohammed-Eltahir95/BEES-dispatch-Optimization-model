"""Basic matplotlib plots: SOC profile, dispatch schedule, revenue breakdown."""
from __future__ import annotations

import matplotlib

# File-only backend keeps plotting reproducible in CI, servers, and containers.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from bess_opt.utils.helpers import ensure_dir, resolve_path


def plot_soc(soc_df: pd.DataFrame, out_dir: str) -> None:
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(soc_df["timestamp"], soc_df["soc_mwh"], marker="o", markersize=3)
    ax.set_title("State of Charge Profile")
    ax.set_xlabel("Time")
    ax.set_ylabel("SOC (MWh)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(resolve_path(out_dir) / "soc_profile.png", dpi=150)
    plt.close(fig)


def plot_dispatch(dispatch_df: pd.DataFrame, out_dir: str) -> None:
    ensure_dir(out_dir)
    pivot_charge = dispatch_df.pivot(index="timestamp", columns="market", values="charge_mw")
    pivot_discharge = dispatch_df.pivot(index="timestamp", columns="market", values="discharge_mw")

    fig, ax = plt.subplots(figsize=(10, 4))
    pivot_discharge.plot.area(ax=ax, alpha=0.7)
    (-pivot_charge).plot.area(ax=ax, alpha=0.7)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Dispatch Schedule by Market")
    ax.set_xlabel("Time")
    ax.set_ylabel("Power (MW)  [+discharge / -charge]")
    fig.tight_layout()
    fig.savefig(resolve_path(out_dir) / "dispatch_schedule.png", dpi=150)
    plt.close(fig)


def plot_revenue_breakdown(revenue_df: pd.DataFrame, out_dir: str) -> None:
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(revenue_df["market"], revenue_df["revenue"])
    ax.set_title("Revenue by Market")
    ax.set_ylabel("Revenue")
    fig.tight_layout()
    fig.savefig(resolve_path(out_dir) / "revenue_breakdown.png", dpi=150)
    plt.close(fig)
