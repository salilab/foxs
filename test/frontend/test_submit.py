import unittest
import saliweb.test
import os
import re
import gzip
import zipfile


# Import the foxs frontend with mocks
foxs = saliweb.test.import_mocked_frontend("foxs", __file__,
                                           '../../frontend')


def make_test_pdb(tmpdir):
    os.mkdir(os.path.join(tmpdir, 'xy'))
    fh = gzip.open(os.path.join(tmpdir, 'xy', 'pdb1xyz.ent.gz'), 'wb')
    fh.write("REMARK  6  TEST REMARK\n")
    fh.write("ATOM      1  N   ALA C   1      27.932  14.488   4.257  "
             "1.00 23.91           N\n")
    fh.write("ATOM      1  N   ALA D   1      27.932  14.488   4.257  "
             "1.00 23.91           N\n")
    fh.close()


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
        emptyf = os.path.join(t.tmpdir, 'empty.pdb')
        with open(emptyf, 'w') as fh:
            pass
        pdbf = os.path.join(t.tmpdir, 'test.pdb')
        with open(pdbf, 'w') as fh:
            fh.write("REMARK\n"
                     "ATOM      2  CA  ALA     1      26.711  14.576   5.091\n")
        proff = os.path.join(t.tmpdir, 'test.profile')
        with open(proff, 'w') as fh:
            fh.write("\n")

        # Empty PDB file
        data = {'pdbfile': open(emptyf)}
        rv = c.post('/job', data=data)
        self.assertEqual(rv.status_code, 400)
        self.assertIn('You have uploaded an empty PDB or zip file', rv.data)

        # Bad hlayer value
        rv = c.post('/job', data={'c2': '5.0'})
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Invalid hydration layer density value', rv.data)

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
        data = {'pdbfile': open(pdbf), 'hlayer': 'on'}
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

    def test_submit_pdb_code(self):
        """Test submit with a PDB code"""
        incoming = saliweb.test.TempDir()
        pdb_root = saliweb.test.TempDir()
        foxs.app.config['DIRECTORIES_INCOMING'] = incoming.tmpdir
        foxs.app.config['PDB_ROOT'] = pdb_root.tmpdir

        make_test_pdb(pdb_root.tmpdir)

        c = foxs.app.test_client()
        rv = c.post('/job', data={'pdb': '1xyz:C'})
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Your job has been submitted', rv.data)

    def test_submit_zip_file(self):
        """Test submit with zip file"""
        incoming = saliweb.test.TempDir()
        zip_root = saliweb.test.TempDir()
        foxs.app.config['DIRECTORIES_INCOMING'] = incoming.tmpdir

        zip_name = os.path.join(zip_root.tmpdir, 'input.zip')
        z = zipfile.ZipFile(zip_name, 'w')
        z.writestr("inputFiles.txt", "foo")  # should be ignored
        z.writestr("in/subdir/1abc.pdb", "bar")
        z.writestr("2xyz.pdb", "baz")
        z.close()

        c = foxs.app.test_client()
        rv = c.post('/job', data={'pdbfile': open(zip_name)})
        self.assertEqual(rv.status_code, 200)
        self.assertIn('Your job has been submitted', rv.data)

    def test_submit_zip_file_fail(self):
        """Test submit with zip file containing too many PDBs"""
        incoming = saliweb.test.TempDir()
        zip_root = saliweb.test.TempDir()
        foxs.app.config['DIRECTORIES_INCOMING'] = incoming.tmpdir

        zip_name = os.path.join(zip_root.tmpdir, 'input.zip')
        z = zipfile.ZipFile(zip_name, 'w')
        for i in range(101):
            z.writestr("%d.pdb" % i, "baz")
        z.close()

        c = foxs.app.test_client()
        rv = c.post('/job', data={'pdbfile': open(zip_name)})
        self.assertEqual(rv.status_code, 400)
        self.assertIn('Only 100 PDB files can run on the server', rv.data)


if __name__ == '__main__':
    unittest.main()
