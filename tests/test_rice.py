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
