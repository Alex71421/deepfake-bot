from worker.swap import parse_progress, get_output_name


def test_parse_progress_0():
    result = parse_progress("processing: 0%")
    assert result == ("processing", 0)


def test_parse_progress_45():
    result = parse_progress("processing: 45%")
    assert result == ("processing", 45)


def test_parse_progress_false():
    result = parse_progress("FaceFusion started")
    assert result is None


def test_get_output_name_empty(tmp_path):
    assert tmp_path / "result_1.mp4" == get_output_name(tmp_path)


def test_get_output_name_first_exists(tmp_path):
    (tmp_path / "result_1.mp4").touch()
    assert tmp_path / "result_2.mp4" == get_output_name(tmp_path)


def test_get_output_name_second_exists(tmp_path):
    (tmp_path / "result_1.mp4").touch()
    (tmp_path / "result_2.mp4").touch()
    assert tmp_path / "result_3.mp4" == get_output_name(tmp_path)
