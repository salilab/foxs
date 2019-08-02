from __future__ import print_function
import sys
import os
import subprocess
import glob


class JobParameters(object):
    """Store job parameters read from files created by the frontend"""
    def __init__(self):
        with open('data.txt') as fh:
            line = fh.readline().rstrip('\r\n')
        (prot_file_name, self.profile_file_name, email, q, psize, hlayer,
         exvolume, ihydrogens, residue, offset, background, hlayer_value,
         exvolume_value, model_option, unit_option) = line.split()
        if self.profile_file_name == '-':
            self.profile_file_name = None
        self.q = float(q)
        self.psize = int(psize)
        self.hlayer = hlayer == "1"
        self.exvolume = exvolume == "1"
        self.ihydrogens = ihydrogens == "1"
        self.residue = residue == "1"
        self.offset = offset == "1"
        self.background = background == "1"
        self.hlayer_value = float(hlayer_value)
        self.exvolume_value = float(exvolume_value)
        self.model_option = int(model_option)
        self.unit_option = int(unit_option)
        with open('inputFiles.txt') as fh:
            self.pdb_file_names = [f.strip() for f in fh]


def set_job_state(state):
    """Write the current state of the job to the job-state file"""
    with open('job-state', 'w') as fh:
        fh.write(state + '\n')


def setup_environment():
    """Set up the environment for the job so we can find FoXS, etc."""
    # Add IMP and gnuplot to the path, using modules
    sys.path.append(os.path.join(os.environ['MODULESHOME'], 'init'))
    from python import module
    module(['load', 'imp', 'gnuplot'])


def get_command_options(p):
    """Get command line options for FoXS and MultiFoXS"""
    foxs_opts = ['-j', '-g', '-m', str(p.model_option),
                 '-u', str(p.unit_option), '-q' , str(p.q),
                 '-s', str(p.psize)] + p.pdb_file_names
    mf_opts = ['-u', str(p.unit_option), '-q', str(p.q)]

    if p.profile_file_name:
        foxs_opts.extend((p.profile_file_name, '-p'))
    if not p.hlayer:
        c = ['--min_c2', str(p.hlayer_value), '--max_c2', str(p.hlayer_value)]
        foxs_opts.extend(c)
        mf_opts.extend(c)
    if not p.exvolume:
        c = ['--min_c1', str(p.exvolume_value),
             '--max_c1', str(p.exvolume_value)]
        foxs_opts.extend(c)
        mf_opts.extend(c)
    if not p.ihydrogens:
        foxs_opts.append('-h')
    if p.residue:
        foxs_opts.append('-r')
    if p.offset:
        foxs_opts.append('-o')
        mf_opts.append('-o')
    if p.background:
        foxs_opts.extend(('-b', '0.2'))
        mf_opts.extend(('-b', '0.2'))
    return foxs_opts, mf_opts


def run_job(params):
    print("Start profile computation analysis")

    foxs_opts, multi_foxs_opts = get_command_options(params)
    # Run FoXS
    run_subprocess(['foxs'] + foxs_opts)
    # Make plots
    run_subprocess(['gnuplot'] + glob.glob('*.plt'))

    png_files = glob.glob("*.png")
    if len(png_files) == 0:
        raise RuntimeError("No plot pngs produced")

    # Run MultiFoXS if necessary
    dat_files = glob.glob("*.pdb.dat")
    if ((len(params.pdb_file_names) > 1 or len(dat_files) > 1)
        and params.profile_file_name):
        run_multifoxs(params, multi_foxs_opts)


def run_multifoxs(params, mf_opts):
    # validate exp. profile, add error if needed
    run_subprocess(['validate_profile', params.profile_file_name,
                    '-q', str(params.q)])
    validated_profile_name = (os.path.splitext(params.profile_file_name)[0]
                              + '_v.dat')

    file_counter = 0
    with open('filenames2.txt', 'w') as fh:
        for pdb in params.pdb_file_names:
            for dat_file in dat_files_for_pdb(pdb):
                fh.write(dat_file + '\n')
                file_counter += 1
    # determine maximal subset size
    max_subset_size = min(5, file_counter)

    print("Start Ensemble computation")
    run_subprocess(['multi_foxs', validated_profile_name, 'filenames2.txt',
                    '-s', str(max_subset_size)] + mf_opts)
    if not os.path.exists('ensembles_size_1.txt'):
        raise RuntimeError("No MultiFoXS ensembles produced")


def dat_files_for_pdb(pdb):
    """Get all dat files for a given PDB"""
    dat_file = pdb + '.dat'
    if os.path.exists(dat_file):
        yield dat_file
    else:  # multi model file
        pdb_code = os.path.splitext(pdb)[0]
        for i in range(1, 101):
            dat_file = "%s_m%d.pdb.dat" % (pdb_code, i)
            if os.path.exists(dat_file):
                yield dat_file


def run_subprocess(cmd):
    """Run and log a subprocess"""
    # Ensure that output from subprocess shows up in the right place in the log
    sys.stdout.flush()
    subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)


def main():
    set_job_state('STARTED')
    try:
        # Send our own error/output to a log file
        sys.stdout = sys.stderr = open('foxs.log', 'w')
        setup_environment()
        params = JobParameters()
        run_job(params)
    finally:
        set_job_state('DONE')


if __name__ == '__main__':
    main()
