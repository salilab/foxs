import unittest
import saliweb.test
import re

# Import the foxs frontend with mocks
foxs = saliweb.test.import_mocked_frontend("foxs", __file__,
                                           '../../frontend')


class Tests(saliweb.test.TestCase):
    """Check results page"""

    def test_results_file(self):
        """Test download of results files"""
        with saliweb.test.make_frontend_job('testjob') as j:
            j.make_file('output.pdb')
            c = foxs.app.test_client()
            rv = c.get('/job/testjob/output.pdb?passwd=%s' % j.passwd)
            self.assertEqual(rv.status_code, 200)

    def test_job_one_pdb_old(self):
        """Test display of job with one PDB, no profile (old view)"""
        with saliweb.test.make_frontend_job('testjob2') as j:
            j.make_file('data.txt',
                        "1abc.pdb - EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n")
            j.make_file('foxs.log', "\n")

            c = foxs.app.test_client()
            rv = c.get('/job/testjob2/old?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*\-.*EMAIL.*'
                           b'NEW!.*interactive interface.*'
                           b'1abc\.png.*plot of profile.*'
                           b'1abc\.pdb\.dat.*Profile file',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)

    def test_job_one_pdb_new(self):
        """Test display of job with one PDB, no profile (new view)"""
        with saliweb.test.make_frontend_job('testjob3') as j:
            j.make_file('data.txt',
                        "1abc.pdb - EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n")
            j.make_file('foxs.log', "\n")
            j.make_file('jmoltable.html',
                        '<a href="dirname/foo.dat">foo</a>\n'
                        '<a href="https://modbase.compbio.ucsf.edu/'
                        'foxs/help.html#foo\n')

            c = foxs.app.test_client()
            rv = c.get('/job/testjob3?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*\-.*EMAIL.*'
                           b'see interactive display\? Use.*old interface.*'
                           b'<canvas id="jsoutput_1".*'
                           b'testjob3\/foo\.dat',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)

    def test_job_one_pdb_profile_old(self):
        """Test display of job with one PDB, fit to a profile (old view)"""
        with saliweb.test.make_frontend_job('testjob4') as j:
            j.make_file('data.txt',
                        "1abc.pdb test.profile EMAIL 0.50 "
                        "500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n")
            j.make_file('foxs.log',
                "1abc.pdb test.profile Chi^2 = 0.202144 c1 = 1.01131 "
                "c2 = 0.5872 default chi^2 = 0.289123\nsecond line\n")

            c = foxs.app.test_client()
            rv = c.get('/job/testjob4/old?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*test\.profile.*EMAIL.*'
                           b'NEW!.*interactive interface.*'
                           b'1abc Fit to experimental profile.*'
                           b'1abc_test\.png.*plot of fit.*'
                           b'1abc_test\.dat.*Experimental profile fit file.*'
                           b'&chi; = 0\.202144 c1 = 1\.01131 c2 = 0\.5872',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)

    def test_job_one_pdb_profile_new(self):
        """Test display of job with one PDB, fit to a profile (new view)"""
        with saliweb.test.make_frontend_job('testjob5') as j:
            j.make_file('data.txt',
                        "1abc.pdb test.profile EMAIL 0.50 "
                        "500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n")
            j.make_file('foxs.log',
                "1abc.pdb test.profile Chi^2 = 0.202144 c1 = 1.01131 "
                "c2 = 0.5872 default chi^2 = 0.289123\nsecond line\n")
            j.make_file('jmoltable.html', "\n")

            c = foxs.app.test_client()
            rv = c.get('/job/testjob5?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*test\.profile.*EMAIL.*'
                           b'see interactive display\? Use.*old interface.*'
                           b'<canvas id="jsoutput_1".*',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)

    def test_job_two_pdbs_old(self):
        """Test display of job with two PDBs, no profile (old view)"""
        with saliweb.test.make_frontend_job('testjob6') as j:
            j.make_file('data.txt',
                        "1abc.pdb - EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n1xyz.pdb")
            j.make_file('foxs.log', "\n")

            c = foxs.app.test_client()
            rv = c.get('/job/testjob6/old?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*\-.*EMAIL.*'
                           b'NEW!.*interactive interface.*'
                           b'1abc\.png.*plot of profile.*'
                           b'1abc\.pdb\.dat.*Profile file.*'
                           b'1xyz\.png.*plot of profile.*'
                           b'1xyz\.pdb\.dat.*Profile file.*'
                           b'All theoretical profiles.*'
                           b'profiles\.png.*plot of profiles',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)

    def test_job_two_pdbs_profile_old(self):
        """Test display of job with two PDBs, fit to profile (old view)"""
        with saliweb.test.make_frontend_job('testjob7') as j:
            j.make_file('data.txt',
                        "1abc.pdb test.profile EMAIL 0.50 500 "
                        "1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n1xyz.pdb")
            j.make_file('foxs.log',
                "1abc.pdb test.profile Chi^2 = 0.202144 c1 = 1.01131 "
                "c2 = 0.5872 default chi^2 = 0.289123\n"
                "1xyz.pdb test.profile Chi^2 = 0.302144 c1 = 1.02131 "
                "c2 = 0.5972 default chi^2 = 0.279123\n")

            c = foxs.app.test_client()
            rv = c.get('/job/testjob7/old?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*test\.profile.*EMAIL.*'
                           b'NEW!.*interactive interface.*'
                           b'PDB file.*&chi;.*c1.*c2.*Download fit file.*'
                           b'1abc\.pdb.*0\.202144.*1.01131.*0\.5872.*'
                           b'1abc_test\.dat.*'
                           b'1abc Fit to experimental profile.*'
                           b'1abc_test\.png.*plot of fit.*'
                           b'1abc_test\.dat.*Experimental profile fit.*'
                           b'1xyz Fit to experimental profile.*'
                           b'1xyz_test\.png.*plot of fit.*'
                           b'1xyz_test\.dat.*Experimental profile fit.*'
                           b'All theoretical profiles.*'
                           b'profiles\.png.*plot of profiles.*'
                           b'fit\.png.*plot of profile fit',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)

    def test_job_two_pdbs_profile_ensemble(self):
        """Test display of ensemble with two PDBs, fit to profile"""
        with saliweb.test.make_frontend_job('testjob8') as j:
            j.make_file('data.txt',
                        "1abc.pdb test.profile EMAIL 0.50 500 "
                        "1 1 1 0 0 0 0.00 1.00 3 1\n")
            j.make_file('inputFiles.txt', "1abc.pdb\n1xyz.pdb")
            c = foxs.app.test_client()
            rv = c.get('/job/testjob8/ensemble?passwd=%s' % j.passwd)
            r = re.compile(b'PDB files.*Profile file.*User e-mail.*'
                           b'1abc\.pdb.*test\.profile.*EMAIL.*'
                           b'models from MultiFoXS.*'
                           b'jsoutput\.3\.js.*'
                           b'<canvas',
                           re.DOTALL | re.MULTILINE)
            self.assertRegex(rv.data, r)


if __name__ == '__main__':
    unittest.main()
