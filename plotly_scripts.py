"""Plotly script generation helpers for admissions visualizations."""

from __future__ import annotations

import json
from typing import Dict, Tuple

import pandas as pd

from data_processor import compute_additional_stats, NumpyEncoder
from html_helpers import create_additional_stats_html


def create_plot_data_script(
    plot_id: int,
    data: pd.DataFrame,
    y_positions: Dict[str, float],
    marker_styles: Dict[str, Dict],
    symbol_map: Dict[str, str] | None = None,
) -> Tuple[str, str, str]:
    """Return JavaScript for box plots and detailed stats tables."""
    color_map = {
        "합격": {"border": "#3366CC", "fill": "rgba(51, 102, 204, 0.3)"},
        "불합격": {"border": "#DC3912", "fill": "rgba(220, 57, 18, 0.3)"},
        "충원합격": {"border": "#109618", "fill": "rgba(16, 150, 24, 0.3)"},
    }

    conv_add_stats = compute_additional_stats(data, "conv_grade")
    all_subj_add_stats = compute_additional_stats(data, "all_subj_grade")

    conv_traces: list[str] = []
    all_subj_traces: list[str] = []

    for result in ["합격", "충원합격", "불합격"]:
        result_data = data[data["result"] == result]
        y_values_conv = result_data["conv_grade"].dropna().tolist()
        if not y_values_conv:
            conv_traces.append(
                f"{{y: [], x: ['{result}'], type: 'box', name: '{result}', boxpoints: false, width: 0.5, marker: {{ color: '{color_map[result]['border']}', opacity: 0.5 }}, line: {{ color: '{color_map[result]['border']}', width: 2 }}, fillcolor: '{color_map[result]['fill']}', showlegend: false, hoverinfo: 'skip'}}"
            )
        else:
            y_json = json.dumps(y_values_conv, cls=NumpyEncoder)
            conv_traces.append(
                f"{{y: {y_json}, x: Array({len(y_values_conv)}).fill('{result}'), type: 'box', name: '{result}', boxpoints: 'outliers', width: 0.5, marker: {{ color: '{color_map[result]['border']}', size: 6, opacity: 0.8, line: {{ width: 1, color: 'rgba(0,0,0,0.5)' }} }}, line: {{ color: '{color_map[result]['border']}', width: 2 }}, fillcolor: '{color_map[result]['fill']}', boxmean: true, hoverinfo: 'y+name', hovertemplate: '환산등급: %{{y}}<br>{result}<extra></extra>'}}"
            )

        y_values_all = result_data["all_subj_grade"].dropna().tolist()
        if not y_values_all:
            all_subj_traces.append(
                f"{{y: [], x: ['{result}'], type: 'box', name: '{result}', boxpoints: false, width: 0.5, marker: {{ color: '{color_map[result]['border']}', opacity: 0.5 }}, line: {{ color: '{color_map[result]['border']}', width: 2 }}, fillcolor: '{color_map[result]['fill']}', showlegend: false, hoverinfo: 'skip'}}"
            )
        else:
            y_json = json.dumps(y_values_all, cls=NumpyEncoder)
            all_subj_traces.append(
                f"{{y: {y_json}, x: Array({len(y_values_all)}).fill('{result}'), type: 'box', name: '{result}', boxpoints: 'outliers', width: 0.5, marker: {{ color: '{color_map[result]['border']}', size: 6, opacity: 0.8, line: {{ width: 1, color: 'rgba(0,0,0,0.5)' }} }}, line: {{ color: '{color_map[result]['border']}', width: 2 }}, fillcolor: '{color_map[result]['fill']}', boxmean: true, hoverinfo: 'y+name', hovertemplate: '전교과등급: %{{y}}<br>{result}<extra></extra>'}}"
            )

    conv_html = create_additional_stats_html(conv_add_stats, "환산등급", ["합격", "충원합격", "불합격"])
    all_subj_html = create_additional_stats_html(all_subj_add_stats, "전교과등급", ["합격", "충원합격", "불합격"])
    script = (
        "<script>\n"
        "if (!window.plotsData) window.plotsData = {};\n"
        f"window.plotsData['{plot_id}'] = {{convTraces: [{', '.join(conv_traces)}], allSubjTraces: [{', '.join(all_subj_traces)}]}};\n"
        "</script>"
    )
    return script, conv_html, all_subj_html


