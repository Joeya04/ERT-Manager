#Controls workflow of all modules needed for the app


def run_analysis(filepath):
    """Parse the uploaded workbook and return a dataframe plus a lightweight report."""

    try:
        from formatter.ERT_date_puller_shiny import parse_ert_workbook

        df = parse_ert_workbook(filepath)
        report = {"status": "parsed", "source": "ERT_date_puller_shiny"}
    except Exception as exc:
        import pandas as pd

        if filepath.endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.DataFrame()

        report = {"status": "fallback", "error": str(exc)}

    return {
        "data": df,
        "statistics": report
    }

