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
        self.assertIn('Fast SAXS Profile Computation', rv.data)
        self.assertIn('Type PDB code of input molecule', rv.data)
        self.assertIn('Experimental profile:', rv.data)

    def test_help(self):
        """Test help page"""
        c = foxs.app.test_client()
        rv = c.get('/help')
        self.assertIn('FoXS requires only one mandatory input parameter',
                      rv.data)
        self.assertIn('displays the profile fit along with the residuals',
                      rv.data)

    def test_contact(self):
        """Test contact page"""
        c = foxs.app.test_client()
        rv = c.get('/contact')
        self.assertIn('Please address inquiries to:', rv.data)

    def test_about(self):
        """Test about page"""
        c = foxs.app.test_client()
        rv = c.get('/about')
        self.assertIn('About Small Angle X-ray Scattering', rv.data)

    def test_faq(self):
        """Test FAQ page"""
        c = foxs.app.test_client()
        rv = c.get('/faq')
        self.assertIn('structure includes non-protein atoms', rv.data)

    def test_links(self):
        """Test links page"""
        c = foxs.app.test_client()
        rv = c.get('/links')
        self.assertIn('BILBOMD', rv.data)
        self.assertIn('Chimera', rv.data)

    def test_queue(self):
        """Test queue page"""
        c = foxs.app.test_client()
        rv = c.get('/job')
        self.assertIn('No pending or running jobs', rv.data)


if __name__ == '__main__':
    unittest.main()
