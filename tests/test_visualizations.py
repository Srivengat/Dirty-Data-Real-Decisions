"""Unit tests for Module 13: Project Visualizations."""

from pathlib import Path

import pandas as pd
import pytest

from src.cleaning.pipeline import run_cleaning_pipeline
from src.data.load_data import load_raw_data
from src.visualization.visualizations import (
    generate_all_figures,
    plot_category_distribution,
    plot_closure_trend,
    plot_duplicate_summary,
    plot_missing_value_heatmap,
    plot_quality_scorecard,
    plot_triage_impact,
)


@pytest.fixture(scope="module")
def raw_df() -> pd.DataFrame:
    """Raw dataset fixture."""
    return load_raw_data("data/raw/case_management_raw.csv")


@pytest.fixture(scope="module")
def clean_df() -> pd.DataFrame:
    """Cleaned dataset fixture."""
    raw = load_raw_data("data/raw/case_management_raw.csv")
    return run_cleaning_pipeline(raw_df=raw).cleaned_df


def test_missing_value_heatmap_creates_file(raw_df, tmp_path, monkeypatch):
    """Verify missing value heatmap generates a valid PNG file."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    out = plot_missing_value_heatmap(raw_df)
    assert out.exists()
    assert out.suffix == ".png"
    assert out.stat().st_size > 5000  # > 5KB means real content was rendered


def test_closure_trend_creates_file(clean_df, tmp_path, monkeypatch):
    """Verify closure trend figure generates a valid PNG file."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    out = plot_closure_trend(clean_df)
    assert out.exists()
    assert out.stat().st_size > 5000


def test_category_distribution_creates_file(clean_df, tmp_path, monkeypatch):
    """Verify category distribution figure generates a valid PNG file."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    out = plot_category_distribution(clean_df)
    assert out.exists()
    assert out.stat().st_size > 5000


def test_duplicate_summary_creates_file(raw_df, clean_df, tmp_path, monkeypatch):
    """Verify duplicate summary figure generates a valid PNG file."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    out = plot_duplicate_summary(raw_df, clean_df)
    assert out.exists()
    assert out.stat().st_size > 5000


def test_quality_scorecard_creates_file(clean_df, tmp_path, monkeypatch):
    """Verify quality scorecard figure generates a valid PNG file."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    out = plot_quality_scorecard(clean_df, overall_score=91.11)
    assert out.exists()
    assert out.stat().st_size > 5000


def test_triage_impact_creates_file(clean_df, tmp_path, monkeypatch):
    """Verify triage impact figure generates a valid PNG file."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    out = plot_triage_impact(clean_df)
    assert out.exists()
    assert out.stat().st_size > 5000


def test_generate_all_figures(raw_df, clean_df, tmp_path, monkeypatch):
    """Verify master runner generates all 6 figures."""
    import src.visualization.visualizations as viz_module
    monkeypatch.setattr(viz_module, "FIGURES_DIR", tmp_path)
    saved = generate_all_figures(raw_df=raw_df, cleaned_df=clean_df, quality_score=91.11)
    assert len(saved) == 6
    for name, path in saved.items():
        assert path.exists(), f"Figure {name} was not created"
        assert path.stat().st_size > 5000, f"Figure {name} appears empty"
