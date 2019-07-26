import unittest
import foxs
import saliweb.test
import saliweb.backend
import os

class JobTests(saliweb.test.TestCase):

    def test_run_ok(self):
        """Test successful run method"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        d = saliweb.test.RunInDir(j.directory)
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
        with open('inputFiles.txt', 'w') as fh:
            fh.write("file1\nfile2\n")
        cls = j.run()
        self.assertIsInstance(cls, saliweb.backend.LocalRunner)


if __name__ == '__main__':
    unittest.main()
