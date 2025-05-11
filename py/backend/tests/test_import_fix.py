import sys
import os
import unittest

# Get the absolute path of the root of the project (ai-six/)
parent_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
# Get the absolute path of the py directory (ai-six/py)
py_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

# Add the parent project root to Python's path
if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

# Now try the import
try:
    from py.backend.engine.config import Config
    print("Import test successful!")
except ImportError as e:
    print(f"Import failed: {e}")

if __name__ == "__main__":
    # This script is just to test imports, not a proper unit test
    pass