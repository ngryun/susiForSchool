# University Admission Filter

This project is a Tkinter application for filtering and visualizing university admission data. It lets you load an Excel file, choose universities, application types and departments, and then generate an HTML report showing statistics and plots.

## Installation
1. Ensure Python 3.11 or later is installed.
2. Install the required packages:
   ```bash
   pip install pandas numpy openpyxl xlrd plotly
   ```
   * `pandas` and `numpy` are used for data handling.
   * `openpyxl` or `xlrd` are required to read Excel files.
   * `plotly` generates interactive charts in the HTML report.

## Running the application
Run the main script from the project root:
```bash
python main.py
```
This starts the GUI. Load your Excel file, choose filters and click **HTML 보고서 생성** to create a report. Reports are saved to the `output_htmls` folder.

