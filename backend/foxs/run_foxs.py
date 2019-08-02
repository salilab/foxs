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


def run_job(p):
    cmd = ['foxs', '-j', '-g', '-m', str(p.model_option),
           '-u', str(p.unit_option), '-q' , str(p.q),
           '-s', str(p.psize)] + p.pdb_file_names
    mf_cmd = ['multi_foxs', '-u', str(p.unit_option), '-q', str(p.q),
              p.profile_file_name] + p.pdb_file_names

    if p.profile_file_name:
        cmd.extend((p.profile_file_name, '-p'))
    if not p.hlayer:
        c = ['--min_c2', str(p.hlayer_value), '--max_c2', str(p.hlayer_value)]
        cmd.extend(c)
        mf_cmd.extend(c)
    if not p.exvolume:
        c = ['--min_c1', str(p.exvolume_value),
             '--max_c1', str(p.exvolume_value)]
        cmd.extend(c)
        mf_cmd.extend(c)
    if not p.ihydrogens:
        cmd.append('-h')
    if p.residue:
        cmd.append('-r')
    if p.offset:
        cmd.append('-o')
        mf_cmd.append('-o')
    if p.background:
        cmd.extend(('-b', '0.2'))
        mf_cmd.extend(('-b', '0.2'))

    # Run FoXS
    run_subprocess(cmd)
    # Make plots
    run_subprocess(['gnuplot'] + glob.glob('*.plt'))


def run_subprocess(cmd):
    """Run and log a subprocess"""
    print(" ".join(cmd))
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
