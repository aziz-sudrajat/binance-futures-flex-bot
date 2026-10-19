"""Tests for the binance-flex workflow launcher (arg parsing + command build)."""
import importlib.util
import json
import os

import pytest

import dashboard

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)  # tests/ -> repo root


def _load_launcher():
    # binance-flex has no .py extension -> explicit SourceFileLoader.
    from importlib.machinery import SourceFileLoader
    path = os.path.join(REPO, "binance-flex")
    loader = SourceFileLoader("binance_flex", path)
    spec = importlib.util.spec_from_loader("binance_flex", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


bf = _load_launcher()


def _args(**kw):
    import argparse
    d = dict(margin=1.0, leverage=10, auto_tp=20.0, once=False,
             dry_run=False, yes=False, specs=[])
    d.update(kw)
    return argparse.Namespace(**d)


class TestParseSpecs:
    def test_full_example(self):
        assert bf.parse_specs(["isolated", "paper"]) == ("isolated", "paper")

    def test_order_independent(self):
        assert bf.parse_specs(["paper", "isolated"]) == ("isolated", "paper")

    def test_defaults(self):
        assert bf.parse_specs([]) == ("isolated", "paper")

    def test_case_insensitive(self):
        assert bf.parse_specs(["CROSS", "LIVE"]) == ("cross", "live")

    def test_unknown(self):
        with pytest.raises(ValueError):
            bf.parse_specs(["hedge"])

    def test_dup_margin_mode(self):
        with pytest.raises(ValueError):
            bf.parse_specs(["isolated", "cross"])

    def test_dup_run_mode(self):
        with pytest.raises(ValueError):
            bf.parse_specs(["paper", "live"])


class TestResolve:
    def test_user_example(self):
        cfg = bf.resolve(_args(margin=100.0, leverage=10,
                               specs=["isolated", "paper"], auto_tp=20.0))
        assert cfg == {"margin": 100.0, "leverage": 10, "auto_tp": 20.0,
                       "margin_mode": "ISOLATED", "run_mode": "paper",
                       "once": False, "dry_run": False, "confirm_yes": False,
                       "verbose": False, "max_exposure_pct": None}

    def test_bad_margin(self):
        with pytest.raises(ValueError):
            bf.resolve(_args(margin=0))

    def test_bad_leverage(self):
        with pytest.raises(ValueError):
            bf.resolve(_args(leverage=200))

    def test_bad_auto_tp(self):
        with pytest.raises(ValueError):
            bf.resolve(_args(auto_tp=150))

    def test_live_accepts_margin_override(self):
        cfg = bf.resolve(_args(margin=100.0, specs=["live"]))
        assert cfg["margin"] == 100.0

    def test_live_accepts_leverage_override(self):
        cfg = bf.resolve(_args(leverage=20, specs=["live"]))
        assert cfg["leverage"] == 20

    def test_live_defaults_ok(self):
        cfg = bf.resolve(_args(specs=["live"], auto_tp=20.0))
        assert cfg["run_mode"] == "live"


class TestBuildCommand:
    def test_paper_command(self):
        cfg = bf.resolve(_args(margin=100.0, leverage=10,
                               specs=["isolated", "paper"]))
        cmd = bf.build_command(cfg)
        assert "--paper" in cmd and "--loop" in cmd
        assert "--fixed-margin-usdt" in cmd and "--leverage" in cmd
        i = cmd.index("--fixed-margin-usdt")
        assert cmd[i + 1] == repr(100.0)
        assert cmd[cmd.index("--leverage") + 1] == "10"
        assert cmd[1].endswith("run_executor.py")

    def test_live_command_has_no_test_flags(self):
        # user 2026-10-19: -m/-l now allowed for live.
        cfg = bf.resolve(_args(specs=["live"]))
        cmd = bf.build_command(cfg)
        assert "--live" in cmd
        assert "--fixed-margin-usdt" in cmd
        assert "--leverage" in cmd

    def test_once(self):
        cfg = bf.resolve(_args(specs=["testnet"], once=True))
        cmd = bf.build_command(cfg)
        assert "--once" in cmd and "--loop" not in cmd


class TestApplySettings:
    def test_writes_mode_section(self, tmp_path, monkeypatch):
        path = str(tmp_path / "dashboard_settings.json")
        monkeypatch.setattr(dashboard, "SETTINGS_PATH", path)
        cfg = bf.resolve(_args(margin=5.0, specs=["cross", "paper"],
                               auto_tp=25.0))
        bf.apply_settings(cfg)
        with open(path) as f:
            data = json.load(f)
        assert data["paper"]["profit_take_pct"] == 25.0
        assert data["paper"]["margin_mode"] == "CROSS"

    def test_preserves_other_modes(self, tmp_path, monkeypatch):
        path = str(tmp_path / "dashboard_settings.json")
        with open(path, "w") as f:
            json.dump({"live": {"profit_take_pct": 20.0}}, f)
        monkeypatch.setattr(dashboard, "SETTINGS_PATH", path)
        cfg = bf.resolve(_args(specs=["paper"]))
        bf.apply_settings(cfg)
        with open(path) as f:
            data = json.load(f)
        assert data["live"]["profit_take_pct"] == 20.0
        assert data["paper"]["profit_take_pct"] == 20.0
