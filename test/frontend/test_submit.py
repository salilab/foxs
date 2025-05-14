import unittest
import saliweb.test
import tempfile
import os
import re
import gzip
import zipfile
from flask import request, request_started
import contextlib
from werkzeug.datastructures import FileStorage


# Import the foxs frontend with mocks
foxs = saliweb.test.import_mocked_frontend("foxs", __file__,
                                           '../../frontend')


@contextlib.contextmanager
def mock_ip(app, ip):
    def handler(sender, **kwargs):
        request.remote_addr = ip
    with request_started.connected_to(handler, app):
        yield


def make_test_pdb(tmpdir):
    os.mkdir(os.path.join(tmpdir, 'xy'))
    fh = gzip.open(os.path.join(tmpdir, 'xy', 'pdb1xyz.ent.gz'), 'wt')
    fh.write("REMARK  6  TEST REMARK\n")
    fh.write("ATOM      1  N   ALA C   1      27.932  14.488   4.257  "
             "1.00 23.91           N\n")
    fh.write("ATOM      1  N   ALA D   1      27.932  14.488   4.257  "
             "1.00 23.91           N\n")
    fh.close()


def make_test_mmcif(tmpdir, ihm=False):
    if ihm:
        os.mkdir(os.path.join(tmpdir, 'zz'))
        os.mkdir(os.path.join(tmpdir, 'zz', '1zza'))
        os.mkdir(os.path.join(tmpdir, 'zz', '1zza', 'structures'))
        fname = os.path.join(tmpdir, 'zz', '1zza', 'structures', '1zza.cif.gz')
    else:
        os.mkdir(os.path.join(tmpdir, 'xy'))
        fname = os.path.join(tmpdir, 'xy', '1xyz.cif.gz')

    with gzip.open(fname, 'wt') as fh:
        fh.write("""
loop_
_atom_site.group_PDB
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.auth_asym_id
_atom_site.label_seq_id
_atom_site.auth_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.label_entity_id
_atom_site.id
_atom_site.pdbx_PDB_model_num
ATOM N N . ALA A C 1 1 ? 27.932 14.488 4.257 1.000 23.91 1 1 1
ATOM N N . ALA B D 1 1 ? 27.932 14.488 4.257 1.000 23.91 1 2 1
""")


