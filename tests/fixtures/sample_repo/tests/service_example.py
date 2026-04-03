from src.service import do_work


def test_do_work() -> None:
    assert do_work() == "done"
