import unittest
import foxs
from foxs import run_foxs
import saliweb.test
import saliweb.backend
import os

class Tests(saliweb.test.TestCase):

    def test_job_parameters_no_profile(self):
        """Test JobParameters class without profile"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        d = saliweb.test.RunInDir(j.directory)
        with open('data.txt', 'w') as fh:
            fh.write("PDB - EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
        with open('inputFiles.txt', 'w') as fh:
            fh.write("file1\nfile2\n")
        p = run_foxs.JobParameters()
        self.assertIsNone(p.profile_file_name)
        self.assertEqual(p.pdb_file_names, ['file1', 'file2'])
        self.assertAlmostEqual(p.q, 0.5, delta=1e-4)
        self.assertEqual(p.psize, 500)
        self.assertTrue(p.hlayer)

    def test_job_parameters_with_profile(self):
        """Test JobParameters class with profile"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        d = saliweb.test.RunInDir(j.directory)
        with open('data.txt', 'w') as fh:
            fh.write("PDB PROF EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
        with open('inputFiles.txt', 'w') as fh:
            fh.write("file1\nfile2\n")
        p = run_foxs.JobParameters()
        self.assertEqual(p.profile_file_name, 'PROF')

    def test_get_command_options(self):
        """Test get_command_options()"""
        class MockParameters(object):
            model_option = 3
            unit_option = 1
            q = 1.0
            psize = 10
            pdb_file_names = ['1.pdb', '2.pdb']
            profile_file_name = None
            hlayer = True
            exvolume = True
            ihydrogens = True
            residue = False
            offset = False
            background = False
        p = MockParameters()
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb'])

        # Check run with profile
        p = MockParameters()
        p.profile_file_name = 'PROF'
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                'PROF', '-p'])

        # Check run with hlayer value
        p = MockParameters()
        p.hlayer = False
        p.hlayer_value = 2.0
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                '--min_c2', '2.0', '--max_c2', '2.0'])

        # Check run with exvolume value
        p = MockParameters()
        p.exvolume = False
        p.exvolume_value = 2.0
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                '--min_c1', '2.0', '--max_c1', '2.0'])

        # Check run without ihydrogens
        p = MockParameters()
        p.ihydrogens = False
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                '-h'])

        # Check run with residue
        p = MockParameters()
        p.residue = True
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                '-r'])

        # Check run with offset
        p = MockParameters()
        p.offset = True
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                '-o'])

        # Check run with background
        p = MockParameters()
        p.background = True
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '1.pdb', '2.pdb',
                                '-b', '0.2'])

    def test_set_job_state(self):
        """Test set_job_state()"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        d = saliweb.test.RunInDir(j.directory)
        run_foxs.set_job_state('DONE')
        with open('job-state') as fh:
            contents = fh.read()
        self.assertEqual(contents, 'DONE\n')


if __name__ == '__main__':
    unittest.main()
