import pandas as pd


def test_read_excel(path) -> tuple:
    xl = pd.ExcelFile(path)
    sheet_names = xl.sheet_names
    dfs = {name: xl.parse(name, index_col=[1, 0]) for name in sheet_names}
    return sheet_names, dfs
