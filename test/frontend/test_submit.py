import unittest
import saliweb.test
import os
import re

# Import the foxs frontend with mocks
foxs = saliweb.test.import_mocked_frontend("foxs", __file__,
                                           '../../frontend')


class Tests(saliweb.test.TestCase):
    """Check submit page"""

    def test_submit_page(self):
        """Test submit page"""
        incoming = saliweb.test.TempDir()
        foxs.app.config['DIRECTORIES_INCOMING'] = incoming.tmpdir
        c = foxs.app.test_client()
        rv = c.post('/job')
        self.assertEqual(rv.status_code, 400)  # no PDB file
        self.assertIn('please specify PDB code or upload file', rv.data)

        t = saliweb.test.TempDir()
        pdbf = os.path.join(t.tmpdir, 'test.pdb')
        with open(pdbf, 'w') as fh:
            fh.write("REMARK\n"
                     "ATOM      2  CA  ALA     1      26.711  14.576   5.091\n")
        proff = os.path.join(t.tmpdir, 'test.profile')
        with open(proff, 'w') as fh:
            fh.write("\n")

        # Bad q value
        rv = c.post('/job', data={'q': '4.0'})
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Invalid q value; it must be &gt; 0 and &lt; 1.0',
                      rv.data)

        # Bad profile size
        rv = c.post('/job', data={'psize': '5000'})
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Invalid profile size; it must be &gt; 20 and &lt; 2000',
                      rv.data)

        # Successful submission with profile (no email)
        data = {'pdbfile': open(pdbf), 'profile': open(proff)}
        rv = c.post('/job', data=data)
        self.assertEqual(rv.status_code, 200)
        r = re.compile('Your job has been submitted.*Results will be found at',
                       re.MULTILINE | re.DOTALL)
        self.assertRegexpMatches(rv.data, r)

        # Successful submission without profile (no email)
        data = {'pdbfile': open(pdbf)}
        rv = c.post('/job', data=data)
        self.assertEqual(rv.status_code, 200)
        r = re.compile('Your job has been submitted.*Results will be found at',
                       re.MULTILINE | re.DOTALL)
        self.assertRegexpMatches(rv.data, r)

        # Successful submission (with email)
        data = {'pdbfile': open(pdbf), 'profile': open(proff),
                'email': 'test@test.com'}
        rv = c.post('/job', data=data)
        self.assertEqual(rv.status_code, 200)
        r = re.compile('Your job has been submitted.*'
                       'Results will be found at.*'
                       'You will receive an e-mail',
                       re.MULTILINE | re.DOTALL)
        self.assertRegexpMatches(rv.data, r)


if __name__ == '__main__':
    unittest.main()
