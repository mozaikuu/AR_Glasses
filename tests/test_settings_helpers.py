from __future__ import annotations

import app.config.settings as settings_module


def test_as_bool_parses_common_values() -> None:
    assert settings_module._as_bool("true") is True
    assert settings_module._as_bool("YES") is True
    assert settings_module._as_bool("1") is True
    assert settings_module._as_bool("false") is False
    assert settings_module._as_bool(None, default=True) is True


def test_pick_prefers_env_over_file(monkeypatch) -> None:
    monkeypatch.setattr(settings_module, "_file_settings", {"UNIT_KEY": "from_file"})
    monkeypatch.setenv("UNIT_KEY", "from_env")
    assert settings_module._pick("UNIT_KEY", "default") == "from_env"


def test_pick_bool_supports_bool_values(monkeypatch) -> None:
    monkeypatch.delenv("UNIT_BOOL", raising=False)
    monkeypatch.setattr(settings_module, "_file_settings", {"UNIT_BOOL": True})
    assert settings_module._pick_bool("UNIT_BOOL", default=False) is True


def test_pick_int_prefers_env(monkeypatch) -> None:
    monkeypatch.setattr(settings_module, "_file_settings", {"UNIT_INT": 7})
    monkeypatch.setenv("UNIT_INT", "42")
    assert settings_module._pick_int("UNIT_INT", 1) == 42


def test_pick_csv_supports_list_and_csv_text(monkeypatch) -> None:
    monkeypatch.delenv("UNIT_CSV", raising=False)
    monkeypatch.setattr(settings_module, "_file_settings", {"UNIT_CSV": ["a", "b", " ", "c"]})
    assert settings_module._pick_csv("UNIT_CSV", "x") == ("a", "b", "c")

    monkeypatch.setattr(settings_module, "_file_settings", {"UNIT_CSV": "a, b, , c"})
    assert settings_module._pick_csv("UNIT_CSV", "x") == ("a", "b", "c")
