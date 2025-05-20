from pathlib import Path
import json
from data_processor import compute_additional_stats, compute_stats, NumpyEncoder # data_processor 모듈이 있다고 가정합니다.
import pandas as pd

def create_additional_stats_html(stats, grade_type, result_order=["합격", "충원합격", "불합격"]):
    """
    추가 통계 정보를 HTML 테이블로 형식화.
    모든 등급 타입에 대해 동일한 형식 사용 (변동계수 열 제외)
    result_order: 결과를 표시할 순서
    """
    if not stats:
        return "<div class='no-stats'>통계 데이터가 없습니다.</div>"

    html_output = f"""
    <div class="stats-detail-title">{grade_type} 상세 통계</div>
    <table class="stats-table">
        <thead>
            <tr>
    """

    # 모든 등급 타입에 대해 동일한 형식 사용
    headers = ["결과", "데이터 수", "평균", "표준편차", "중앙값", "최댓값", "최솟값", "Q1-Q3 범위"]
    for header in headers:
        html_output += f"<th>{header}</th>"
    html_output += """
        </tr>
    </thead>
    <tbody>
    """

    for result_key_name in result_order:
        if result_key_name not in stats or stats[result_key_name]['count'] == 0:
            if result_key_name not in stats:
                continue

            if stats[result_key_name]['count'] == 0:
                num_cols = len(headers)
                html_output += f"""<tr><td>{result_key_name}</td><td colspan='{num_cols-1}' style='text-align:center;'>데이터 없음</td></tr>"""
                continue

        result_stats_data = stats[result_key_name]
        color_class = ""
        if result_key_name == "합격": color_class = "pass-row"
        elif result_key_name == "불합격": color_class = "fail-row"
        elif result_key_name == "충원합격": color_class = "waitlist-row"

        mean_val = f"{result_stats_data.get('mean', 'N/A'):.2f}" if isinstance(result_stats_data.get('mean'), (int, float)) else "N/A"
        std_val = f"{result_stats_data.get('std', 'N/A'):.2f}" if isinstance(result_stats_data.get('std'), (int, float)) else "N/A"
        median_val = f"{result_stats_data.get('median', 'N/A'):.2f}" if isinstance(result_stats_data.get('median'), (int, float)) else "N/A"
        max_val = f"{result_stats_data.get('max', 'N/A'):.2f}" if isinstance(result_stats_data.get('max'), (int, float)) else "N/A"
        min_val = f"{result_stats_data.get('min', 'N/A'):.2f}" if isinstance(result_stats_data.get('min'), (int, float)) else "N/A"
        q1_val = result_stats_data.get('q1')
        q3_val = result_stats_data.get('q3')
        q_range_val = "N/A"
        if isinstance(q1_val, (int, float)) and isinstance(q3_val, (int, float)):
            q_range_val = f"{q1_val:.2f} - {q3_val:.2f}"

        html_output += f"""
            <tr class="{color_class}">
                <td>{result_key_name}</td>
                <td>{result_stats_data['count']}명</td>
                <td>{mean_val}</td>
                <td>{std_val}</td>
                <td>{median_val}</td>
                <td>{max_val}</td>
                <td>{min_val}</td>
                <td>{q_range_val}</td>
            </tr>
        """

    html_output += """
        </tbody>
    </table>
    """

    return html_output

# HTML 통계 정보 생성 함수 (기존 코드 유지)
def create_stats_html(stats: dict) -> str:
    """통계 정보를 HTML 형식으로 변환"""
    sc = ''
    sc += f'<div class="stats-item stats-total">총 {stats.get("total_count",0)}명</div>'
    if 'all_pass_count' in stats:
        pr = stats['all_pass_rate'].rstrip('%')
        sc += f'<div class="stats-item stats-pass">합격(전체): {stats["all_pass_count"]}명 <span class="highlight-rate">({pr}%)</span> '
        if all(k in stats for k in ['all_pass_min','all_pass_max','all_pass_mean']):
            sc += f'<span class="highlight-range">등급 {stats["all_pass_min"]:.1f}~{stats["all_pass_max"]:.1f}</span>, <span class="highlight-mean">평균 {stats["all_pass_mean"]:.2f}</span>'
        sc += '</div>'
    if 'pass_count' in stats:
        pr = stats.get('pass_rate', '0.0%').rstrip('%')
        sc += f'<div class="stats-item stats-pass">합격(일반): {stats["pass_count"]}명 <span class="highlight-rate">({pr}%)</span></div>'
    if 'waitlist_count' in stats:
        wr = stats.get('waitlist_rate', '0.0%').rstrip('%')
        sc += f'<div class="stats-item stats-wait">합격(충원): {stats["waitlist_count"]}명 <span class="highlight-rate">({wr}%)</span></div>'
    if 'fail_count' in stats:
        fc = stats['fail_count']
        tc = stats.get('total_count', 1)
        tc = 1 if tc == 0 else tc
        sc += f'<div class="stats-item stats-fail">불합격: {fc}명 <span class="highlight-fail-rate">({fc/tc*100:.1f}%)</span></div>'
    return sc

    # 플롯 데이터 스크립트 생성 함수 (수정됨: 평균 숫자 표시 제거)
