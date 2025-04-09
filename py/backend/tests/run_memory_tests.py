#!/usr/bin/env python3
"""
Run all memory-related tests.
"""

import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import the test modules
from memory.test_file_memory_provider import TestFileMemoryProvider
from memory.test_summarizer import TestConversationSummarizer
from memory.test_memory_tools import TestMemoryTools
from memory.test_engine_memory import TestEngineMemory

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add the test cases
    test_suite.addTest(unittest.makeSuite(TestFileMemoryProvider))
    test_suite.addTest(unittest.makeSuite(TestConversationSummarizer))
    test_suite.addTest(unittest.makeSuite(TestMemoryTools))
    test_suite.addTest(unittest.makeSuite(TestEngineMemory))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with non-zero status if there were failures
    sys.exit(not result.wasSuccessful())