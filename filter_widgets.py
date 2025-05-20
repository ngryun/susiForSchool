# filter_widgets.py
# ---------------------------------------------------------------------
# Tkinter용 범용 다중-선택 필터 위젯 (검색 + 모두선택/비우기 + 선택콜백)
# ---------------------------------------------------------------------
import tkinter as tk
from tkinter import ttk
from typing import Iterable, Callable, Optional

class MultiSelectFilter(ttk.Frame):
    """
    공통 다중-선택 필터 위젯

    Parameters
    ----------
    master : tk widget
    df : pandas.DataFrame           # 전체 데이터 (후보 목록 계산용)
    column : str                    # df 컬럼명 – 이 필터가 담당할 열
    label : str, optional           # 위젯 상단 라벨
    height : int, optional          # Listbox 표시 행 수
    callback : callable, optional   # 선택 변경 시 호출 함수
    """
    def __init__(
        self,
        master,
        df,
        column: str,
        *,
        label: str = "선택",
        height: int = 14,
        callback: Optional[Callable] = None,
    ):
        super().__init__(master)
        self.df, self.column, self.callback = df, column, callback

        # ── 타이틀 ──────────────────────────────────────────────
        ttk.Label(self, text=label, font=("Pretendard", 10, "bold")).pack(anchor="w")

        # ── 검색창 ──────────────────────────────────────────────
        top = ttk.Frame(self); top.pack(fill="x", pady=4)

        self._q = tk.StringVar()
        ttk.Entry(top, textvariable=self._q).pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="🔄", width=3, command=self._clear_search).pack(side="right")

        # ── Listbox + 스크롤바 ─────────────────────────────────
        body = ttk.Frame(self); body.pack(fill="both", expand=True)

        self._lb = tk.Listbox(
            body, selectmode=tk.MULTIPLE, height=height, exportselection=False
        )
        self._lb.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(body, orient="vertical", command=self._lb.yview)
        sb.pack(side="right", fill="y")
        self._lb.configure(yscrollcommand=sb.set)

        # ── 퀵-액션 버튼 ────────────────────────────────────────
        bottom = ttk.Frame(self); bottom.pack(fill="x", pady=2)
        ttk.Button(bottom, text="모두 선택", command=self._select_all).pack(side="left")
        ttk.Button(bottom, text="비우기", command=self._clear_all).pack(side="right")

        # ── 이벤트 바인딩 ──────────────────────────────────────
        self._q.trace_add("write", lambda *_: self.refresh())
        self._lb.bind("<<ListboxSelect>>", lambda _: self._fire())

        # 최초 후보 세팅
        self.refresh()

    # ───────────────────────── 공개 메서드 ──────────────────────────
    def get_selected(self) -> list[str]:
        """현재 선택된 항목 리스트 반환"""
        return [self._lb.get(i) for i in self._lb.curselection()]
    
    def refresh(self, candidates: Optional[Iterable[str]] = None) -> None:
        """후보 목록을 갱신한다. 이전 선택은 가능한 유지한다."""
        # 현재 선택된 항목들을 저장
        currently_selected = set(self.get_selected())
        
        items = (
            sorted(set(candidates))
            if candidates is not None
            else sorted(self.df[self.column].dropna().unique())
        )
        q = self._q.get().lower().strip()

        # Listbox 내용 갱신
        self._lb.delete(0, tk.END)
        
        # 검색어에 맞는 항목만 표시
        filtered_items = []
        for item in items:
            if not q or q in str(item).lower():
                self._lb.insert(tk.END, item)
                filtered_items.append(item)
                # 이전에 선택되었던 항목이면 다시 선택
                if item in currently_selected:
                    self._lb.selection_set(tk.END)
    # ──────────────────────── 내부 유틸 ───────────────────────────
    def _fire(self):
        if callable(self.callback):
            self.callback()

    def _clear_search(self):
        self._q.set("")

    def _select_all(self):
        self._lb.select_set(0, tk.END)
        self._fire()

    def _clear_all(self):
        self._lb.selection_clear(0, tk.END)
        self._fire()
