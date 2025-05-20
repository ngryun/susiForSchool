import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import webbrowser
from pathlib import Path

import pandas as pd  # used only for typing hints, not strictly required

from filter_widgets import MultiSelectFilter
from data_processor import read_input
from html_generator import plot_selected_depts
from utils import sanitize


class DepartmentSelector(tk.Tk):
    """주요 흐름
    1) 엑셀을 로드하면 DataFrame(self.df)이 채워진다.
    2) 그 시점에 3‑중 MultiSelectFilter(UI)가 생성된다.
    3) 필터 변화 → _on_filter_change → 그래프 / HTML 재생성.  
       (render_plots(df) 함수를 이미 갖고 계시다면 그대로 호출하세요.)
    """

    # ------------------------------------------------------------
    # ▶ 초기화
    # ------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()

        self.title("모집단위 입시 결과 시각화 프로그램")
        self.geometry("950x650")
        self.minsize(900, 600)

        # DataFrame 자리
        self.df: pd.DataFrame | None = None

        # 출력 디렉터리
        self.output_dir = Path("output_htmls")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 기본 스타일
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # UI 구성 (필터 UI는 엑셀 로드 후 생성)
        self._build_base_widgets()

        # 창 가운데 정렬
        self._center_window()

    # ------------------------------------------------------------
    # ▶ 베이스 위젯 (파일 선택, 상태바 등)
    # ------------------------------------------------------------
    def _build_base_widgets(self) -> None:
        self.main_frame = ttk.Frame(self, padding=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # ── 입력 파일 선택 ───────────────────────────────────
        top_frame = ttk.LabelFrame(self.main_frame, text="입력 파일 선택", padding=10)
        top_frame.pack(fill=tk.X, pady=(0, 15))

        self.file_path_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.file_path_var, width=60).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10)
        )
        ttk.Button(top_frame, text="파일 찾아보기", command=self._browse_file).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(top_frame, text="데이터 로드", command=self._load_file).pack(side=tk.LEFT)

        # ── 필터 영역 placeholder (엑셀 로드 후 build_filters) ──
        self.filter_container = ttk.Frame(self.main_frame)
        self.filter_container.pack(fill=tk.BOTH, expand=True)
        self._placeholder_lbl = ttk.Label(
            self.filter_container,
            text="엑셀 파일을 먼저 로드해 주세요.",
            anchor="center",
            font=("Helvetica", 12, "italic"),
        )
        self._placeholder_lbl.pack(fill=tk.BOTH, expand=True)

        # ── 출력 파일 설정 + 생성 버튼 ─────────────────────────
        bottom_frame = ttk.Frame(self.main_frame)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Label(bottom_frame, text="출력 HTML 파일명:").pack(side=tk.LEFT)
        self.filename_var = tk.StringVar(value="선택된_모집단위_입시결과.html")
        ttk.Entry(bottom_frame, textvariable=self.filename_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=5
        )
        ttk.Button(
            bottom_frame,
            text="HTML 보고서 생성",
            command=self._generate_html,
            style="Accent.TButton",
        ).pack(side=tk.RIGHT)

        # 스타일 맵
        self.style.configure("Accent.TButton", font=("Helvetica", 10, "bold"), foreground="white")
        try:
            self.style.map(
                "Accent.TButton",
                background=[("active", "#0056b3"), ("!disabled", "#007bff")],
            )
        except tk.TclError:
            self.style.configure("Accent.TButton", background="#007bff")

        # 상태바
        self.status_var = tk.StringVar(value="엑셀 파일을 로드하고 분석할 필터를 선택하세요.")
        ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5).pack(
            fill=tk.X, side=tk.BOTTOM
        )

    # ------------------------------------------------------------
    # ▶ 창 가운데 배치
    # ------------------------------------------------------------
    def _center_window(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

    # ------------------------------------------------------------
    # ▶ MultiSelectFilter 3종 생성
    # ------------------------------------------------------------
    def _build_filters(self) -> None:
        # placeholder 제거
        if self._placeholder_lbl.winfo_exists():
            self._placeholder_lbl.destroy()

        # 이전 필터 프레임이 있다면 제거
        for child in self.filter_container.winfo_children():
            child.destroy()

        filter_frame = ttk.Frame(self.filter_container)
        filter_frame.pack(fill=tk.BOTH, expand=True)

        self.univ_filter = MultiSelectFilter(filter_frame, self.df, "univ", label="대학", callback=self._on_filter_change)
        self.subtype_filter = MultiSelectFilter(filter_frame, self.df, "subtype", label="전형", callback=self._on_filter_change)
        self.dept_filter = MultiSelectFilter(filter_frame, self.df, "dept", label="모집단위", callback=self._on_filter_change)

        for col, widget in enumerate((self.univ_filter, self.subtype_filter, self.dept_filter)):
            widget.grid(row=0, column=col, sticky="nsew", padx=5)
            filter_frame.columnconfigure(col, weight=1)

    # ------------------------------------------------------------
    # ▶ 파일 다이얼로그
    # ------------------------------------------------------------
    def _browse_file(self) -> None:
        file_path = filedialog.askopenfilename(title="입시 결과 엑셀 파일 선택", filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_path_var.set(file_path)
            self.status_var.set(f"선택된 파일: {Path(file_path).name}")

    # ------------------------------------------------------------
    # ▶ 엑셀 로드 (스레드)
    # ------------------------------------------------------------
    def _load_file(self) -> None:
        file_path = self.file_path_var.get().strip()
        if not file_path:
            messagebox.showerror("오류", "먼저 엑셀 파일을 선택해주세요.")
            return
        if not Path(file_path).exists():
            messagebox.showerror("오류", f"파일을 찾을 수 없습니다: {file_path}")
            return

        # UI 잠금
        self._set_widgets_state(tk.DISABLED)
        self.status_var.set("데이터 로드 중...")

        threading.Thread(target=self._load_file_thread, args=(file_path,), daemon=True).start()

    def _load_file_thread(self, file_path: str) -> None:
        try:
            df = read_input(Path(file_path))
            self.df = df
            self.after(0, self._build_filters)
            self.after(0, lambda: self.status_var.set("데이터 로드 완료. 필터를 선택하세요."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("오류", f"파일 로드 실패: {e}"))
            self.after(0, lambda: self.status_var.set("데이터 로드 실패."))
        finally:
            self.after(0, lambda: self._set_widgets_state(tk.NORMAL))

    # ------------------------------------------------------------
    # ▶ 필터 변경 → 그래프 / HTML 재렌더
    # ------------------------------------------------------------

    def _on_filter_change(self) -> None:
        if self.df is None:
            return

        # 현재 선택된 필터 값 가져오기
        univs = self.univ_filter.get_selected()
        subs = self.subtype_filter.get_selected()
        depts = self.dept_filter.get_selected()

        # 기본 데이터프레임 복사
        filtered_df = self.df.copy()
        
        # 필터링을 위한 임시 데이터프레임 (각 필터에 적용할 데이터)
        univ_filter_df = self.df.copy()
        subtype_filter_df = self.df.copy()
        dept_filter_df = self.df.copy()
        
        # 선택된 필터 적용 - 결과 확인용
        if univs:
            filtered_df = filtered_df[filtered_df["univ"].isin(univs)]
            subtype_filter_df = subtype_filter_df[subtype_filter_df["univ"].isin(univs)]
            dept_filter_df = dept_filter_df[dept_filter_df["univ"].isin(univs)]
        
        if subs:
            filtered_df = filtered_df[filtered_df["subtype"].isin(subs)]
            univ_filter_df = univ_filter_df[univ_filter_df["subtype"].isin(subs)]
            dept_filter_df = dept_filter_df[dept_filter_df["subtype"].isin(subs)]
        
        if depts:
            filtered_df = filtered_df[filtered_df["dept"].isin(depts)]
            univ_filter_df = univ_filter_df[univ_filter_df["dept"].isin(depts)]
            subtype_filter_df = subtype_filter_df[subtype_filter_df["dept"].isin(depts)]

        # 각 필터 항목 업데이트
        self.univ_filter.refresh(univ_filter_df["univ"].unique())
        self.subtype_filter.refresh(subtype_filter_df["subtype"].unique())
        self.dept_filter.refresh(dept_filter_df["dept"].unique())

        # 필요하다면 그래프 즉시 렌더
        if not filtered_df.empty and hasattr(self, "render_plots"):
            self.render_plots(filtered_df)

    # ------------------------------------------------------------
    # ▶ HTML 보고서 생성
    # ------------------------------------------------------------
    def _generate_html(self) -> None:
        if self.df is None:
            messagebox.showerror("오류", "먼저 데이터를 로드해주세요.")
            return

        selected_depts = self.dept_filter.get_selected() or None
        selected_univs = self.univ_filter.get_selected() or None
        selected_subtypes = self.subtype_filter.get_selected() or None

        if not any([selected_depts, selected_univs, selected_subtypes]):
            messagebox.showerror("오류", "대학, 전형 또는 모집단위를 하나 이상 선택해주세요.")
            return

        filename = self.filename_var.get().strip()
        if not filename:
            messagebox.showerror("오류", "출력 파일명을 입력해주세요.")
            return
        if not filename.lower().endswith(".html"):
            filename += ".html"
        filename = sanitize(filename)
        self.filename_var.set(filename)

        output_path = self.output_dir / filename

        # 진행 다이얼로그
        prog_win = tk.Toplevel(self)
        prog_win.title("보고서 생성 중")
        prog_win.resizable(False, False)
        prog_win.transient(self)
        prog_win.grab_set()
        ttk.Label(prog_win, text="HTML 보고서를 생성 중입니다…").pack(padx=15, pady=15)
        bar = ttk.Progressbar(prog_win, mode="indeterminate", length=250)
        bar.pack(pady=(0, 15))
        bar.start(10)

        def worker():
            try:
                msg = plot_selected_depts(self.df, self.output_dir, selected_depts, selected_univs, selected_subtypes, filename)
                self.after(0, lambda: self._on_html_done(msg, output_path, prog_win))
            except Exception as e:
                self.after(0, lambda: self._on_html_error(e, prog_win))

        threading.Thread(target=worker, daemon=True).start()

    def _on_html_done(self, msg: str, output_path: Path, win: tk.Toplevel) -> None:
        if win.winfo_exists():
            win.destroy()
        messagebox.showinfo("생성 완료", msg)
        self.status_var.set(f"보고서 생성 완료: {output_path.name}")
        if messagebox.askyesno("보고서 열기", "생성된 보고서를 열어보시겠습니까?"):
            webbrowser.open(output_path.resolve().as_uri())

    def _on_html_error(self, err: Exception, win: tk.Toplevel) -> None:
        if win.winfo_exists():
            win.destroy()
        messagebox.showerror("오류", f"HTML 생성 실패: {err}")
        self.status_var.set("HTML 보고서 생성 실패")

    # ------------------------------------------------------------
    # ▶ 유틸 : 위젯 상태 잠금/해제
    # ------------------------------------------------------------
    def _set_widgets_state(self, state: str) -> None:
        for child in self.main_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Button, ttk.Entry)):
                    widget.configure(state=state)


# ------------------------------------------------------------
# ▶ 실행
# ------------------------------------------------------------
if __name__ == "__main__":
    try:
        from ctypes import windll  # type: ignore
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # non‑Windows

    app = DepartmentSelector()
    app.mainloop()
