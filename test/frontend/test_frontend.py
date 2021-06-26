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
        self.assertIn(b'Fast SAXS Profile Computation', rv.data)
        self.assertIn(b'Type PDB code of input molecule', rv.data)
        self.assertIn(b'Experimental profile:', rv.data)

    def test_help(self):
        """Test help page"""
        c = foxs.app.test_client()
        rv = c.get('/help')
        self.assertIn(b'FoXS requires only one mandatory input parameter',
                      rv.data)
        self.assertIn(b'displays the profile fit along with the residuals',
                      rv.data)

    def test_help_multi(self):
        """Test help_multi page"""
        c = foxs.app.test_client()
        rv = c.get('/help_multi')
        self.assertIn(b'If multiple PDB files were uploaded', rv.data)

    def test_about(self):
        """Test about page"""
        c = foxs.app.test_client()
        rv = c.get('/about')
        self.assertIn(b'About Small Angle X-ray Scattering', rv.data)

    def test_faq(self):
        """Test FAQ page"""
        c = foxs.app.test_client()
        rv = c.get('/faq')
        self.assertIn(b'structure includes non-protein atoms', rv.data)

    def test_download(self):
        """Test download page"""
        c = foxs.app.test_client()
        rv = c.get('/download')
        self.assertIn(b'see the source code of this web service', rv.data)

    def test_links(self):
        """Test links page"""
        c = foxs.app.test_client()
        rv = c.get('/links')
        self.assertIn(b'BILBOMD', rv.data)
        self.assertIn(b'Chimera', rv.data)

    def test_queue(self):
        """Test queue page"""
        c = foxs.app.test_client()
        rv = c.get('/job')
        self.assertIn(b'No pending or running jobs', rv.data)


if __name__ == '__main__':
    unittest.main()