def create_plot_data_script(plot_id, data, y_positions, marker_styles, symbol_map=None):
    """
    환산등급과 전교과 등급에 대한 박스플롯 데이터를 생성하는 JavaScript 코드 반환
    추가 통계 정보를 함께 표시, 결과 순서 변경
    모든 결과 카테고리(합격, 충원합격, 불합격)에 대해 항상 trace 생성
    """
    color_map = {
        "합격": {"border": "#3366CC", "fill": "rgba(51, 102, 204, 0.3)"},
        "불합격": {"border": "#DC3912", "fill": "rgba(220, 57, 18, 0.3)"},
        "충원합격": {"border": "#109618", "fill": "rgba(16, 150, 24, 0.3)"}
    }
    conv_add_stats = compute_additional_stats(data, "conv_grade")
    all_subj_add_stats = compute_additional_stats(data, "all_subj_grade")
    conv_traces = []
    # conv_means_traces = [] # 평균 숫자 표시 제거

    for result in ["합격", "충원합격", "불합격"]:
        result_data = data[data["result"] == result]
        y_values_conv = result_data["conv_grade"].dropna().tolist()
        if len(y_values_conv) == 0:
            conv_traces.append(f"""{{
                y: [], x: ['{result}'], type: 'box', name: '{result}', boxpoints: false, width: 0.5,
                marker: {{ color: '{color_map[result]["border"]}', opacity: 0.5 }},
                line: {{ color: '{color_map[result]["border"]}', width: 2 }},
                fillcolor: '{color_map[result]["fill"]}', showlegend: false, hoverinfo: 'skip'
            }}""")
        else:
            y_values_json = json.dumps(y_values_conv, cls=NumpyEncoder)
            # mean_value = sum(y_values_conv) / len(y_values_conv) if len(y_values_conv) > 0 else 0 # 평균 숫자 표시 제거

            conv_traces.append(f"""{{
                y: {y_values_json}, x: Array({len(y_values_conv)}).fill('{result}'), type: 'box', name: '{result}',
                boxpoints: 'outliers', width: 0.5,
                marker: {{ color: '{color_map[result]["border"]}', size: 6, opacity: 0.8, line: {{ width: 1, color: 'rgba(0,0,0,0.5)' }} }},
                line: {{ color: '{color_map[result]["border"]}', width: 2 }},
                fillcolor: '{color_map[result]["fill"]}', boxmean: true, hoverinfo: 'y+name',
                hovertemplate: '환산등급: %{{y}}<br>{result}<extra></extra>'
            }}""")

            # 평균값을 표시하는 텍스트 트레이스 추가 (제거됨)
            # conv_means_traces.append(f"""{{
            #     type: 'scatter',
            #     x: ['{result}'],
            #     y: [{mean_value}],
            #     mode: 'text',
            #     text: ['평균: {mean_value:.2f}'],
            #     textposition: 'top center',
            #     textfont: {{ size: 11, color: '{color_map[result]["border"]}', weight: 'bold' }},
            #     showlegend: false,
            #     hoverinfo: 'none'
            # }}""")

    all_subj_traces = []
    # all_subj_means_traces = [] # 평균 숫자 표시 제거

    for result in ["합격", "충원합격", "불합격"]:
        result_data = data[data["result"] == result]
        y_values_all_subj = result_data["all_subj_grade"].dropna().tolist()
        if len(y_values_all_subj) == 0:
            all_subj_traces.append(f"""{{
                y: [], x: ['{result}'], type: 'box', name: '{result}', boxpoints: false, width: 0.5,
                marker: {{ color: '{color_map[result]["border"]}', opacity: 0.5 }},
                line: {{ color: '{color_map[result]["border"]}', width: 2 }},
                fillcolor: '{color_map[result]["fill"]}', showlegend: false, hoverinfo: 'skip'
            }}""")
        else:
            y_values_json = json.dumps(y_values_all_subj, cls=NumpyEncoder)
            # mean_value = sum(y_values_all_subj) / len(y_values_all_subj) if len(y_values_all_subj) > 0 else 0 # 평균 숫자 표시 제거

            all_subj_traces.append(f"""{{
                y: {y_values_json}, x: Array({len(y_values_all_subj)}).fill('{result}'), type: 'box', name: '{result}',
                boxpoints: 'outliers', width: 0.5,
                marker: {{ color: '{color_map[result]["border"]}', size: 6, opacity: 0.8, line: {{ width: 1, color: 'rgba(0,0,0,0.5)' }} }},
                line: {{ color: '{color_map[result]["border"]}', width: 2 }},
                fillcolor: '{color_map[result]["fill"]}', boxmean: true, hoverinfo: 'y+name',
                hovertemplate: '전교과등급: %{{y}}<br>{result}<extra></extra>'
            }}""")

            # 평균값을 표시하는 텍스트 트레이스 추가 (제거됨)
            # all_subj_means_traces.append(f"""{{
            #     type: 'scatter',
            #     x: ['{result}'],
            #     y: [{mean_value}],
            #     mode: 'text',
            #     text: ['평균: {mean_value:.2f}'],
            #     textposition: 'top center',
            #     textfont: {{ size: 11, color: '{color_map[result]["border"]}', weight: 'bold' }},
            #     showlegend: false,
            #     hoverinfo: 'none'
            # }}""")

    conv_stats_html_table = create_additional_stats_html(conv_add_stats, "환산등급", ["합격", "충원합격", "불합격"])
    all_subj_stats_html_table = create_additional_stats_html(all_subj_add_stats, "전교과등급", ["합격", "충원합격", "불합격"])
    script = f"""
    <script>
    if (!window.plotsData) window.plotsData = {{}};
    window.plotsData["{plot_id}"] = {{
        convTraces: [ {", ".join(conv_traces)} ],
        allSubjTraces: [ {", ".join(all_subj_traces)} ]
    }};
    </script>
    """
    # 위 script 문자열에서 conv_means_traces와 all_subj_means_traces 부분을 제거했습니다.
    # 원래 코드: convTraces: [ {", ".join(conv_traces)}, {", ".join(conv_means_traces)} ],
    # 원래 코드: allSubjTraces: [ {", ".join(all_subj_traces)}, {", ".join(all_subj_means_traces)} ]

    return script, conv_stats_html_table, all_subj_stats_html_table

