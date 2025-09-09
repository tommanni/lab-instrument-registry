from django.test import TestCase
# Create your tests here.

# always true, for testing the testing frameworks
class TestingTest(TestCase):
    def test_test(self):
        self.assertEqual(True, True)