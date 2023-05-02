import unittest
import foxs
from foxs import run_foxs
import saliweb.test
import saliweb.backend
import os
import tempfile
import contextlib


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


class MockRunSubprocess(object):
    def __init__(self):
        self.cmds = []

    def __call__(self, cmd):
        self.cmds.append(cmd)


@contextlib.contextmanager
def mocked_run_subprocess():
    """Temporarily replace run_foxs.run_subprocess with a mock"""
    old_rs = run_foxs.run_subprocess
    run_foxs.run_subprocess = mock_rs = MockRunSubprocess()
    yield mock_rs
    run_foxs.run_subprocess = old_rs


class Tests(saliweb.test.TestCase):

    def test_job_parameters_no_profile(self):
        """Test JobParameters class without profile"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        with saliweb.test.working_directory(j.directory):
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
        with saliweb.test.working_directory(j.directory):
            with open('data.txt', 'w') as fh:
                fh.write("PDB PROF EMAIL 0.50 500 1 1 1 0 0 0 0.00 1.00 3 1\n")
            with open('inputFiles.txt', 'w') as fh:
                fh.write("file1\nfile2\n")
            p = run_foxs.JobParameters()
            self.assertEqual(p.profile_file_name, 'PROF')

    def test_get_command_options(self):
        """Test get_command_options()"""
        p = MockParameters()
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '--',
                                '1.pdb', '2.pdb'])

        # Check run with profile
        p = MockParameters()
        p.profile_file_name = 'PROF'
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '-p', '--',
                                '1.pdb', '2.pdb', 'PROF'])

        # Check run with hlayer value
        p = MockParameters()
        p.hlayer = False
        p.hlayer_value = 2.0
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10',
                                '--min_c2', '2.0', '--max_c2', '2.0', '--',
                                '1.pdb', '2.pdb'])

        # Check run with exvolume value
        p = MockParameters()
        p.exvolume = False
        p.exvolume_value = 2.0
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10',
                                '--min_c1', '2.0', '--max_c1', '2.0', '--',
                                '1.pdb', '2.pdb'])

        # Check run without ihydrogens
        p = MockParameters()
        p.ihydrogens = False
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '-h', '--',
                                '1.pdb', '2.pdb'])

        # Check run with residue
        p = MockParameters()
        p.residue = True
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '-r', '--',
                                '1.pdb', '2.pdb'])

        # Check run with offset
        p = MockParameters()
        p.offset = True
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '-o', '--',
                                '1.pdb', '2.pdb'])

        # Check run with background
        p = MockParameters()
        p.background = True
        opts, mf_opts = run_foxs.get_command_options(p)
        self.assertEqual(opts, ['-j', '-g', '-m', '3', '-u', '1',
                                '-q', '1.0', '-s', '10', '-b', '0.2', '--',
                                '1.pdb', '2.pdb'])

    def test_set_job_state(self):
        """Test set_job_state()"""
        j = self.make_test_job(foxs.Job, 'RUNNING')
        with saliweb.test.working_directory(j.directory):
            run_foxs.set_job_state('DONE')
            with open('job-state') as fh:
                contents = fh.read()
            self.assertEqual(contents, 'DONE\n')

    def test_make_gnuplot_canvas_plot(self):
        """Test make_gnuplot_canvas_plot()"""
        with saliweb.test.temporary_working_directory():
            with mocked_run_subprocess() as mock:
                run_foxs.make_gnuplot_canvas_plot(max_states=5, profile='PROF')
                self.assertEqual(
                    mock.cmds, [['gnuplot', 'canvas_ensemble.plt']])
            with open('canvas_ensemble.plt') as fh:
                contents = fh.read()
            self.assertIn("set output 'jsoutput.3.js'", contents)
            self.assertIn('multi_state_model_1_1_1.fit', contents)
            self.assertIn('multi_state_model_5_1_1.fit', contents)
            self.assertIn("plot 'PROF'", contents)

    def test_get_min_max_score(self):
        """Test get_min_max_score()"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ensemble_file = os.path.join(tmpdir, 'ensembles_size_2.txt')
            with open(ensemble_file, 'w') as fh:
                fh.write("""
1 |  0.04 | x1 0.05 (1.02, 1.66)
    2   | 0.521 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
    3   | 0.479 (0.612, 0.113) | nodes18_m33.pdb.dat (0.035)
2 |  0.07 | x1 0.05 (1.02, 1.84)
    2   | 0.559 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
   10   | 0.441 (0.481, 0.108) | nodes63_m9.pdb.dat (0.018)
garbage |  0.06 | x1 0.06 (1.03, 1.66)
3 |  0.20 | x1 0.06 (1.03, 1.66)
    2   | 0.660 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
   34   | 0.340 (0.377, 0.081) | nodes19_m86.pdb.dat (0.012)
4 |  0.30 | x1 0.06 (1.02, 1.66)
    2   | 0.611 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
   15   | 0.389 (0.498, 0.098) | nodes54_m72.pdb.dat (0.038)
""")
            (number_of_states, first_score,
             diff) = run_foxs.get_min_max_score(ensemble_file, 3)
            self.assertEqual(number_of_states, 2)
            self.assertAlmostEqual(first_score, 0.04, delta=0.01)
            self.assertAlmostEqual(diff, 0.16, delta=0.01)

    def test_plot_states_histogram_small_diff(self):
        """Test plot_states_histogram() with diff smaller than score"""
        with saliweb.test.temporary_working_directory():
            ensemble_file = 'ensembles_size_1.txt'
            with open(ensemble_file, 'w') as fh:
                fh.write("""
1 |  0.04 | x1 0.05 (1.02, 1.66)
    2   | 0.521 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
""")
            with mocked_run_subprocess() as mock:
                run_foxs.plot_states_histogram(max_states=5, max_models=10)
                self.assertEqual(mock.cmds, [['gnuplot', 'plotbar3.plt']])
            with open('chis') as fh:
                contents = fh.read()
            num_states, first_score, diff = contents.rstrip('\r\n').split()
            self.assertEqual(int(num_states), 1)
            self.assertAlmostEqual(float(first_score), 0.04, delta=0.01)
            self.assertAlmostEqual(float(diff), 0.0, delta=0.01)
            with open('plotbar3.plt') as fh:
                contents = fh.read()
            self.assertIn('set output "chis.png"', contents)
            self.assertIn("plot 'chis' u 1:2:3", contents)

    def test_plot_states_histogram_big_diff(self):
        """Test plot_states_histogram() with diff larger than score"""
        with saliweb.test.temporary_working_directory():
            ensemble_file = 'ensembles_size_1.txt'
            with open(ensemble_file, 'w') as fh:
                fh.write("""
1 |  0.04 | x1 0.05 (1.02, 1.66)
    2   | 0.521 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
2 |  0.14 | x1 0.05 (1.02, 1.66)
    2   | 0.521 (0.698, 0.077) | nodes98_m49.pdb.dat (0.058)
""")
            with mocked_run_subprocess() as mock:
                run_foxs.plot_states_histogram(max_states=5, max_models=10)
                self.assertEqual(mock.cmds, [['gnuplot', 'plotbar3.plt']])

    def test_run_job_no_pngs(self):
        """Test run_job failure (no pngs produced)"""
        p = MockParameters()
        with saliweb.test.temporary_working_directory():
            with mocked_run_subprocess():
                self.assertRaises(RuntimeError, run_foxs.run_job, p)

    def test_run_job_ok_one_pdb(self):
        """Test run_job success with one PDB"""
        p = MockParameters()
        with saliweb.test.temporary_working_directory():
            # Simulate production of plot png
            with open('pdb6lyt_lyzexp.png', 'w') as fh:
                fh.write('\n')
            with mocked_run_subprocess():
                run_foxs.run_job(p)

    def test_run_job_ok_multimodel_pdb(self):
        """Test run_job success with multimodel PDB"""
        p = MockParameters()
        p.model_option = 2
        p.pdb_file_names = ['1.pdb', '2.pdb', '4.pdb']
        with saliweb.test.temporary_working_directory():
            with open('1.pdb', 'w') as fh:
                fh.write("HEADER\nMODEL  \nATOM line1\nline2\nENDMDL\n"
                         # empty model in middle of file
                         "MODEL  \nENDMDL\n"
                         "MODEL  \nATOM line3\nline4\nENDMDL\n"
                         # empty model at end of file
                         "MODEL  \nnot-atom-line\nENDMDL\n"
                         "END\n")
            with open('2.pdb', 'w') as fh:
                fh.write("HEADER\nEND\n")
            with open('3.pdb', 'w') as fh:
                fh.write("HEADER\nMODEL  \nATOM line1\nline2\nENDMDL\nEND\n")
            with open('4.pdb', 'w') as fh:
                fh.write("HEADER\nMODEL  \nATOM line1\nline2\n"
                         "MODEL  \nHETATM line3\nline4\nEND\n")
            # Simulate production of plot png
            with open('pdb6lyt_lyzexp.png', 'w') as fh:
                fh.write('\n')
            with mocked_run_subprocess():
                run_foxs.run_job(p)
            # Should have made multimodel list and files
            os.unlink("1_m1.pdb")
            os.unlink("1_m2.pdb")
            os.unlink("4_m1.pdb")
            os.unlink("4_m2.pdb")
            self.assertFalse(os.path.exists("1_m3.pdb"))
            self.assertFalse(os.path.exists("2_m1.pdb"))
            self.assertFalse(os.path.exists("3_m1.pdb"))
            os.unlink("multi-model-files.txt")

    def test_run_job_no_ensemble(self):
        """Test run_job failure (no MultiFoXS ensemble produced)"""
        p = MockParameters()
        p.profile_file_name = 'PROF'
        with saliweb.test.temporary_working_directory():
            # Simulate production of plot png
            with open('pdb6lyt_lyzexp.png', 'w') as fh:
                fh.write('\n')
            # Simulate dat files
            with open('1.pdb.dat', 'w') as fh:
                fh.write('\n')
            with open('2_m1.pdb.dat', 'w') as fh:
                fh.write('\n')
            with open('2_m2.pdb.dat', 'w') as fh:
                fh.write('\n')
            with mocked_run_subprocess():
                self.assertRaises(RuntimeError, run_foxs.run_job, p)


if __name__ == '__main__':
    unittest.main()
