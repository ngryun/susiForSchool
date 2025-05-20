import pandas as pd
import numpy as np
import json
from pathlib import Path

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super(NumpyEncoder, self).default(obj)

# 추가 통계 정보 계산 함수 (기존 코드 유지)
def compute_additional_stats(data, grade_column):
    """
    추가 통계 정보(표준편차, 변동계수, 최솟값, 최댓값 등) 계산
    """
    stats = {}

    # 결과별 통계 계산
    for result_key in ["합격", "불합격", "충원합격"]:
        result_data = data[data['result'] == result_key][grade_column].dropna()
        if len(result_data) > 0: # 데이터가 있을 때만 통계 계산
            stats[result_key] = {
                'count': len(result_data),
                'mean': result_data.mean(),
                'std': result_data.std(),
                'cv': (result_data.std() / result_data.mean()) * 100 if result_data.mean() != 0 else 0,  # 변동계수 (%)
                'min': result_data.min(),
                'max': result_data.max(),
                'median': result_data.median(),
                'q1': result_data.quantile(0.25),
                'q3': result_data.quantile(0.75)
            }
        else: # 데이터가 없는 경우 count만 0으로 설정하고 나머지는 N/A 처리 준비 (또는 빈 dict)
             stats[result_key] = {'count': 0}

    return stats

def read_input(path: Path) -> pd.DataFrame:
    """
    엑셀 파일을 읽어서 필요한 열만 추출하고 전처리합니다.
    성능 최적화: 필요한 열만 로드하여 메모리 사용 최소화
    """
    try:
        engine = "openpyxl" if str(path).lower().endswith(".xlsx") else "xlrd"
        df = pd.read_excel(
            path,
            header=None,
            skiprows=2,
            usecols="F,L,J,R,U,AE",
            engine=engine,
        )
        
        df.columns = ["univ", "subtype", "dept", "conv_grade", "result", "all_subj_grade"]
        df["result"] = df["result"].astype(str).str.strip()
        df["conv_grade"] = pd.to_numeric(df["conv_grade"], errors="coerce")
        df["all_subj_grade"] = pd.to_numeric(df["all_subj_grade"], errors="coerce")
        rows_before = len(df)
        df = df.dropna(subset=["result", "univ", "dept", "subtype"])
        rows_after = len(df)
        if rows_before > rows_after:
            print(f"경고: {rows_before - rows_after}개 행이 필수 정보 누락으로 제외됨")
        rows_before = len(df)
        df = df[(~df["conv_grade"].isna()) | (~df["all_subj_grade"].isna())]
        rows_after = len(df)
        if rows_before > rows_after:
            print(f"경고: {rows_before - rows_after}개 행이 등급 정보 누락으로 제외됨")
        df = df.reset_index(drop=True)
        return df
    except Exception as e:
        print(f"파일 읽기 오류: {e}")
        raise

# 그룹별 통계 계산 함수 (기존 코드 유지)
def compute_stats(group_data: pd.DataFrame, grade_column: str = "conv_grade") -> dict:
    """
    그룹별 통계 정보 계산 - 충원합격 포함
    grade_column: 사용할 등급 열 이름 ("conv_grade" 또는 "all_subj_grade")
    """
    stats = {}
    total_count = len(group_data)
    stats['total_count'] = total_count
    if total_count == 0:
        return stats

    result_counts = group_data['result'].value_counts()
    pass_data = group_data[group_data['result'].isin(['합격', '충원합격'])]
    if not pass_data.empty:
        all_pass_count = len(pass_data)
        stats['all_pass_count'] = all_pass_count
        stats['all_pass_rate'] = f"{all_pass_count/total_count*100:.1f}%" if total_count > 0 else "0.0%"
        valid_grades = pass_data[grade_column].dropna()
        if not valid_grades.empty:
            stats['all_pass_min'] = valid_grades.min()
            stats['all_pass_max'] = valid_grades.max()
            stats['all_pass_mean'] = valid_grades.mean()

    if '합격' in result_counts:
        pass_count = result_counts['합격']
        stats['pass_count'] = pass_count
        stats['pass_rate'] = f"{pass_count/total_count*100:.1f}%" if total_count > 0 else "0.0%"
        pass_grades = group_data[group_data['result'] == '합격'][grade_column].dropna()
        if not pass_grades.empty:
            stats['pass_min'] = pass_grades.min()
            stats['pass_max'] = pass_grades.max()
            stats['pass_mean'] = pass_grades.mean()

    if '충원합격' in result_counts:
        waitlist_count = result_counts['충원합격']
        stats['waitlist_count'] = waitlist_count
        stats['waitlist_rate'] = f"{waitlist_count/total_count*100:.1f}%" if total_count > 0 else "0.0%"
        waitlist_grades = group_data[group_data['result'] == '충원합격'][grade_column].dropna()
        if not waitlist_grades.empty:
            stats['waitlist_min'] = waitlist_grades.min()
            stats['waitlist_max'] = waitlist_grades.max()
            stats['waitlist_mean'] = waitlist_grades.mean()

    if '불합격' in result_counts:
        stats['fail_count'] = result_counts['불합격']
    return stats