# 새로운 함수: 히스토그램 및 추가 시각화 생성
def create_advanced_visualizations(plot_id, data):
    """전체 데이터 요약에 대한 추가 시각화 생성"""
    # 파스텔톤 색상 맵
    color_map = {
        "합격": "#A8D8EA",     # 부드러운 하늘색
        "불합격": "#FFAAA7",   # 부드러운 핑크/연한 빨강
        "충원합격": "#A8E6CE"  # 부드러운 민트색
    }

    # 1. 결과별 도넛 차트 데이터 생성
    result_counts = data['result'].value_counts().to_dict()

    # 도넛 차트 데이터 - 모든 결과를 하나의 차트로 표시
    values = []
    labels = []
    colors = []

    for result, count in result_counts.items():
        values.append(count)
        labels.append(result)
        colors.append(color_map.get(result, "#666666"))

    # 값, 레이블, 색상을 모두 JSON으로 변환
    values_json = json.dumps(values, cls=NumpyEncoder)
    labels_json = json.dumps(labels)
    colors_json = json.dumps(colors)

    donut_data = [f"""{{
        values: {values_json},
        labels: {labels_json},
        type: 'pie',
        hole: 0.6,
        marker: {{ colors: {colors_json} }},
        textinfo: 'label+percent',
        textposition: 'outside',
        hoverinfo: 'label+value+percent',
        insidetextorientation: 'radial'
    }}"""]

    # 2. 환산등급 히스토그램 데이터
    conv_grade_histograms = []

    # 합격(충원합격 포함) 데이터
    pass_data = data[data["result"].isin(["합격", "충원합격"])]["conv_grade"].dropna()
    if len(pass_data) > 0:
        values_json = json.dumps(pass_data.tolist(), cls=NumpyEncoder)
        conv_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '합격(충원포함)',
            opacity: 0.7,
            marker: {{ color: '#A8D8EA' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '#A8D8EA' }}
        }}""")

    # 불합격 데이터
    fail_data = data[data["result"] == "불합격"]["conv_grade"].dropna()
    if len(fail_data) > 0:
        values_json = json.dumps(fail_data.tolist(), cls=NumpyEncoder)
        conv_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '불합격',
            opacity: 0.7,
            marker: {{ color: '{color_map.get("불합격", "#666666")}' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '{color_map.get("불합격", "#666666")}' }}
        }}""")

    # 3. 전교과등급 히스토그램 데이터
    all_subj_grade_histograms = []

    # 합격(충원합격 포함) 데이터
    pass_data = data[data["result"].isin(["합격", "충원합격"])]["all_subj_grade"].dropna()
    if len(pass_data) > 0:
        values_json = json.dumps(pass_data.tolist(), cls=NumpyEncoder)
        all_subj_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '합격(충원포함)',
            opacity: 0.7,
            marker: {{ color: '#A8D8EA' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '#A8D8EA' }}
        }}""")

    # 불합격 데이터
    fail_data = data[data["result"] == "불합격"]["all_subj_grade"].dropna()
    if len(fail_data) > 0:
        values_json = json.dumps(fail_data.tolist(), cls=NumpyEncoder)
        all_subj_grade_histograms.append(f"""{{
            x: {values_json},
            type: 'histogram',
            name: '불합격',
            opacity: 0.7,
            marker: {{ color: '{color_map.get("불합격", "#666666")}' }},
            xbins: {{ start: 1, end: 9, size: 0.25 }},
            hoverinfo: 'y+x+name',
            hoverlabel: {{ bgcolor: '{color_map.get("불합격", "#666666")}' }}
        }}""")

    # 4. 대학별 합격률 상위 10개 대학 (가로 막대 차트)
    univ_pass_rates = []
    if len(data) > 0 and 'univ' in data.columns: # 'univ' 컬럼 존재 확인
        # 대학별 지원자 및 합격자 수 계산
        univ_stats = {}
        for univ, group in data.groupby('univ'):
            total = len(group)
            passed = len(group[group['result'].isin(['합격', '충원합격'])])
            if total >= 5:  # 최소 5명 이상 지원한 대학만 포함
                univ_stats[univ] = {'total': total, 'passed': passed, 'rate': passed/total*100 if total > 0 else 0} # ZeroDivisionError 방지

        # 합격률 상위 10개 대학 선택
        top_univs = sorted(univ_stats.items(), key=lambda x: x[1]['rate'], reverse=True)[:10]

        if top_univs:
            univs = [item[0] for item in top_univs]
            rates = [item[1]['rate'] for item in top_univs]
            totals = [item[1]['total'] for item in top_univs]

            univs_json = json.dumps(univs)
            rates_json = json.dumps(rates)
            totals_json = json.dumps(totals)

            univ_pass_rates.append(f"""{{
                y: {univs_json},
                x: {rates_json},
                text: {totals_json}.map(val => '지원자: ' + val + '명'),
                type: 'bar',
                orientation: 'h',
                marker: {{
                    color: {rates_json}.map(val =>
                        val >= 70 ? '#A8D8EA' :  // 높은 합격률 - 부드러운 하늘색
                        val >= 50 ? '#A8E6CE' :  // 중간 합격률 - 부드러운 민트색
                        val >= 30 ? '#FFD3B5' :  // 낮은 합격률 - 부드러운 주황색
                        '#FFAAA7'               // 매우 낮은 합격률 - 부드러운 핑크
                    ),
                    line: {{ width: 0 }}
                }},
                hoverinfo: 'text',
                text: {univs_json}.map((univ, i) => univ + '<br>합격률: ' + {rates_json}[i].toFixed(1) + '%<br>' + '지원자: ' + {totals_json}[i] + '명')
            }}""")

    # 모든 시각화를 위한 스크립트 생성
    script = f"""
    <script>
    if (!window.advancedVisualizationData) window.advancedVisualizationData = {{}};
    window.advancedVisualizationData["{plot_id}"] = {{
        donutChartTraces: [ {", ".join(donut_data) if donut_data else ""} ],
        convGradeHistograms: [ {", ".join(conv_grade_histograms) if conv_grade_histograms else ""} ],
        allSubjGradeHistograms: [ {", ".join(all_subj_grade_histograms) if all_subj_grade_histograms else ""} ],
        univPassRates: [ {", ".join(univ_pass_rates) if univ_pass_rates else ""} ]
    }};
    </script>
    """

    # HTML 컨테이너 생성
    visualizations_html = f"""
    <div class="advanced-visualizations-container">
        <div class="visualization-row">
            <div class="half-width-visualization">
                <div class="visualization-title">결과별 분포</div>
                <div class="plot-container" id="donut-chart-{plot_id}" style="height: 400px;"></div>
            </div>
            <div class="half-width-visualization">
                <div class="visualization-title">대학별 합격률 (상위 10개)</div>
                <div class="plot-container" id="univ-pass-rates-{plot_id}" style="height: 400px;"></div>
            </div>
        </div>
        <div class="visualization-row">
            <div class="full-width-visualization">
                <div class="visualization-title">환산등급 분포</div>
                <div class="plot-container" id="conv-grade-histogram-{plot_id}" style="height: 350px;"></div>
            </div>
        </div>
        <div class="visualization-row">
            <div class="full-width-visualization">
                <div class="visualization-title">전교과등급 분포</div>
                <div class="plot-container" id="all-subj-grade-histogram-{plot_id}" style="height: 350px;"></div>
            </div>
        </div>
    </div>
    """

    # JavaScript 초기화 코드
    init_script = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        initAdvancedVisualizations("{plot_id}");
    }});

    function initAdvancedVisualizations(plotId) {{
        if (!window.Plotly || !window.advancedVisualizationData || !window.advancedVisualizationData[plotId]) return;

        var data = window.advancedVisualizationData[plotId];

        // 결과별 도넛 차트
        if (data.donutChartTraces && data.donutChartTraces.length > 0 && document.getElementById('donut-chart-' + plotId)) {{
            try {{
                Plotly.newPlot('donut-chart-' + plotId, data.donutChartTraces, {{
                    title: '',
                    legend: {{ orientation: 'h', y: -0.1, x: 0.5, xanchor: 'center' }},
                    margin: {{ t: 30, b: 50, l: 50, r: 50 }},
                    autosize: true,
                    height: 350,
                    plot_bgcolor: '#FAFAFA',
                    paper_bgcolor: '#FAFAFA'
                }}, {{ displayModeBar: false, responsive: true }});
            }} catch (e) {{ console.error("도넛 차트 생성 오류:", e); }}
        }}

        // 대학별 합격률
        if (data.univPassRates && data.univPassRates.length > 0 && document.getElementById('univ-pass-rates-' + plotId)) {{
           try {{
                Plotly.newPlot('univ-pass-rates-' + plotId, data.univPassRates, {{
                    title: '',
                    showlegend: false,
                    margin: {{ t: 30, b: 50, l: 150, r: 50 }},
                    xaxis: {{ title: '합격률 (%)', range: [0, 100] }},
                    yaxis: {{ automargin: true }},
                    autosize: true,
                    height: 350,
                    plot_bgcolor: '#FAFAFA',
                    paper_bgcolor: '#FAFAFA'
                }}, {{ displayModeBar: false, responsive: true }});
            }} catch (e) {{ console.error("대학별 합격률 차트 생성 오류:", e); }}
        }}

        // 환산등급 히스토그램
        if (data.convGradeHistograms && data.convGradeHistograms.length > 0 && document.getElementById('conv-grade-histogram-' + plotId)) {{
            try {{
                Plotly.newPlot('conv-grade-histogram-' + plotId, data.convGradeHistograms, {{
                    title: '',
                    barmode: 'overlay',
                    bargap: 0.1,
                    xaxis: {{ title: '환산등급', range: [1, 9], dtick: 1 }},
                    yaxis: {{ title: '인원 (명)' }},
                    legend: {{ orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }},
                    margin: {{ t: 30, b: 60, l: 60, r: 50 }},
                    autosize: true,
                    height: 350,
                    plot_bgcolor: '#FAFAFA',
                    paper_bgcolor: '#FAFAFA'
                }}, {{ displayModeBar: false, responsive: true }});
            }} catch (e) {{ console.error("환산등급 히스토그램 생성 오류:", e); }}
        }}

        // 전교과등급 히스토그램
        if (data.allSubjGradeHistograms && data.allSubjGradeHistograms.length > 0 && document.getElementById('all-subj-grade-histogram-' + plotId)) {{
            try {{
                Plotly.newPlot('all-subj-grade-histogram-' + plotId, data.allSubjGradeHistograms, {{
                    title: '',
                    barmode: 'overlay',
                    bargap: 0.1,
                    xaxis: {{ title: '전교과등급', range: [1, 9], dtick: 1 }},
                    yaxis: {{ title: '인원 (명)' }},
                    legend: {{ orientation: 'h', y: 1.1, x: 0.5, xanchor: 'center' }},
                    margin: {{ t: 30, b: 60, l: 60, r: 50 }},
                    autosize: true,
                    height: 350,
                    plot_bgcolor: '#FAFAFA',
                    paper_bgcolor: '#FAFAFA'
                }}, {{ displayModeBar: false, responsive: true }});
            }} catch (e) {{ console.error("전교과등급 히스토그램 생성 오류:", e); }}
        }}
    }}
    </script>
    """

    return script + visualizations_html + init_script