def create_advanced_visualizations(plot_id: int, data: pd.DataFrame) -> str:
    """Return script for histogram and donut chart visualizations."""
    color_map = {"합격": "#A8D8EA", "불합격": "#FFAAA7", "충원합격": "#A8E6CE"}

    result_counts = data["result"].value_counts().to_dict()
    values: list[int] = []
    labels: list[str] = []
    colors: list[str] = []
    for result, count in result_counts.items():
        values.append(count)
        labels.append(result)
        colors.append(color_map.get(result, "#666666"))

    values_json = json.dumps(values, cls=NumpyEncoder)
    labels_json = json.dumps(labels)
    colors_json = json.dumps(colors)

    donut_data = [
        f"{{values: {values_json}, labels: {labels_json}, type: 'pie', hole: 0.6, marker: {{ colors: {colors_json} }}, textinfo: 'label+percent', textposition: 'outside', hoverinfo: 'label+value+percent', insidetextorientation: 'radial'}}"
    ]

    conv_grade_histograms: list[str] = []
    pass_data = data[data["result"].isin(["합격", "충원합격"])] ["conv_grade"].dropna()
    if len(pass_data) > 0:
        conv_grade_histograms.append(
            f"{{x: {json.dumps(pass_data.tolist(), cls=NumpyEncoder)}, type: 'histogram', name: '합격(충원포함)', opacity: 0.7, marker: {{ color: '#A8D8EA' }}, xbins: {{ start: 1, end: 9, size: 0.25 }}, hoverinfo: 'y+x+name', hoverlabel: {{ bgcolor: '#A8D8EA' }}}}"
        )
    fail_data = data[data["result"] == "불합격"]["conv_grade"].dropna()
    if len(fail_data) > 0:
        conv_grade_histograms.append(
            f"{{x: {json.dumps(fail_data.tolist(), cls=NumpyEncoder)}, type: 'histogram', name: '불합격', opacity: 0.7, marker: {{ color: '{color_map.get('불합격', '#666666')}' }}, xbins: {{ start: 1, end: 9, size: 0.25 }}, hoverinfo: 'y+x+name', hoverlabel: {{ bgcolor: '{color_map.get('불합격', '#666666')}' }}}}"
        )

    all_subj_grade_histograms: list[str] = []
    pass_data = data[data["result"].isin(["합격", "충원합격"])] ["all_subj_grade"].dropna()
    if len(pass_data) > 0:
        all_subj_grade_histograms.append(
            f"{{x: {json.dumps(pass_data.tolist(), cls=NumpyEncoder)}, type: 'histogram', name: '합격(충원포함)', opacity: 0.7, marker: {{ color: '#A8D8EA' }}, xbins: {{ start: 1, end: 9, size: 0.25 }}, hoverinfo: 'y+x+name', hoverlabel: {{ bgcolor: '#A8D8EA' }}}}"
        )
    fail_data = data[data["result"] == "불합격"]["all_subj_grade"].dropna()
    if len(fail_data) > 0:
        all_subj_grade_histograms.append(
            f"{{x: {json.dumps(fail_data.tolist(), cls=NumpyEncoder)}, type: 'histogram', name: '불합격', opacity: 0.7, marker: {{ color: '{color_map.get('불합격', '#666666')}' }}, xbins: {{ start: 1, end: 9, size: 0.25 }}, hoverinfo: 'y+x+name', hoverlabel: {{ bgcolor: '{color_map.get('불합격', '#666666')}' }}}}"
        )

    script = (
        "<script>\n"
        "if (!window.advancedVisualizationData) window.advancedVisualizationData = {};\n"
        f"window.advancedVisualizationData['{plot_id}'] = {{donutChartTraces: [{', '.join(donut_data)}], convGradeHistograms: [{', '.join(conv_grade_histograms)}], allSubjGradeHistograms: [{', '.join(all_subj_grade_histograms)}], univPassRates: []}};\n"
        "</script>"
    )
    return script
