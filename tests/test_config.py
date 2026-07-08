import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("config", ROOT / "config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


class ConfigTests(unittest.TestCase):
    def test_get_google_api_key_from_env_file(self):
        api_key = config.get_google_api_key()
        self.assertIsNotNone(api_key)
        self.assertIsInstance(api_key, str)
        self.assertTrue(api_key.startswith("AQ"))


if __name__ == "__main__":
    unittest.main()
