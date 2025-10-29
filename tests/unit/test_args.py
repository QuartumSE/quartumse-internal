"""Unit tests for quartumse.utils.args CLI argument helpers."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from quartumse.utils.args import (
    DEFAULT_DATA_DIR,
    add_backend_option,
    add_data_dir_option,
    add_seed_option,
    add_shadow_size_option,
    namespace_overrides,
)


class TestAddBackendOption:
    """Tests for add_backend_option()."""

    def test_adds_backend_argument(self):
        """add_backend_option should add --backend flag to parser."""
        parser = argparse.ArgumentParser()
        add_backend_option(parser)
        args = parser.parse_args(["--backend", "aer_simulator"])
        assert args.backend == "aer_simulator"

    def test_accepts_ibm_descriptor(self):
        """--backend should accept IBM Runtime descriptor format."""
        parser = argparse.ArgumentParser()
        add_backend_option(parser)
        args = parser.parse_args(["--backend", "ibm:ibm_brisbane"])
        assert args.backend == "ibm:ibm_brisbane"

    def test_default_value(self):
        """add_backend_option should respect default parameter."""
        parser = argparse.ArgumentParser()
        add_backend_option(parser, default="aer_simulator")
        args = parser.parse_args([])
        assert args.backend == "aer_simulator"

    def test_required_option(self):
        """add_backend_option should enforce required=True."""
        parser = argparse.ArgumentParser()
        add_backend_option(parser, required=True)
        with pytest.raises(SystemExit):
            parser.parse_args([])  # Missing required --backend


class TestAddDataDirOption:
    """Tests for add_data_dir_option()."""

    def test_adds_data_dir_argument(self):
        """add_data_dir_option should add --data-dir flag."""
        parser = argparse.ArgumentParser()
        add_data_dir_option(parser)
        args = parser.parse_args(["--data-dir", "/tmp/data"])
        assert args.data_dir == Path("/tmp/data")

    def test_returns_path_object(self):
        """--data-dir should return Path instances, not strings."""
        parser = argparse.ArgumentParser()
        add_data_dir_option(parser)
        args = parser.parse_args(["--data-dir", "validation_data"])
        assert isinstance(args.data_dir, Path)
        assert args.data_dir == Path("validation_data")

    def test_default_none(self):
        """add_data_dir_option should default to None when not specified."""
        parser = argparse.ArgumentParser()
        add_data_dir_option(parser)
        args = parser.parse_args([])
        assert args.data_dir is None

    def test_custom_default(self):
        """add_data_dir_option should accept custom default path."""
        parser = argparse.ArgumentParser()
        add_data_dir_option(parser, default="custom_data")
        args = parser.parse_args([])
        assert args.data_dir == Path("custom_data")

    def test_windows_paths(self):
        """--data-dir should handle Windows-style paths."""
        parser = argparse.ArgumentParser()
        add_data_dir_option(parser)
        args = parser.parse_args(["--data-dir", r"C:\Users\data"])
        assert args.data_dir == Path(r"C:\Users\data")


class TestAddSeedOption:
    """Tests for add_seed_option()."""

    def test_adds_seed_argument(self):
        """add_seed_option should add --seed flag."""
        parser = argparse.ArgumentParser()
        add_seed_option(parser)
        args = parser.parse_args(["--seed", "42"])
        assert args.seed == 42

    def test_accepts_integer_values(self):
        """--seed should parse string to integer."""
        parser = argparse.ArgumentParser()
        add_seed_option(parser)
        args = parser.parse_args(["--seed", "123456"])
        assert args.seed == 123456
        assert isinstance(args.seed, int)

    def test_default_none(self):
        """add_seed_option should default to None when not specified."""
        parser = argparse.ArgumentParser()
        add_seed_option(parser)
        args = parser.parse_args([])
        assert args.seed is None

    def test_custom_default(self):
        """add_seed_option should accept custom default seed."""
        parser = argparse.ArgumentParser()
        add_seed_option(parser, default=999)
        args = parser.parse_args([])
        assert args.seed == 999

    def test_rejects_non_integer(self):
        """--seed should reject non-integer values."""
        parser = argparse.ArgumentParser()
        add_seed_option(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["--seed", "not_a_number"])


class TestAddShadowSizeOption:
    """Tests for add_shadow_size_option()."""

    def test_adds_shadow_size_argument(self):
        """add_shadow_size_option should add --shadow-size flag."""
        parser = argparse.ArgumentParser()
        add_shadow_size_option(parser)
        args = parser.parse_args(["--shadow-size", "512"])
        assert args.shadow_size == 512

    def test_accepts_large_values(self):
        """--shadow-size should accept large integer values."""
        parser = argparse.ArgumentParser()
        add_shadow_size_option(parser)
        args = parser.parse_args(["--shadow-size", "100000"])
        assert args.shadow_size == 100000
        assert isinstance(args.shadow_size, int)

    def test_default_none(self):
        """add_shadow_size_option should default to None."""
        parser = argparse.ArgumentParser()
        add_shadow_size_option(parser)
        args = parser.parse_args([])
        assert args.shadow_size is None

    def test_custom_default(self):
        """add_shadow_size_option should accept custom default."""
        parser = argparse.ArgumentParser()
        add_shadow_size_option(parser, default=256)
        args = parser.parse_args([])
        assert args.shadow_size == 256

    def test_rejects_non_integer(self):
        """--shadow-size should reject non-integer values."""
        parser = argparse.ArgumentParser()
        add_shadow_size_option(parser)
        with pytest.raises(SystemExit):
            parser.parse_args(["--shadow-size", "five-hundred"])


class TestNamespaceOverrides:
    """Tests for namespace_overrides()."""

    def test_extracts_backend(self):
        """namespace_overrides should extract backend when present."""
        namespace = argparse.Namespace(backend="aer_simulator")
        overrides = namespace_overrides(namespace)
        assert overrides == {"backend": "aer_simulator"}

    def test_extracts_data_dir(self):
        """namespace_overrides should extract data_dir as Path."""
        namespace = argparse.Namespace(data_dir=Path("/tmp/data"))
        overrides = namespace_overrides(namespace)
        assert overrides == {"data_dir": Path("/tmp/data")}

    def test_extracts_seed(self):
        """namespace_overrides should extract seed when present."""
        namespace = argparse.Namespace(seed=42)
        overrides = namespace_overrides(namespace)
        assert overrides == {"seed": 42}

    def test_extracts_shadow_size(self):
        """namespace_overrides should extract shadow_size when present."""
        namespace = argparse.Namespace(shadow_size=1024)
        overrides = namespace_overrides(namespace)
        assert overrides == {"shadow_size": 1024}

    def test_omits_none_values(self):
        """namespace_overrides should omit attributes set to None."""
        namespace = argparse.Namespace(
            backend="aer_simulator",
            data_dir=None,
            seed=42,
            shadow_size=None,
        )
        overrides = namespace_overrides(namespace)
        # Only non-None values should be present
        assert overrides == {"backend": "aer_simulator", "seed": 42}
        assert "data_dir" not in overrides
        assert "shadow_size" not in overrides

    def test_handles_empty_namespace(self):
        """namespace_overrides should return empty dict for empty namespace."""
        namespace = argparse.Namespace()
        overrides = namespace_overrides(namespace)
        assert overrides == {}

    def test_handles_all_none(self):
        """namespace_overrides should return empty dict when all values None."""
        namespace = argparse.Namespace(
            backend=None, data_dir=None, seed=None, shadow_size=None
        )
        overrides = namespace_overrides(namespace)
        assert overrides == {}

    def test_extracts_all_attributes(self):
        """namespace_overrides should extract all supported attributes."""
        namespace = argparse.Namespace(
            backend="ibm:ibm_brisbane",
            data_dir=Path("validation_data"),
            seed=12345,
            shadow_size=2048,
        )
        overrides = namespace_overrides(namespace)
        assert len(overrides) == 4
        assert overrides["backend"] == "ibm:ibm_brisbane"
        assert overrides["data_dir"] == Path("validation_data")
        assert overrides["seed"] == 12345
        assert overrides["shadow_size"] == 2048


class TestIntegration:
    """Integration tests combining multiple arg helpers."""

    def test_all_options_together(self):
        """All arg options should work together in one parser."""
        parser = argparse.ArgumentParser()
        add_backend_option(parser)
        add_data_dir_option(parser)
        add_seed_option(parser)
        add_shadow_size_option(parser)

        args = parser.parse_args(
            [
                "--backend",
                "aer_simulator",
                "--data-dir",
                "/tmp/data",
                "--seed",
                "999",
                "--shadow-size",
                "4096",
            ]
        )

        assert args.backend == "aer_simulator"
        assert args.data_dir == Path("/tmp/data")
        assert args.seed == 999
        assert args.shadow_size == 4096

    def test_config_override_pattern(self):
        """Simulate typical config file + CLI override pattern."""
        # Simulate config file defaults
        config = {
            "backend": "aer_simulator",
            "data_dir": "data",
            "seed": 42,
            "shadow_size": 256,
        }

        # Simulate CLI with partial overrides
        parser = argparse.ArgumentParser()
        add_backend_option(parser)
        add_data_dir_option(parser)
        add_seed_option(parser)
        add_shadow_size_option(parser)

        args = parser.parse_args(["--backend", "ibm:ibm_kyoto", "--seed", "999"])

        # Extract CLI overrides
        cli_overrides = namespace_overrides(args)

        # Merge: CLI overrides take precedence
        final_config = {**config, **cli_overrides}

        assert final_config["backend"] == "ibm:ibm_kyoto"  # CLI override
        assert final_config["seed"] == 999  # CLI override
        assert final_config["data_dir"] == "data"  # From config (CLI was None)
        assert final_config["shadow_size"] == 256  # From config (CLI was None)

    def test_default_data_dir_constant(self):
        """DEFAULT_DATA_DIR constant should be accessible."""
        assert DEFAULT_DATA_DIR == Path("data")
        assert isinstance(DEFAULT_DATA_DIR, Path)
