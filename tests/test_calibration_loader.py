import pytest
import json
import tempfile
from pathlib import Path
from polychemtools.utils.calibration_loader import (
    load_calibration,
    parse_calibration_string,
    resolve_calibration,
    CalibrationError,
    CalibrationNotFoundError,
    CalibrationFileError,
    InvalidCalibrationError
)


@pytest.fixture
def sample_calibrations():
    """Sample calibration data for testing"""
    return {
        "sample_calibration": {
            "type": "cubic",
            "params": [-0.001701334, 0.064349247, -1.197289570, 14.035147838]
        }
    }


@pytest.fixture
def calibration_file(tmp_path, sample_calibrations):
    """Create a temporary JSON calibration file"""
    cal_file = tmp_path / "calibrations.json"
    with cal_file.open('w') as f:
        json.dump(sample_calibrations, f)
    return cal_file


class TestLoadCalibration:
    """Tests for the load_calibration function"""

    def test_load_valid_calibration(self, calibration_file):
        """Test loading a valid calibration from a file"""
        calibration = load_calibration(
            str(calibration_file),
            "sample_calibration"
        )

        assert calibration["type"] == "cubic"
        assert len(calibration["params"]) == 4
        assert calibration["params"][0] == pytest.approx(-0.001701334)

    def test_file_not_found(self, tmp_path):
        """Test error when calibration file doesn't exist"""
        with pytest.raises(CalibrationFileError, match="not found"):
            load_calibration(
                str(tmp_path / "nonexistent.json"),
                "sample_calibration"
            )

    def test_calibration_not_found(self, calibration_file):
        """Test error when calibration name doesn't exist in file"""
        with pytest.raises(
            CalibrationNotFoundError,
            match="not found.*Available calibrations"
        ):
            load_calibration(
                str(calibration_file),
                "nonexistent_calibration"
            )

    def test_invalid_json(self, tmp_path):
        """Test error when file contains invalid JSON"""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ this is not valid json }")

        with pytest.raises(CalibrationFileError, match="Failed to parse JSON"):
            load_calibration(str(bad_file), "sample_calibration")

    def test_missing_type_key(self, tmp_path):
        """Test error when calibration is missing 'type' key"""
        cal_data = {
            "bad_calibration": {
                "params": [1, 2, 3]
            }
        }
        cal_file = tmp_path / "calibrations.json"
        with cal_file.open('w') as f:
            json.dump(cal_data, f)

        with pytest.raises(InvalidCalibrationError, match="missing required 'type'"):
            load_calibration(str(cal_file), "bad_calibration")

    def test_missing_params_key(self, tmp_path):
        """Test error when calibration is missing 'params' key"""
        cal_data = {
            "bad_calibration": {
                "type": "cubic"
            }
        }
        cal_file = tmp_path / "calibrations.json"
        with cal_file.open('w') as f:
            json.dump(cal_data, f)

        with pytest.raises(InvalidCalibrationError, match="missing required 'params'"):
            load_calibration(str(cal_file), "bad_calibration")

    def test_params_not_list(self, tmp_path):
        """Test error when params is not a list"""
        cal_data = {
            "bad_calibration": {
                "type": "cubic",
                "params": "not a list"
            }
        }
        cal_file = tmp_path / "calibrations.json"
        with cal_file.open('w') as f:
            json.dump(cal_data, f)

        with pytest.raises(InvalidCalibrationError, match="params must be a list"):
            load_calibration(str(cal_file), "bad_calibration")

    def test_calibration_not_dict(self, tmp_path):
        """Test error when calibration is not a dictionary"""
        cal_data = {
            "bad_calibration": "this is a string, not a dict"
        }
        cal_file = tmp_path / "calibrations.json"
        with cal_file.open('w') as f:
            json.dump(cal_data, f)

        with pytest.raises(InvalidCalibrationError, match="must be a dictionary"):
            load_calibration(str(cal_file), "bad_calibration")


class TestParseCalibrationString:
    """Tests for the parse_calibration_string function"""

    def test_valid_string(self):
        """Test parsing a valid calibration string"""
        filepath, name = parse_calibration_string(
            "../data/calibrations.json:sample_calibration"
        )
        assert filepath == "../data/calibrations.json"
        assert name == "sample_calibration"

    def test_absolute_path(self):
        """Test parsing with absolute path"""
        filepath, name = parse_calibration_string(
            "/Users/data/calibrations.json:my_calibration"
        )
        assert filepath == "/Users/data/calibrations.json"
        assert name == "my_calibration"

    def test_with_whitespace(self):
        """Test that whitespace is trimmed"""
        filepath, name = parse_calibration_string(
            "  calibrations.json : sample_calibration  "
        )
        assert filepath == "calibrations.json"
        assert name == "sample_calibration"

    def test_missing_colon(self):
        """Test error when colon is missing"""
        with pytest.raises(ValueError, match="must be in format"):
            parse_calibration_string("calibrations.json")

    def test_empty_filepath(self):
        """Test error when filepath is empty"""
        with pytest.raises(ValueError, match="Filepath cannot be empty"):
            parse_calibration_string(":sample_calibration")

    def test_empty_name(self):
        """Test error when calibration name is empty"""
        with pytest.raises(ValueError, match="Calibration name cannot be empty"):
            parse_calibration_string("calibrations.json:")

    def test_multiple_colons(self):
        """Test that only first colon is used as separator"""
        filepath, name = parse_calibration_string(
            "data/file.json:calibration:with:colons"
        )
        assert filepath == "data/file.json"
        assert name == "calibration:with:colons"


class TestResolveCalibration:
    """Tests for the resolve_calibration function"""

    def test_resolve_dict(self):
        """Test that dict calibrations are returned as-is"""
        cal_dict = {
            "type": "cubic",
            "params": [1, 2, 3, 4]
        }
        result = resolve_calibration(cal_dict)
        assert result is cal_dict

    def test_resolve_string(self, calibration_file):
        """Test that string calibrations are loaded from file"""
        cal_string = f"{calibration_file}:sample_calibration"
        result = resolve_calibration(cal_string)

        assert isinstance(result, dict)
        assert result["type"] == "cubic"
        assert len(result["params"]) == 4

    def test_invalid_type(self):
        """Test error when calibration is neither dict nor string"""
        with pytest.raises(ValueError, match="must be either a dict or a string"):
            resolve_calibration(123)

        with pytest.raises(ValueError, match="must be either a dict or a string"):
            resolve_calibration([1, 2, 3])

    def test_resolve_string_file_not_found(self):
        """Test error when file in string doesn't exist"""
        with pytest.raises(CalibrationFileError, match="not found"):
            resolve_calibration("nonexistent.json:sample_calibration")


class TestIntegration:
    """Integration tests with actual sample calibration file"""

    def test_load_from_examples(self):
        """Test loading from the actual examples directory"""
        # This test uses the real sample_calibrations.json in examples
        calibration = load_calibration(
            "examples/sample_calibrations.json",
            "sample_calibration"
        )

        assert calibration["type"] == "cubic"
        assert len(calibration["params"]) == 4
        assert isinstance(calibration["params"][0], float)

    def test_resolve_from_examples(self):
        """Test resolve_calibration with real example file"""
        calibration = resolve_calibration(
            "examples/sample_calibrations.json:sample_calibration"
        )

        assert calibration["type"] == "cubic"
        assert len(calibration["params"]) == 4
