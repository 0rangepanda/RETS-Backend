import unittest
import os

#case_path = os.path.join(os.getcwd(), "librets_test")


def all_case():
    discover = unittest.defaultTestLoader.discover(
        os.getcwd(),
        pattern="*test.py",
        top_level_dir=None
    )
    return discover


if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(all_case())
