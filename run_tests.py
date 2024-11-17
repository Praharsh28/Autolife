import os
import sys
import unittest

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load and run tests
test_loader = unittest.TestLoader()
test_suite = test_loader.discover('tests')
runner = unittest.TextTestRunner(verbosity=2)
runner.run(test_suite)
