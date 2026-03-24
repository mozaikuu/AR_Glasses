from __future__ import annotations

import unittest


class CompatibilityImportTests(unittest.TestCase):
    def test_top_level_modules_import(self) -> None:
        import agent.agent_loop  # noqa: F401
        import agent.llm  # noqa: F401
        import config.settings  # noqa: F401
        import models.requests  # noqa: F401
        import models.responses  # noqa: F401
        import server.api_v2  # noqa: F401
        import server.gateway  # noqa: F401
        import server.server  # noqa: F401

    def test_flask_launcher_imports(self) -> None:
        import run_flask  # noqa: F401


if __name__ == "__main__":
    unittest.main()
