import unittest
import foxs
import saliweb.test
import saliweb.backend


class JobTests(saliweb.test.TestCase):

    def test_run_ok(self):
        """Test successful run method"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        with saliweb.test.working_directory(j.directory):
            with open('data.txt', 'w') as fh:
                fh.write("PDB - EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            with open('inputFiles.txt', 'w') as fh:
                fh.write("file1\nfile2\n")
            cls = j.run()
            self.assertIsInstance(cls, saliweb.backend.LocalRunner)

    def test_postprocess_ok(self):
        """Test successful postprocess"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        with saliweb.test.working_directory(j.directory):
            with open('foxs.log', 'w') as fh:
                fh.write('no error\n')
            j.postprocess()

    def test_postprocess_fail(self):
        """Test postprocess with failed job"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        with saliweb.test.working_directory(j.directory):
            with open('foxs.log', 'w') as fh:
                fh.write('Traceback (most recent call last):\n')
            self.assertRaises(foxs.LogError, j.postprocess)


if __name__ == '__main__':
    unittest.main()
