import unittest
from selection_manager import Selection

class TestSelection(unittest.TestCase):

    def setUp(self):
        """Setup a simple selection."""
        self.sample_path = "sample_file.py"
        self.selection = Selection(self.sample_path, 10, 20)

    def test_provide_summary(self):
        """Test that ProvideSummary returns the correct summary string."""
        expected_summary = f"Selected from {self.sample_path}: 11 lines."
        actual_summary = self.selection.ProvideSummary()
        self.assertEqual(expected_summary, actual_summary)

if __name__ == "__main__":
    unittest.main()