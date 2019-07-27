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
            r = re.compile('PDB files.*Profile file.*User e-mail.*'
                           '1abc\.pdb.*\-.*EMAIL.*'
                           'NEW!.*interactive interface.*'
                           '1abc\.png.*plot of profile.*'
                           '1abc\.pdb\.dat.*Profile file',
                           re.DOTALL | re.MULTILINE)
            self.assertRegexpMatches(rv.data, r)


if __name__ == '__main__':
    unittest.main()
