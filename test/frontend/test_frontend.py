import unittest
import saliweb.test

# Import the foxs frontend with mocks
foxs = saliweb.test.import_mocked_frontend("foxs", __file__,
                                           '../../frontend')


class Tests(saliweb.test.TestCase):

    def test_index(self):
        """Test index page"""
        c = foxs.app.test_client()
        rv = c.get('/')
        self.assertIn('Main Page', rv.data)


if __name__ == '__main__':
    unittest.main()