class Tests(saliweb.test.TestCase):
    """Check submit page"""

    def test_submit_page(self):
        """Test submit page"""
        with tempfile.TemporaryDirectory() as tmpdir:
            incoming = os.path.join(tmpdir, 'incoming')
            os.mkdir(incoming)
            foxs.app.config['DIRECTORIES_INCOMING'] = incoming
            c = foxs.app.test_client()
            rv = c.post('/job')
            self.assertEqual(rv.status_code, 400)  # no PDB file
            self.assertIn(b'please specify PDB code or upload PDB/mmCIF file',
                          rv.data)

            emptyf = os.path.join(tmpdir, 'empty.pdb')
            with open(emptyf, 'w') as fh:
                pass
            badf = os.path.join(tmpdir, 'bad.pdb')
            with open(badf, 'w') as fh:
                fh.write("not a PDB")
            pdbf = os.path.join(tmpdir, 'test.pdb')
            with open(pdbf, 'w') as fh:
                fh.write(
                    "REMARK\n"
                    "ATOM      2  CA  ALA     1      26.711  14.576   5.091\n")
            badproff = os.path.join(tmpdir, 'bad.profile')
            with open(badproff, 'w') as fh:
                fh.write("1 2 3 4 5 6\n")
            proff = os.path.join(tmpdir, 'test.profile')
            with open(proff, 'w') as fh:
                fh.write("# sample profile\n"
                         "garbage\n"
                         "more garbage, ignored\n"
                         "0more garbage\n"
                         "  0.1 -0.5\n"
                         "  0.2 0.5\n")

            # Empty PDB file
            data = {'pdbfile': open(emptyf, 'rb')}
            rv = c.post('/job', data=data)
            self.assertEqual(rv.status_code, 400)
            self.assertIn(
                b'You have uploaded an empty PDB, mmCIF or zip file', rv.data)

            # Something not a PDB file
            data = {'pdbfile': open(badf, 'rb')}
            rv = c.post('/job', data=data)
            self.assertEqual(rv.status_code, 400)
            self.assertIn(
                b'PDB file bad.pdb contains no ATOM or HETATM records',
                rv.data)

            # Filename starting with a dash
            with open(badf, 'rb') as fh:
                fs = FileStorage(stream=fh, filename="-startdash.pdb")
                data = {'pdbfile': fs}
                rv = c.post('/job', data=data)
                self.assertEqual(rv.status_code, 400)
                self.assertIn(
                    b'PDB file -startdash.pdb contains no ATOM or '
                    b'HETATM records', rv.data)

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

            # Bad profile contents
            data = {'pdbfile': open(pdbf, 'rb'),
                    'profile': open(badproff, 'rb')}
            rv = c.post('/job', data=data, follow_redirects=True)
            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'Invalid profile uploaded', rv.data)

            # PDB uploaded instead of profile
            data = {'pdbfile': open(pdbf, 'rb'),
                    'profile': open(pdbf, 'rb')}
            rv = c.post('/job', data=data, follow_redirects=True)
            self.assertEqual(rv.status_code, 400)
            self.assertIn(b'PDB or mmCIF file uploaded', rv.data)

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

    def test_submit_pdb_code_pdb(self):
        """Test submit with a PDB code (PDB format)"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as pdb_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming
                foxs.app.config['PDB_ROOT'] = pdb_root
                foxs.app.config['MMCIF_ROOT'] = pdb_root
                foxs.app.config['IHM_ROOT'] = pdb_root

                make_test_pdb(pdb_root)

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdb': '1xyz:C',
                                          'jobname': 'myjob'},
                            follow_redirects=True)
                self.assertEqual(rv.status_code, 503)
                self.assertIn(b'Your job has been submitted', rv.data)

    def test_submit_pdb_code_mmcif(self):
        """Test submit with a PDB code (mmCIF format)"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as pdb_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming
                foxs.app.config['PDB_ROOT'] = pdb_root
                foxs.app.config['MMCIF_ROOT'] = pdb_root
                foxs.app.config['IHM_ROOT'] = pdb_root

                make_test_mmcif(pdb_root)

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdb': '1xyz:C',
                                          'jobname': 'myjob'},
                            follow_redirects=True)
                self.assertEqual(rv.status_code, 503)
                self.assertIn(b'Your job has been submitted', rv.data)

    def test_submit_pdb_code_ihm(self):
        """Test submit with a PDB code (PDB-IHM format)"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as pdb_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming
                foxs.app.config['PDB_ROOT'] = pdb_root
                foxs.app.config['MMCIF_ROOT'] = pdb_root
                foxs.app.config['IHM_ROOT'] = pdb_root

                make_test_mmcif(pdb_root, ihm=True)

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdb': '1zza:C',
                                          'jobname': 'myjob'},
                            follow_redirects=True)
                self.assertEqual(rv.status_code, 503)
                self.assertIn(b'Your job has been submitted', rv.data)

    def test_submit_zip_file(self):
        """Test submit with zip file"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as zip_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming

                zip_name = os.path.join(zip_root, 'input.zip')
                z = zipfile.ZipFile(zip_name, 'w')
                z.writestr("inputFiles.txt", "foo")  # should be ignored
                z.writestr("in/subdir/.hidden.pdb", "bar")  # should be ignored
                z.writestr("in/subdir/", "")   # directory, should be ignored
                z.writestr("in/subdir/1abc.pdb", "ATOM  bar")
                z.writestr("in/subdir/1def.pdb", "ATOM  bar")
                z.writestr("2xyz.pdb", "ATOM  baz")
                z.close()

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')},
                            follow_redirects=True)
                self.assertEqual(rv.status_code, 503)
                self.assertIn(b'Your job has been submitted', rv.data)

    def test_submit_zip_file_fail(self):
        """Test submit with zip file containing too many PDBs"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as zip_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming

                zip_name = os.path.join(zip_root, 'input.zip')
                z = zipfile.ZipFile(zip_name, 'w')
                for i in range(101):
                    z.writestr("%d.pdb" % i, "ATOM  \n")
                z.close()

                # File limit should be enforced for non-local IPs
                with mock_ip(foxs.app, '1.2.3.4'):
                    c = foxs.app.test_client()
                    rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')})
                    self.assertEqual(rv.status_code, 400)
                    self.assertIn(
                        b'Only 100 PDB/mmCIF files can run on the server',
                        rv.data)

                # All fine if coming from localhost
                with mock_ip(foxs.app, '127.0.0.1'):
                    c = foxs.app.test_client()
                    rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')},
                                follow_redirects=True)
                    self.assertEqual(rv.status_code, 503)
                    r = re.compile(
                        b'Your job has been submitted.*results will be found',
                        re.MULTILINE | re.DOTALL)
                    self.assertRegex(rv.data, r)

    def test_submit_zip_file_not_pdb(self):
        """Test submit with zip file containing something not a PDB"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as zip_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming

                zip_name = os.path.join(zip_root, 'input.zip')
                z = zipfile.ZipFile(zip_name, 'w')
                z.writestr("input/test.pdb", "garbage")
                z.close()

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')})
                self.assertEqual(rv.status_code, 400)
                self.assertIn(b'PDB file input/test.pdb contains no '
                              b'ATOM or HETATM records', rv.data)

    def test_submit_zip_file_empty(self):
        """Test submit with zip file containing no PDBs"""
        with tempfile.TemporaryDirectory() as incoming:
            with tempfile.TemporaryDirectory() as zip_root:
                foxs.app.config['DIRECTORIES_INCOMING'] = incoming

                zip_name = os.path.join(zip_root, 'input.zip')
                z = zipfile.ZipFile(zip_name, 'w')
                # empty zipfile
                z.close()

                c = foxs.app.test_client()
                rv = c.post('/job', data={'pdbfile': open(zip_name, 'rb')})
                self.assertEqual(rv.status_code, 400)
                self.assertIn(b'The uploaded zip file contains no PDB/mmCIFs',
                              rv.data)


if __name__ == '__main__':
    unittest.main()
