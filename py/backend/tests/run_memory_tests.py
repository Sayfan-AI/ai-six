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
from py.backend.tests.memory.test_file_memory_provider import TestFileMemoryProvider
from py.backend.tests.memory.test_summarizer import TestConversationSummarizer
from py.backend.tests.memory.test_memory_tools import TestMemoryTools
from py.backend.tests.memory.test_engine_memory import TestEngineMemory
from py.backend.tests.memory.test_duplicate_tool_calls import TestDuplicateToolCalls

if __name__ == "__main__":
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add the test cases
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestFileMemoryProvider))
    test_suite.addTest(loader.loadTestsFromTestCase(TestConversationSummarizer))
    test_suite.addTest(loader.loadTestsFromTestCase(TestMemoryTools))
    test_suite.addTest(loader.loadTestsFromTestCase(TestEngineMemory))
    test_suite.addTest(loader.loadTestsFromTestCase(TestDuplicateToolCalls))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with non-zero status if there were failures
    sys.exit(not result.wasSuccessful())