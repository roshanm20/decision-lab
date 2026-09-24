import pytest

from decisionlab.product.rice import Item, fragility, load_items, rank


def write(tmp_path, text):
    path = tmp_path / "backlog.csv"
    path.write_text(text)
    return str(path)


def test_score_and_order(tmp_path):
    items = load_items(write(tmp_path, "name,reach,impact,confidence,effort\nA,100,1,50,1\nB,100,2,100,1\n"))
    assert [i.name for i in rank(items)] == ["B", "A"]
    assert rank(items)[0].score == 200


def test_confidence_accepts_percent_or_fraction(tmp_path):
    items = load_items(write(tmp_path, "name,reach,impact,confidence,effort\nA,10,1,80,1\nB,10,1,0.8,1\n"))
    assert items[0].confidence == items[1].confidence == 0.8


def test_example_file_marks_dark_mode_fragile():
    items = load_items("examples/rice_backlog.csv")
    assert fragility(items) == {"Dark mode": 2}


def test_fragility_restores_confidence():
    items = [Item("A", 100, 1, 0.9, 1), Item("B", 80, 1, 0.9, 1)]
    fragility(items)
    assert [i.confidence for i in items] == [0.9, 0.9]


def test_warnings(tmp_path):
    items = load_items(write(tmp_path, "name,reach,impact,confidence,effort\nA,10,5,99,1\n"))
    joined = " ".join(items[0].warnings)
    assert "off the 3/2/1" in joined and "rarely earned" in joined


@pytest.mark.parametrize("csv_text", [
    "name,reach,impact,confidence,effort\nA,10,1,50,0\n",
    "name,reach,impact,confidence,effort\nA,ten,1,50,1\n",
    "name,reach,impact,effort\nA,10,1,1\n",
    "name,reach,impact,confidence,effort\n",
])
def test_bad_files_raise(tmp_path, csv_text):
    with pytest.raises(ValueError):
        load_items(write(tmp_path, csv_text))


@pytest.mark.parametrize("row", [
    "A,10,1,50,nan", "A,10,1,-50,1", "A,10,-1,50,1", "A,10,1,50,inf",
])
def test_nonsense_values_are_refused(tmp_path, row):
    with pytest.raises(ValueError):
        load_items(write(tmp_path, "name,reach,impact,confidence,effort\n" + row + "\n"))


def test_duplicate_names_are_refused(tmp_path):
    with pytest.raises(ValueError, match="appears twice"):
        load_items(write(tmp_path, "name,reach,impact,confidence,effort\nA,10,1,50,1\nA,20,1,50,1\n"))


def test_cli_gives_a_clean_error_for_a_directory(tmp_path):
    from decisionlab.cli import main
    assert main(["rice", str(tmp_path)]) == 2


def test_fragility_shade_and_drop_are_configurable():
    # Worked out by hand: Bulk export (2,160) and Saved filters (1,600) are
    # 26% apart, so a 50% shade to Saved filters' confidence (0.8 -> 0.4,
    # score 800) drops it below both Dark mode (900) and Slack alerts (833),
    # a fall of 3 places from rank 2 to rank 5. drop=1 counts any fall.
    items = load_items("examples/rice_backlog.csv")
    result = fragility(items, shade=0.5, drop=1)
    assert result["Saved filters on the reports page"] == 3


def test_fragility_drop_threshold_filters_small_falls():
    # With shade=0.5 the hand-worked falls are Saved filters=3, Bulk export=1,
    # Slack alerts=2, Onboarding=1, Dark mode=3 (see test above). drop=3
    # should keep only the two that fall 3 or more places.
    items = load_items("examples/rice_backlog.csv")
    strict = fragility(items, shade=0.5, drop=3)
    assert set(strict) == {"Saved filters on the reports page", "Dark mode"}
    assert all(v >= 3 for v in strict.values())


def test_fragility_can_check_reach_instead_of_confidence():
    # Dark mode's RICE score (900) leans on reach (6,000) just as much as on
    # confidence: 6,000 x 0.25 x 0.9 / 1.5 = 900. Shading reach by 30% gives
    # 4,200 x 0.25 x 0.9 / 1.5 = 630, below Slack alerts (833) and the
    # onboarding checklist (810), the same two-place fall as shading confidence.
    items = load_items("examples/rice_backlog.csv")
    assert fragility(items, field="reach") == {"Dark mode": 2}


def test_fragility_restores_reach_after_checking_it():
    items = [Item("A", 100, 1, 0.9, 1), Item("B", 80, 1, 0.9, 1)]
    fragility(items, field="reach")
    assert [i.reach for i in items] == [100, 80]


def test_fragility_rejects_bad_field():
    items = load_items("examples/rice_backlog.csv")
    with pytest.raises(ValueError, match="field"):
        fragility(items, field="effort")


@pytest.mark.parametrize("kwargs", [
    {"shade": 0}, {"shade": 1}, {"shade": 1.2}, {"shade": -0.1}, {"drop": 0}, {"drop": -1},
])
def test_fragility_rejects_bad_shade_or_drop(kwargs):
    items = load_items("examples/rice_backlog.csv")
    with pytest.raises(ValueError):
        fragility(items, **kwargs)


def test_cli_check_reach_adds_a_column(capsys):
    from decisionlab.cli import main
    assert main(["rice", "examples/rice_backlog.csv", "--check-reach"]) == 0
    out = capsys.readouterr().out
    assert "Fragile (reach)" in out
    assert "Fragile at the top on reach" in out


def test_cli_rejects_bad_shade(capsys):
    from decisionlab.cli import main
    assert main(["rice", "examples/rice_backlog.csv", "--shade", "2"]) == 2
    assert "shade must be" in capsys.readouterr().err
