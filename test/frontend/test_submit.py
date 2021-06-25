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
    fh = gzip.open(os.path.join(tmpdir, 'xy', 'pdb1xyz.ent.gz'), 'wt')
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
        with saliweb.test.temporary_directory() as tmpdir:
            incoming = os.path.join(tmpdir, 'incoming')
            os.mkdir(incoming)
            foxs.app.config['DIRECTORIES_INCOMING'] = incoming
            c = foxs.app.test_client()
            rv = c.post('/job')
            self.assertEqual(rv.status_code, 400)  # no PDB file
            self.assertIn(b'please specify PDB code or upload file', rv.data)

            emptyf = os.path.join(tmpdir, 'empty.pdb')
            with open(emptyf, 'w') as fh:
                pass
            pdbf = os.path.join(tmpdir, 'test.pdb')
            with open(pdbf, 'w') as fh:
                fh.write(
                    "REMARK\n"
                    "ATOM      2  CA  ALA     1      26.711  14.576   5.091\n")
            proff = os.path.join(tmpdir, 'test.profile')
            with open(proff, 'w') as fh:
                fh.write("\n")

            # Empty PDB file
            data = {'pdbfile': open(emptyf, 'rb')}
            rv = c.post('/job', data=data)
            self.assertEqual(rv.status_code, 400)
            self.assertIn(
                b'You have uploaded an empty PDB or zip file', rv.data)

            # Bad hlayer value
            rv = c.post('/job', data={'c2': '5.0'})
            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'Invalid hydration layer density value', rv.data)

            # Bad q value
            rv = c.post('/job', data={'q': '4.0'})
            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'Invalid q value; it must be &gt; 0 and &lt; 1.0',
                          rv.data)

            # Bad profile size
            rv = c.post('/job', data={'psize': '5000'})
            self.assertEqual(rv.status_code, 400)
            self.assertIn(
                b'Invalid profile size; it must be &gt; 20 and &lt; 2000',
                rv.data)

            # Successful submission with profile (no email)
            data = {'pdbfile': open(pdbf, 'rb'), 'profile': open(proff, 'rb')}
            rv = c.post('/job', data=data, follow_redirects=True)
            self.assertEqual(rv.status_code, 503)
            r = re.compile(
                b'Your job has been submitted.*results will be found',
                re.MULTILINE | re.DOTALL)
            self.assertRegex(rv.data, r)

            # Successful submission without profile (no email)
            data = {'pdbfile': open(pdbf, 'rb'), 'hlayer': 'on'}
            rv = c.post('/job', data=data, follow_redirects=True)
            self.assertEqual(rv.status_code, 503)
            r = re.compile(
                b'Your job has been submitted.*results will be found',
                re.MULTILINE | re.DOTALL)
            self.assertRegex(rv.data, r)

            # Successful submission (with email)
            data = {'pdbfile': open(pdbf, 'rb'), 'profile': open(proff, 'rb'),
                    'email': 'test@test.com'}
            rv = c.post('/job', data=data, follow_redirects=True)
            self.assertEqual(rv.status_code, 503)
            r = re.compile(b'Your job has been submitted.*'
                           b'results will be found.*'
                           b'You will receive an e-mail',
                           re.MULTILINE | re.DOTALL)
            self.assertRegex(rv.data, r)

    def test_submit_pdb_code(self):
        """Test submit with a PDB code"""
        with saliweb.test.temporary_directory() as incoming:
            with saliweb.test.temporary_directory() as pdb_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming
                foxs.app.config['PDB_ROOT'] = pdb_root

                make_test_pdb(pdb_root)

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdb': '1xyz:C'},
                            follow_redirects=True)
                self.assertEqual(rv.status_code, 503)
                self.assertIn(b'Your job has been submitted', rv.data)

    def test_submit_zip_file(self):
        """Test submit with zip file"""
        with saliweb.test.temporary_directory() as incoming:
            with saliweb.test.temporary_directory() as zip_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming

                zip_name = os.path.join(zip_root, 'input.zip')
                z = zipfile.ZipFile(zip_name, 'w')
                z.writestr("inputFiles.txt", "foo")  # should be ignored
                z.writestr("in/subdir/1abc.pdb", "bar")
                z.writestr("2xyz.pdb", "baz")
                z.close()

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')},
                            follow_redirects=True)
                self.assertEqual(rv.status_code, 503)
                self.assertIn(b'Your job has been submitted', rv.data)

    def test_submit_zip_file_fail(self):
        """Test submit with zip file containing too many PDBs"""
        with saliweb.test.temporary_directory() as incoming:
            with saliweb.test.temporary_directory() as zip_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming

                zip_name = os.path.join(zip_root, 'input.zip')
                z = zipfile.ZipFile(zip_name, 'w')
                for i in range(101):
                    z.writestr("%d.pdb" % i, "baz")
                z.close()

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')})
                self.assertEqual(rv.status_code, 400)
                self.assertIn(b'Only 100 PDB files can run on the server',
                              rv.data)


if __name__ == '__main__':
    unittest.main()
