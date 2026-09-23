from decisionlab.bi.cohort import build_cohorts, load_rows, month_add, month_diff, month_key


def test_month_helpers():
    assert month_key("2025-04-17T09:31:00Z") == "2025-04"
    assert month_add("2025-11", 3) == "2026-02"
    assert month_diff("2025-11", "2026-02") == 3


def test_messy_file_reports_problems_instead_of_crashing(tmp_path):
    path = tmp_path / "messy.csv"
    path.write_text(
        "customer_id,order_date,revenue\n"
        'C1,2025-01-05T10:00:00Z,"1,200"\n'
        "C1,2025-03-02,500\n"
        "C2,notadate,50\n"
        "C3,,10\n"
    )
    rows, problems, has_revenue = load_rows(str(path), "customer_id", "order_date", "revenue")
    assert has_revenue
    assert len(rows) == 2
    assert rows[0][2] == 1200.0
    assert len(problems) == 2


def test_unreached_months_are_not_counted_as_zero(tmp_path):
    rows = [("A", "2025-01", 0), ("A", "2025-02", 0), ("B", "2025-02", 0)]
    cohorts, sizes, grid, last = build_cohorts(rows, "customers", periods=2)
    assert last == "2025-02"
    assert sizes == {"2025-01": 1, "2025-02": 1}
    # B's cohort started in February, so its month 1 is March, which the data never reached.
    assert month_add("2025-02", 1) > last
    assert grid[("2025-01", 1)] == 1


def test_impossible_and_future_dates_are_reported_not_trusted(tmp_path):
    path = tmp_path / "typos.csv"
    path.write_text(
        "customer_id,order_date\n"
        "C1,2025-01-05\n"
        "C2,2025-02-31\n"
        "C3,2205-01-01\n"
    )
    rows, problems, _ = load_rows(str(path), "customer_id", "order_date", "revenue")
    assert [r[1] for r in rows] == ["2025-01"]
    assert len(problems) == 2
    # The typo'd year must not become the table's last month, which would stop blanking.
    _, _, _, last = build_cohorts(rows, "customers", periods=2)
    assert last == "2025-01"


def test_cli_rejects_negative_periods():
    from decisionlab.cli import main
    assert main(["cohort", "--demo", "--periods", "-1"]) == 2


def test_dates_without_zero_padding_are_read():
    assert month_key("2025-4-7") == "2025-04"
    assert month_key("2025-04-17 09:31") == "2025-04"
