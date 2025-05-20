"""HTML template helper functions for admissions reports."""

from __future__ import annotations

from typing import Dict, Iterable


def create_additional_stats_html(
    stats: Dict[str, Dict[str, float]],
    grade_type: str,
    result_order: Iterable[str] = ("합격", "충원합격", "불합격"),
) -> str:
    """Return an HTML table summarizing additional statistics."""
    if not stats:
        return "<div class='no-stats'>통계 데이터가 없습니다.</div>"

    headers = [
        "결과",
        "데이터 수",
        "평균",
        "표준편차",
        "중앙값",
        "최댓값",
        "최솟값",
        "Q1-Q3 범위",
    ]

    html_output = [
        f"<div class='stats-detail-title'>{grade_type} 상세 통계</div>",
        "<table class='stats-table'><thead><tr>",
    ]
    html_output.extend(f"<th>{h}</th>" for h in headers)
    html_output.append("</tr></thead><tbody>")

    for result_key_name in result_order:
        if result_key_name not in stats or stats[result_key_name].get("count", 0) == 0:
            if result_key_name not in stats:
                continue
            num_cols = len(headers)
            html_output.append(
                f"<tr><td>{result_key_name}</td><td colspan='{num_cols - 1}' style='text-align:center;'>데이터 없음</td></tr>"
            )
            continue

        result_stats = stats[result_key_name]
        color_class = ""
        if result_key_name == "합격":
            color_class = "pass-row"
        elif result_key_name == "불합격":
            color_class = "fail-row"
        elif result_key_name == "충원합격":
            color_class = "waitlist-row"

        def fmt(v: float | None) -> str:
            return f"{v:.2f}" if isinstance(v, (int, float)) else "N/A"

        q1, q3 = result_stats.get("q1"), result_stats.get("q3")
        q_range = (
            f"{q1:.2f} - {q3:.2f}" if isinstance(q1, (int, float)) and isinstance(q3, (int, float)) else "N/A"
        )

        html_output.append(
            f"<tr class='{color_class}'>"
            f"<td>{result_key_name}</td>"
            f"<td>{result_stats['count']}명</td>"
            f"<td>{fmt(result_stats.get('mean'))}</td>"
            f"<td>{fmt(result_stats.get('std'))}</td>"
            f"<td>{fmt(result_stats.get('median'))}</td>"
            f"<td>{fmt(result_stats.get('max'))}</td>"
            f"<td>{fmt(result_stats.get('min'))}</td>"
            f"<td>{q_range}</td>"
            "</tr>"
        )

    html_output.append("</tbody></table>")
    return "\n".join(html_output)


def create_stats_html(stats: Dict[str, float]) -> str:
    """Return simple statistic badges as a HTML fragment."""
    sc: list[str] = []
    sc.append(f"<div class='stats-item stats-total'>총 {stats.get('total_count', 0)}명</div>")
    if "all_pass_count" in stats:
        pr = stats["all_pass_rate"].rstrip("%")
        sc.append(
            f"<div class='stats-item stats-pass'>합격(전체): {stats['all_pass_count']}명 <span class='highlight-rate'>({pr}%)</span>"
        )
        if all(k in stats for k in ("all_pass_min", "all_pass_max", "all_pass_mean")):
            sc.append(
                f"<span class='highlight-range'>등급 {stats['all_pass_min']:.1f}~{stats['all_pass_max']:.1f}</span>, <span class='highlight-mean'>평균 {stats['all_pass_mean']:.2f}</span>"
            )
        sc.append("</div>")
    if "pass_count" in stats:
        pr = stats.get("pass_rate", "0.0%").rstrip("%")
        sc.append(
            f"<div class='stats-item stats-pass'>합격(일반): {stats['pass_count']}명 <span class='highlight-rate'>({pr}%)</span></div>"
        )
    if "waitlist_count" in stats:
        wr = stats.get("waitlist_rate", "0.0%").rstrip("%")
        sc.append(
            f"<div class='stats-item stats-wait'>합격(충원): {stats['waitlist_count']}명 <span class='highlight-rate'>({wr}%)</span></div>"
        )
    if "fail_count" in stats:
        fc = stats["fail_count"]
        tc = stats.get("total_count", 1) or 1
        sc.append(
            f"<div class='stats-item stats-fail'>불합격: {fc}명 <span class='highlight-fail-rate'>({fc/tc*100:.1f}%)</span></div>"
        )
    return "".join(sc)