# 선택된 모집단위에 대한 대학별 시각화 함수 (전형 필터 추가)
def plot_selected_depts(df: pd.DataFrame, out_dir: Path, selected_depts: list = None, selected_univs: list = None, selected_subtypes: list = None, output_file: str = "선택된_모집단위들.html") -> str:
    """선택된 모집단위에 대한 입시 결과를 대학별로 시각화"""
    # 선택된 모집단위와 대학에 해당하는 데이터만 필터링
    df_filtered = df.copy()

    # 선택된 모집단위 필터링
    if selected_depts:
        df_filtered = df_filtered[df_filtered['dept'].isin(selected_depts)]

    # 선택된 대학 필터링
    if selected_univs:
        df_filtered = df_filtered[df_filtered['univ'].isin(selected_univs)]

    # 선택된 전형 필터링
    if selected_subtypes:
        df_filtered = df_filtered[df_filtered['subtype'].isin(selected_subtypes)]

    if df_filtered.empty:
        return "선택된 조건에 맞는 데이터가 없습니다."

    # 필터링된 데이터에서 대학 목록 추출 (순서 보존을 위해 사용)
    universities = sorted(df_filtered['univ'].unique())

    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>선택된 모집단위 입시 결과</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body, html {{ margin:0; padding:0; font-family:'Malgun Gothic', '맑은 고딕', sans-serif; background-color: #f4f7f6; }}
            .fixed-header {{ position: sticky; top: 0; background-color: white; padding: 10px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 1000; width: 100%; border-bottom: 1px solid #ddd; }}
            .header-content {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; flex-direction: column; align-items: center; }}
            .university-title {{ text-align: center; font-size: 24px; margin: 10px 0 15px; font-weight: bold; color: #333; }}
            .controls-legend-wrapper {{ display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 10px; flex-wrap: wrap; }}
            .grade-toggle-container {{ padding: 10px; background-color: #f8f8f8; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); flex: 1; min-width: 280px; margin-right: 10px; text-align: center; }}
            .grade-toggle-btn {{ padding: 10px 18px; margin: 0 5px; font-size: 14px; cursor: pointer; border: 1px solid #ccc; border-radius: 6px; background-color: white; transition: all 0.2s ease-in-out; font-weight: 500; }}
            .grade-toggle-btn:hover {{ background-color: #e9e9e9; border-color: #bbb; }}
            .grade-toggle-btn.active {{ background-color: #007bff; color: white; border-color: #0056b3; box-shadow: 0 0 5px rgba(0,123,255,0.5); }}
            .legend-container {{ display: flex; flex-direction: column; align-items: flex-start; flex: 1; min-width: 300px; background-color: #f8f8f8; padding: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            .legend-items-wrapper {{ display: flex; justify-content: flex-start; margin-bottom: 8px; flex-wrap: wrap; }}
            .legend-item {{ display: inline-flex; align-items: center; margin: 5px 10px 5px 0; }}
            .legend-marker {{ width: 18px; height: 18px; margin-right: 8px; display: inline-block; border-radius: 4px; }}
            .legend-text {{ font-size: 14px; color: #333; }}
            .axis-label {{ font-size: 13px; color: #505050; font-weight: bold; margin-top: 5px; }}
            .axis-icon {{ font-size: 16px; margin-right: 5px; }}
            .layout {{ display: flex; justify-content: center; align-items: flex-start; max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
            .toc-container {{ flex: 0 0 220px; position: sticky; top: 160px; margin-right: 25px; background-color: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; max-height: calc(100vh - 200px); overflow-y: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.08); z-index: 900; }}
            .toc-header {{ font-weight: bold; font-size: 18px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; color: #333; }}
            .toc-university {{ font-weight: bold; margin-top: 10px; cursor: pointer; padding: 6px 8px; border-radius: 4px; transition: background-color 0.2s; color: #0056b3; }}
            .toc-university:hover {{ background-color: #e9ecef; }}
            .toc-subtype-item {{ margin-left: 18px; font-size: 0.9em; cursor: pointer; padding: 5px 8px; border-radius: 4px; transition: background-color 0.2s; color: #333; }}
            .toc-subtype-item:hover {{ background-color: #f1f3f5; }}
            .main-content {{ flex: 1 1 auto; max-width: calc(100% - 245px); padding-top: 20px; }}
            .dept-container {{ margin-bottom: 50px; border: 1px solid #d1d9e6; border-radius: 12px; padding: 25px; background-color: #ffffff; box-shadow: 0 6px 18px rgba(0,0,0,0.07); }}
            .dept-header {{ margin-bottom: 20px; font-weight: bold; font-size: 22px; color: #2c3e50; border-bottom: 2px solid #007bff; padding-bottom: 12px; }}
            .subtype-container {{ margin-bottom: 30px; border: 1px solid #e7eaf0; border-radius: 8px; padding: 20px; background-color: #fdfdfd; }}
            .subtype-header {{ margin-bottom: 15px; font-weight: bold; font-size: 18px; color: #34495e; }}
            .visualization-container {{ display: flex; flex-direction: column; width: 100%; margin-bottom: 20px; }}
            .plot-stats-wrapper {{ width: 100%; margin-bottom: 10px; }}
            .stats-container {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }}
            .stats-item {{ padding: 6px 12px; border-radius: 6px; background-color: #f0f4f7; white-space: nowrap; font-size: 14px; color: #333; border: 1px solid #d6dde3; }}
            .stats-total {{ font-weight: bold; background-color: #e2e8ef; border-color: #c8d0d8; }}
            .stats-pass {{ border-left: 4px solid #007bff; }}
            .stats-wait {{ border-left: 4px solid #28a745; }}
            .stats-fail {{ border-left: 4px solid #dc3545; }}
            .highlight-rate, .highlight-fail-rate {{ font-weight: bold; }}
            .highlight-rate {{ color: #0056b3; }}
            .highlight-fail-rate {{ color: #c82333; }}
            .highlight-mean {{ font-weight: bold; color: #1e7e34; }}
            .highlight-range {{ color: #5a6268; font-size: 13px; }}
            .plot-container {{ height: 350px; width: 100%; margin: 0 auto; }}
            .stats-tables-wrapper {{ width: 100%; margin-bottom: 30px; }}
            .additional-stats-container {{ width: 100%; padding: 10px 0; background-color: transparent; border-radius: 0; font-size: 13px; }}
            .stats-detail-title {{ font-weight: bold; margin-bottom: 8px; color: #333; font-size: 15px; }}
            .stats-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; table-layout: fixed; }}
            .stats-table th, .stats-table td {{ padding: 8px; text-align: center; border: 1px solid #dee2e6; }}
            .stats-table th {{ background-color: #e9ecef; font-weight: bold; color: #495057; }}
            .stats-table .pass-row td {{ background-color: rgba(0, 123, 255, 0.05); }}
            .stats-table .fail-row td {{ background-color: rgba(220, 53, 69, 0.05); }}
            .stats-table .waitlist-row td {{ background-color: rgba(40, 167, 69, 0.05); }}
            .no-stats {{ font-style: italic; color: #6c757d; text-align: center; padding: 15px; }}
            /* 추가 시각화를 위한 스타일 */
            .advanced-visualizations-container {{ width: 100%; margin-top: 20px; }}
            .visualization-row {{ display: flex; margin-bottom: 30px; gap: 20px; flex-wrap: wrap; }}
            .half-width-visualization {{ flex: 1 1 calc(50% - 10px); min-width: 400px; background-color: #FFFFFF; border-radius: 12px; padding: 20px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); }}
            .full-width-visualization {{ flex: 1 1 100%; background-color: #FFFFFF; border-radius: 12px; padding: 20px; box-shadow: 0 3px 10px rgba(0,0,0,0.05); }}
            .visualization-title {{ font-weight: bold; font-size: 16px; margin-bottom: 15px; color: #506380; text-align: center; }}
            @media (max-width: 992px) {{
                .layout {{ flex-direction: column; align-items: center; }}
                .toc-container {{ position: static; width: 100%; max-width: 600px; margin-right: 0; margin-bottom: 20px; max-height: 300px; }}
                .main-content {{ max-width: 100%; width: 100%; }}
                .controls-legend-wrapper {{ flex-direction: column; align-items: stretch; }}
                .grade-toggle-container, .legend-container {{ width: auto; margin-right: 0; margin-bottom: 10px; }}
                .visualization-row {{ flex-direction: column; }}
                .half-width-visualization {{ min-width: 100%; margin-bottom: 15px; }}
            }}
            @media (max-width: 768px) {{
                .fixed-header {{ padding: 5px 0; }}
                .header-content {{ padding: 0 10px; }}
                .university-title {{ font-size: 20px; margin-bottom: 10px; }}
                .grade-toggle-btn {{ padding: 8px 12px; font-size: 13px; }}
                .legend-item {{ margin: 3px 8px 3px 0; }}
                .legend-text, .axis-label {{ font-size: 12px; }}
                .dept-header {{ font-size: 20px; }}
                .subtype-header {{ font-size: 17px; }}
                .stats-item {{ font-size: 13px; padding: 5px 10px; }}
                .plot-container {{ height: 300px; }}
                .additional-stats-container {{ padding: 10px 0; }}
                .stats-detail-title {{ font-size: 14px; }}
                .stats-table th, .stats-table td {{ padding: 6px; }}
            }}
            .filter-info-container {{
                margin: 15px 0;
                background-color: #e9f7fe;
                border: 1px solid #b8e3ff;
                padding: 15px;
                border-radius: 8px;
            }}
            .filter-info-container h3 {{
                margin-top: 0;
                color: #0275d8;
                font-size: 16px;
                margin-bottom: 10px;
            }}
            .filter-info-container ul {{
                margin: 0;
                padding-left: 20px;
            }}
            .filter-info-container li {{
                margin-bottom: 5px;
                font-size: 14px;
            }}
        </style>

    </head>
    <body>
        <div class="fixed-header">
            <div class="header-content">
                <div class="university-title">선택된 모집단위 입시 결과</div>
                <div class="controls-legend-wrapper">
                    <div class="grade-toggle-container">
                        <button id="btn-conv-grade" class="grade-toggle-btn active" onclick="switchGradeType('conv')">환산등급</button>
                        <button id="btn-all-subj-grade" class="grade-toggle-btn" onclick="switchGradeType('all_subj')">전교과100 등급</button>
                    </div>
                    <div class="legend-container">
                        <div class="legend-items-wrapper">
                            <div class="legend-item"><span class="legend-marker" style="background-color: rgba(51, 102, 204, 0.7);"></span><span class="legend-text">합격</span></div>
                            <div class="legend-item"><span class="legend-marker" style="background-color: rgba(16, 150, 24, 0.7);"></span><span class="legend-text">충원합격</span></div>
                            <div class="legend-item"><span class="legend-marker" style="background-color: rgba(220, 57, 18, 0.7);"></span><span class="legend-text">불합격</span></div>
                        </div>
                        <div class="axis-label"><span class="axis-icon">↕</span> Y축: <span id="grade-type-label">환산등급</span> (1등급 ~ 9등급)</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="layout">
            <aside class="toc-container">
                <div class="toc-header">목차</div>
                <div id="toc-content"></div>
            </aside>
            <main class="main-content">\n"""

    y_positions = {"합격":0.01, "충원합격":0.0, "불합격":-0.03}
    marker_styles = {
        "합격": {"opacity":0.7, "line":dict(width=1.5, color="blue"), "color":"rgba(0,0,255,0.3)"},
        "불합격": {"opacity":0.6, "line":dict(width=0.7, color="red"), "color":"rgba(255,0,0,0.2)"},
        "충원합격": {"opacity":0.7, "line":dict(width=1.2, color="steelblue"), "color":"rgba(70,130,180,0.3)"}
    }
    plot_counter = 1

    for univ_idx, univ in enumerate(universities, 1):
        # 현재 대학 + 선택된 모집단위에 해당하는 데이터 필터링
        df_univ = df_filtered[df_filtered['univ'] == univ]
        html_content += f"""
        <div class="dept-container" id="univ-{univ_idx}">
            <div class="dept-header">{univ}</div>
        """

        # 각 대학에서 모집단위 목록 가져오기
        if selected_depts:
            univ_depts = sorted(set(df_univ['dept']) & set(selected_depts))
        else:
            univ_depts = sorted(df_univ['dept'].unique())

        # 모집단위별 루프
        for d_idx, dept in enumerate(univ_depts, 1):
            dd = df_univ[df_univ['dept'] == dept]

            html_content += f"""
            <div class="subtype-container" id="dept-container-{univ_idx}-{d_idx}">
                <div class="subtype-header" style="color: #34495e;">{d_idx}) {dept}</div>
            """

            # 선택된 전형 목록 가져오기
            if selected_subtypes:
                dept_subtypes = sorted(set(dd['subtype']) & set(selected_subtypes))
            else:
                dept_subtypes = sorted(dd['subtype'].unique())

            # 전형별 루프
            for st_idx, subtype_val in enumerate(dept_subtypes, 1):
                st_data = dd[dd['subtype'] == subtype_val]
                if st_data.empty:
                    continue

                # 통계 계산
                conv_stats = compute_stats(st_data, "conv_grade")
                all_subj_stats = compute_stats(st_data, "all_subj_grade")
                conv_stats_html = create_stats_html(conv_stats)
                all_subj_stats_html = create_stats_html(all_subj_stats)

                # 박스플롯 스크립트 및 통계 테이블 생성
                plot_script, conv_detail_stats, all_subj_detail_stats = create_plot_data_script(
                    plot_counter, st_data, y_positions, marker_styles
                )

                html_content += f"""
                <div class="subtype-container" id="subtype-{univ_idx}-{d_idx}-{st_idx}" style="margin-left: 20px; background-color: #fbfcfe;">
                    <div class="subtype-header" style="font-size: 16px; color: #4a5568;">{st_idx}) {subtype_val}</div>
                    <div class="visualization-container">
                        <div class="plot-stats-wrapper">
                            <div id="conv-stats-{plot_counter}" class="stats-container">{conv_stats_html}</div>
                            <div id="all-subj-stats-{plot_counter}" class="stats-container" style="display:none;">{all_subj_stats_html}</div>
                            <div class="plot-container" id="plot-{plot_counter}"></div>
                        </div>
                        {plot_script}
                        <div class="stats-tables-wrapper">
                            <div id="conv-additional-stats-{plot_counter}" class="additional-stats-container">
                                {conv_detail_stats}
                            </div>
                            <div id="all-subj-additional-stats-{plot_counter}" class="additional-stats-container" style="display:none;">
                                {all_subj_detail_stats}
                            </div>
                        </div>
                    </div>
                </div>
                """
                plot_counter += 1

            # 모집단위별 요약 (모든 전형 포함)
            dept_summary_stats_conv = compute_stats(dd, "conv_grade")
            dept_summary_stats_all_subj = compute_stats(dd, "all_subj_grade")
            dept_summary_html_conv = create_stats_html(dept_summary_stats_conv)
            dept_summary_html_all_subj = create_stats_html(dept_summary_stats_all_subj)

            plot_script, conv_detail_stats, all_subj_detail_stats = create_plot_data_script(
                plot_counter, dd, y_positions, marker_styles
            )

            html_content += f"""
            <div class="subtype-container" id="dept-summary-{univ_idx}-{d_idx}" style="margin-left: 20px; background-color: #f0f4f8;">
                <div class="subtype-header" style="font-size: 16px; color: #2c3e50;">전체 전형 통합</div>
                <div class="visualization-container">
                    <div class="plot-stats-wrapper">
                        <div id="conv-stats-{plot_counter}" class="stats-container">{dept_summary_html_conv}</div>
                        <div id="all-subj-stats-{plot_counter}" class="stats-container" style="display:none;">{dept_summary_html_all_subj}</div>
                        <div class="plot-container" id="plot-{plot_counter}"></div>
                    </div>
                    {plot_script}
                    <div class="stats-tables-wrapper">
                        <div id="conv-additional-stats-{plot_counter}" class="additional-stats-container">
                            {conv_detail_stats}
                        </div>
                        <div id="all-subj-additional-stats-{plot_counter}" class="additional-stats-container" style="display:none;">
                            {all_subj_detail_stats}
                        </div>
                    </div>
                </div>
            </div>
            """
            plot_counter += 1

            html_content += """
            </div>
            """

        # 대학별 전형 요약 섹션 (이전 코드와 유사)
        summary_container_id = f"summary-container-{univ_idx}"
        html_content += f"""
        <div class="subtype-container" id="{summary_container_id}" style="background-color: #eef2f7;">
            <div class="subtype-header" style="color: #1a202c;">전형별 요약</div>
        """

        # 전형 목록 가져오기
        if selected_subtypes:
            subtypes_all = sorted(set(df_univ['subtype']) & set(selected_subtypes))
        else:
            subtypes_all = sorted(df_univ['subtype'].unique())

        for s_idx, subtype in enumerate(subtypes_all, 1):
            # 해당 전형의 모든 데이터 추출
            ss = df_univ[df_univ['subtype'] == subtype]

            # 선택된 모집단위 필터링 적용
            if selected_depts:
                ss = ss[ss['dept'].isin(selected_depts)]
                if ss.empty:
                    continue

            # 통계 계산
            conv_stats = compute_stats(ss, "conv_grade")
            all_subj_stats = compute_stats(ss, "all_subj_grade")
            conv_stats_html = create_stats_html(conv_stats)
            all_subj_stats_html = create_stats_html(all_subj_stats)

            # 박스플롯 스크립트 및 통계 테이블 생성
            plot_script, conv_detail_stats, all_subj_detail_stats = create_plot_data_script(
                plot_counter, ss, y_positions, marker_styles
            )

            html_content += f"""
                <div class="subtype-container" id="subtype-summary-{univ_idx}-{s_idx}" style="margin-left: 20px; background-color: #fbfcfe;">
                    <div class="subtype-header" style="font-size: 16px; color: #4a5568;">{subtype}</div>
                    <div class="visualization-container">
                        <div class="plot-stats-wrapper">
                            <div id="conv-stats-{plot_counter}" class="stats-container">{conv_stats_html}</div>
                            <div id="all-subj-stats-{plot_counter}" class="stats-container" style="display:none;">{all_subj_stats_html}</div>
                            <div class="plot-container" id="plot-{plot_counter}"></div>
                        </div>
                        {plot_script}
                        <div class="stats-tables-wrapper">
                            <div id="conv-additional-stats-{plot_counter}" class="additional-stats-container">
                                {conv_detail_stats}
                            </div>
                            <div id="all-subj-additional-stats-{plot_counter}" class="additional-stats-container" style="display:none;">
                                {all_subj_detail_stats}
                            </div>
                        </div>
                    </div>
                </div>
            """
            plot_counter += 1

        html_content += """
        </div>
        </div>
        """

    # 전체 데이터 요약 섹션 추가
    html_content += """
    <div class="dept-container" id="overall-summary">
        <div class="dept-header" style="color: #2c3e50; border-bottom: 2px solid #e74c3c;">전체 데이터 요약</div>
        <div class="subtype-container" style="background-color: #f8f9fa;">
            <div class="subtype-header" style="color: #1a202c;">선택된 모든 필터에 대한 종합 분석</div>
    """

    # 전체 필터링된 데이터에 대한 통계 계산
    overall_conv_stats = compute_stats(df_filtered, "conv_grade")
    overall_all_subj_stats = compute_stats(df_filtered, "all_subj_grade")
    overall_conv_stats_html = create_stats_html(overall_conv_stats)
    overall_all_subj_stats_html = create_stats_html(overall_all_subj_stats)

    # 박스플롯 스크립트 및 통계 테이블 생성
    overall_plot_script, overall_conv_detail_stats, overall_all_subj_detail_stats = create_plot_data_script(
        plot_counter, df_filtered, y_positions, marker_styles
    )

    html_content += f"""
        <div class="visualization-container">
            <div class="plot-stats-wrapper">
                <div id="conv-stats-{plot_counter}" class="stats-container">{overall_conv_stats_html}</div>
                <div id="all-subj-stats-{plot_counter}" class="stats-container" style="display:none;">{overall_all_subj_stats_html}</div>
                <div class="plot-container" id="plot-{plot_counter}"></div>
            </div>
            {overall_plot_script}
            <div class="stats-tables-wrapper">
                <div id="conv-additional-stats-{plot_counter}" class="additional-stats-container">
                    {overall_conv_detail_stats}
                </div>
                <div id="all-subj-additional-stats-{plot_counter}" class="additional-stats-container" style="display:none;">
                    {overall_all_subj_detail_stats}
                </div>
            </div>
        </div>
    """

    # 추가 시각화 생성 - 전체 데이터 요약에 대한 추가 그래프
    additional_visualizations = create_advanced_visualizations(plot_counter, df_filtered)
    html_content += additional_visualizations

    # 선택된 필터 정보 표시 (옵션)
    filter_info = []
    if selected_univs:
        univ_count = len(selected_univs)
        univ_text = f"{univ_count}개 대학" if univ_count > 3 else ", ".join(selected_univs)
        filter_info.append(f"선택된 대학: {univ_text}")
    if selected_subtypes:
        subtype_count = len(selected_subtypes)
        subtype_text = f"{subtype_count}개 전형" if subtype_count > 3 else ", ".join(selected_subtypes)
        filter_info.append(f"선택된 전형: {subtype_text}")
    if selected_depts:
        dept_count = len(selected_depts)
        dept_text = f"{dept_count}개 모집단위" if dept_count > 3 else ", ".join(selected_depts)
        filter_info.append(f"선택된 모집단위: {dept_text}")

    if filter_info:
        filter_info_html = "<div class='filter-info-container'><h3>적용된 필터</h3><ul>"
        for info in filter_info:
            filter_info_html += f"<li>{info}</li>"
        filter_info_html += "</ul></div>"
        html_content += filter_info_html

    html_content += """
        </div>
    </div>
    """

    plot_counter += 1

    html_content += """
    <script>
    var currentGradeType = 'conv';
    var plotsInitialized = false;
    document.addEventListener('DOMContentLoaded', function() {
        console.log('페이지 초기화 시작...');
        var toc = document.getElementById('toc-content');
        var tocHTML = '';

        // 대학별 컨테이너 순회
        document.querySelectorAll('.dept-container').forEach(function(container) {
            var uniId = container.id;
            var uniHeader = container.querySelector('.dept-header');
            if (!uniHeader) return; // dept-header가 없는 경우 건너뛰기 (예: 전체 요약)
            var uniTitle = uniHeader.textContent;

            // '전체 데이터 요약'은 별도로 처리
            if (uniId === 'overall-summary') return;

            tocHTML += `<div class="toc-university" onclick="scrollToElement('${uniId}')">${uniTitle}</div>`;

            // 모집단위 컨테이너 찾기 (dept-container- 접두사로 시작하는 ID)
            container.querySelectorAll('[id^="dept-container-"]').forEach(function(deptContainer) {
                var deptHeader = deptContainer.querySelector('.subtype-header');
                if (deptHeader) {
                    var deptId = deptContainer.id;
                    var deptTitle = deptHeader.textContent.replace(/^\\d+\\)\\s*/, '').trim();

                    // 모집단위 추가
                    tocHTML += `<div class="toc-dept-item" style="margin-left: 18px; font-weight: bold; margin-top: 8px; color: #0056b3;">${deptTitle}</div>`;

                    // 전형 컨테이너 찾기
                    deptContainer.querySelectorAll('[id^="subtype-"]').forEach(function(subtypeContainer) {
                        var subtypeHeader = subtypeContainer.querySelector('.subtype-header');
                        if (subtypeHeader) {
                            var subtypeId = subtypeContainer.id;
                            var subtypeTitle = subtypeHeader.textContent.replace(/^\\d+\\)\\s*/, '').trim();

                            // 전형 추가
                            tocHTML += `<div class="toc-subtype-item" style="margin-left: 36px;" onclick="scrollToElement('${subtypeId}')">${subtypeTitle}</div>`;
                        }
                    });

                    // 모집단위 요약 추가
                    var deptSummaryId = deptId.replace('container', 'summary');
                    var deptSummaryElement = document.getElementById(deptSummaryId);
                    if (deptSummaryElement) {
                        var summaryHeader = deptSummaryElement.querySelector('.subtype-header');
                        if (summaryHeader && summaryHeader.textContent.includes('전체 전형 통합')) { // 정확한 요약 항목인지 확인
                            tocHTML += `<div class="toc-subtype-item" style="margin-left: 36px; font-style: italic;" onclick="scrollToElement('${deptSummaryId}')">전체 전형 통합</div>`;
                        }
                    }
                }
            });

            // 대학별 전형 요약 추가 (summary-container- 접두사로 시작하는 ID)
            var univSummaryId = `summary-container-${uniId.split('-')[1]}`;
            var summaryElement = document.getElementById(univSummaryId);
            if (summaryElement) {
                var summaryHeader = summaryElement.querySelector('.subtype-header'); // 전형별 요약 타이틀
                if (summaryHeader && summaryHeader.textContent.includes('전형별 요약')) {
                     tocHTML += `<div class="toc-subtype-item" style="margin-left: 18px; font-weight: bold; color: #2a4365; margin-top: 8px;" onclick="scrollToElement('${univSummaryId}')">${summaryHeader.textContent}</div>`;
                }
            }
        });

        // 전체 요약 섹션 목차에 추가
        var overallSummaryElem = document.getElementById('overall-summary');
        if (overallSummaryElem) {
            var overallHeader = overallSummaryElem.querySelector('.dept-header');
            if (overallHeader) {
                 tocHTML += `<div class="toc-university" onclick="scrollToElement('overall-summary')" style="margin-top: 20px; color: #e74c3c;">${overallHeader.textContent}</div>`;
            }
        }
        toc.innerHTML = tocHTML;
        initializeAllPlots();

    });

    function initializeAllPlots() {
        if (plotsInitialized || !window.Plotly) return;
        console.log('모든 플롯 초기화 중...');
        var plotContainers = document.querySelectorAll('.plot-container[id^="plot-"]');
        plotContainers.forEach(function(plotDiv) {
            var plotId = plotDiv.id;
            var numericId = plotId.split('-')[1];
            try {
                // 기본 박스플롯 처리
                if(plotId.startsWith('plot-')) {
                    if (!window.plotsData || !window.plotsData[numericId]) {
                        console.error('플롯 데이터를 찾을 수 없음:', numericId);
                        plotDiv.innerHTML = '<p style="text-align:center; color:red;">플롯 데이터 로드 실패</p>';
                        return;
                    }
                    var plotData = window.plotsData[numericId];
                    var traces = JSON.parse(JSON.stringify(plotData.convTraces)); // 기본으로 convTraces 사용
                    var layout = createPlotLayout();
                    Plotly.newPlot(plotDiv, traces, layout, {displayModeBar: false, responsive: true, useResizeHandler: true});
                }
                // 추가 시각화는 별도 함수로 처리됨 (donut-chart, histograms 등)
            } catch (error) {
                console.error(`플롯 ${numericId} 초기화 오류:`, error);
                plotDiv.innerHTML = `<p style="text-align:center; color:red;">플롯 생성 중 오류 발생: ${error.message}</p>`;
            }
        });
        plotsInitialized = true;
        console.log('모든 플롯 초기화 완료');
    }

    function createPlotLayout() {
        return {
            height: 300,
            autosize: true,
            margin: {t: 15, b: 50, l: 60, r: 30},
            bargap: 0.2,
            xaxis: {
                type: 'category',
                categoryorder: 'array',
                categoryarray: ['합격', '충원합격', '불합격'],
                showgrid: false,
                tickfont: { size: 14, weight: 'bold' }
            },
            yaxis: {
                visible: true,
                showgrid: true,
                gridcolor: [
                    '#e0e0e0', // 1등급 - 연한 그레이
                    '#b0b0b0', // 2등급 - 진한 그레이
                    '#e0e0e0', // 3등급 - 연한 그레이
                    '#b0b0b0', // 4등급 - 진한 그레이
                    '#e0e0e0', // 5등급 - 연한 그레이
                    '#b0b0b0', // 6등급 - 진한 그레이
                    '#e0e0e0', // 7등급 - 연한 그레이
                    '#b0b0b0', // 8등급 - 진한 그레이
                    '#e0e0e0'  // 9등급 - 연한 그레이
                ],
                gridwidth: [
                    0.5, // 1등급 - 얇은 선
                    1.0, // 2등급 - 굵은 선
                    0.5, // 3등급 - 얇은 선
                    1.0, // 4등급 - 굵은 선
                    0.5, // 5등급 - 얇은 선
                    1.0, // 6등급 - 굵은 선
                    0.5, // 7등급 - 얇은 선
                    1.0, // 8등급 - 굵은 선
                    0.5  // 9등급 - 얇은 선
                ],
                griddash: [
                    'dot', // 1등급 - 점선
                    'solid', // 2등급 - 실선
                    'dot', // 3등급 - 점선
                    'solid', // 4등급 - 실선
                    'dot', // 5등급 - 점선
                    'solid', // 6등급 - 실선
                    'dot', // 7등급 - 점선
                    'solid', // 8등급 - 실선
                    'dot'  // 9등급 - 점선
                ],
                range: [9.5, 0.5], // Y-axis range for grades (1 at top, 9 at bottom)
                title: { text: '등급', font: { size: 13, color: '#333' }},
                autorange: false,
                tickmode: 'array', // Use explicit tick values
                tickvals: [1, 2, 3, 4, 5, 6, 7, 8, 9], // Values for the ticks
                ticktext: ['1', '2', '3', '4', '5', '6', '7', '8', '9'], // Text labels for the ticks
                tickfont: {
                    size: 11, // Base size for tick labels
                    color: [ // Array of colors for tick labels
                        '#7f7f7f', // Tick 1 (lighter grey)
                        '#333333', // Tick 2 (darker grey/black)
                        '#7f7f7f', // Tick 3 (lighter grey)
                        '#333333', // Tick 4 (darker grey/black)
                        '#7f7f7f', // Tick 5 (lighter grey)
                        '#333333', // Tick 6 (darker grey/black)
                        '#7f7f7f', // Tick 7 (lighter grey)
                        '#333333', // Tick 8 (darker grey/black)
                        '#7f7f7f'  // Tick 9 (lighter grey)
                    ]
                }
            },
            plot_bgcolor: "white",
            paper_bgcolor: "white",
            showlegend: false,
            boxmode: 'overlay'
        };
    }

    function switchGradeType(gradeType) {
        if (currentGradeType === gradeType || !window.Plotly) return;
        console.log("등급 전환: " + gradeType);
        currentGradeType = gradeType;
        document.getElementById('btn-conv-grade').classList.toggle('active', gradeType === 'conv');
        document.getElementById('btn-all-subj-grade').classList.toggle('active', gradeType === 'all_subj');
        document.getElementById('grade-type-label').textContent = gradeType === 'conv' ? '환산등급' : '전교과100 등급';

        var overallSummaryPlotId = null;
        var overallSummaryContainer = document.getElementById('overall-summary');
        if (overallSummaryContainer) {
            var plotContainer = overallSummaryContainer.querySelector('.plot-container[id^="plot-"]');
            if (plotContainer) {
                overallSummaryPlotId = plotContainer.id.split('-')[1];
            }
        }


        updateAllPlots(gradeType); // 먼저 박스플롯들을 업데이트
        
        // 통계 정보 및 상세 통계 테이블 가시성 업데이트
        document.querySelectorAll('.plot-stats-wrapper').forEach(function(wrapper) {
            var plotId = wrapper.querySelector('.plot-container[id^="plot-"]').id.split('-')[1];
            
            var convStatsElem = document.getElementById('conv-stats-' + plotId);
            var allSubjStatsElem = document.getElementById('all-subj-stats-' + plotId);
            var convAddStatsElem = document.getElementById('conv-additional-stats-' + plotId);
            var allSubjAddStatsElem = document.getElementById('all-subj-additional-stats-' + plotId);

            if (convStatsElem) convStatsElem.style.display = (gradeType === 'conv') ? 'flex' : 'none';
            if (allSubjStatsElem) allSubjStatsElem.style.display = (gradeType === 'all_subj') ? 'flex' : 'none';
            if (convAddStatsElem) convAddStatsElem.style.display = (gradeType === 'conv') ? 'block' : 'none';
            if (allSubjAddStatsElem) allSubjAddStatsElem.style.display = (gradeType === 'all_subj') ? 'block' : 'none';
        });
        
        // 전체 데이터 요약 섹션의 히스토그램 가시성 업데이트
        if (overallSummaryPlotId) {
            var convHistogram = document.getElementById('conv-grade-histogram-' + overallSummaryPlotId);
            var allSubjHistogram = document.getElementById('all-subj-grade-histogram-' + overallSummaryPlotId);
            
            if (convHistogram) convHistogram.style.display = (gradeType === 'conv') ? 'block' : 'none';
            if (allSubjHistogram) allSubjHistogram.style.display = (gradeType === 'all_subj') ? 'block' : 'none';
        }
    }

    function updateAllPlots(gradeType) {
        console.log('모든 플롯 업데이트 중... 타입:', gradeType);
        var plotContainers = document.querySelectorAll('.plot-container[id^="plot-"]');
        plotContainers.forEach(function(plotDiv) {
            var plotId = plotDiv.id;
            var numericId = plotId.split('-')[1]; // plot-container의 ID에서 숫자 부분 추출
            try {
                if (!window.plotsData || !window.plotsData[numericId]) {
                    console.error('플롯 데이터를 찾을 수 없음 (update):', numericId);
                    return;
                }
                var plotData = window.plotsData[numericId];
                var traces;
                if (gradeType === 'conv') {
                    traces = JSON.parse(JSON.stringify(plotData.convTraces));
                } else {
                    traces = JSON.parse(JSON.stringify(plotData.allSubjTraces));
                }
                var layout = createPlotLayout();
                Plotly.react(plotDiv, traces, layout, {displayModeBar: false, responsive: true, useResizeHandler: true});
            } catch (error) {
                console.error(`플롯 ${numericId} 업데이트 오류:`, error);
                // plotDiv.innerHTML = `<p style="text-align:center; color:red;">플롯 업데이트 중 오류 발생: ${error.message}</p>`;
            }
        });
        console.log('모든 플롯 업데이트 완료');
    }

    function scrollToElement(id) {
        var el = document.getElementById(id);
        if (el) {
            var headerHeight = document.querySelector('.fixed-header').offsetHeight;
            var elementPosition = el.getBoundingClientRect().top + window.pageYOffset;
            var offsetPosition = elementPosition - headerHeight - 20; // 20px 추가 여백
            window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
            // 하이라이트 효과 (선택 사항)
            el.style.transition = 'background-color 0.5s ease-out';
            el.style.backgroundColor = 'rgba(255, 223, 186, 0.5)'; // 연한 주황색 하이라이트
            setTimeout(function() { el.style.backgroundColor = ''; }, 1500); // 1.5초 후 원래대로
        }
    }
    </script>
    """
    html_content += """
            </main>
        </div>
    </body>
    </html>
    """

    output_path = out_dir / output_file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return f"{output_path.resolve()} 파일이 생성되었습니다."
    except Exception as e:
        return f"파일 저장 중 오류 발생: {e}"