from pathlib import Path

from scripts.verify_governance import invalid_change_record_filenames


def test_change_record_filename_validator_accepts_canonical_names(tmp_path: Path) -> None:
    (tmp_path / "CR-20261031-001.md").write_text("valid", encoding="utf-8")
    (tmp_path / "README.md").write_text("not a change record", encoding="utf-8")

    assert invalid_change_record_filenames(tmp_path) == []


def test_change_record_filename_validator_rejects_noncanonical_names(tmp_path: Path) -> None:
    (tmp_path / "CR-20261031-002.md").write_text("valid", encoding="utf-8")
    (tmp_path / "CR-20261031-003-long-title.md").write_text("invalid", encoding="utf-8")
    (tmp_path / "CR-20261031.md").write_text("invalid", encoding="utf-8")

    assert invalid_change_record_filenames(tmp_path) == [
        "CR-20261031-003-long-title.md",
        "CR-20261031.md",
    ]
