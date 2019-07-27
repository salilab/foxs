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
            fh.write("PDB - EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
        with open('inputFiles.txt', 'w') as fh:
            fh.write("file1\nfile2\n")
        cls = j.run()
        self.assertIsInstance(cls, saliweb.backend.LocalRunner)
        self.assertFileContains('run.sh', 'foxs -j -g -m 3 -u 1')

        # Check run with profile
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', 'PROF -p')

        # Check run with hlayer value
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 0 1 1 0 0 0 2.00 1.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', '--min_c2 2.0')

        # Check run with exvolume value
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 0 1 0 0 0 0.00 4.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', '--min_c1 4.0')

        # Check run without ihydrogens
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 0 0 0 0 0.00 1.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', ' -h ')

        # Check run with residue
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 1 1 0 0 0.00 1.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', ' -r ')

        # Check run with offset
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 1 0 1 0 0.00 1.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', ' -o ')

        # Check run with background
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 1 0 0 1 0.00 1.00 3 1\n")
        cls = j.run()
        self.assertFileContains('run.sh', ' -b 0.2')

    def assertFileContains(self, filename, text):
        """Assert that the given file exists and contains the given text"""
        with open(filename) as fh:
            contents = fh.read()
        self.assertIn(text, contents)


if __name__ == '__main__':
    unittest.main()
