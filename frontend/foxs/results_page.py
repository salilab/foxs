import saliweb.frontend
import collections
import os


Result = collections.namedtuple('Result', ['pdb', 'fit_png', 'fit_dat',
                                           'fit_chi', 'fit_c1', 'fit_c2'])


def show_results(job, interactive):
    pdb, profile, email = get_input_data(job)
    results = list(get_results(job, profile))
    return saliweb.frontend.render_results_template("results_old.html", job=job,
        pdb=pdb, profile=profile, email=email, results=results)


def get_results(job, profile):
    """Get a list of Result objects for the given job"""
    profile = os.path.splitext(profile)[0]
    log_results = parse_log(job)
    for pdb in get_pdb_files(job):
        chi, c1, c2 = log_results[pdb]
        pdb = os.path.splitext(pdb)[0]
        yield Result(pdb=pdb, fit_png="%s_%s.png" % (pdb, profile),
                     fit_dat="%s_%s.dat" % (pdb, profile),
                     fit_chi=chi, fit_c1=c1, fit_c2=c2)


def parse_log(job):
    """Get a dict of (chi, c1, c2) values for PDB-file keys"""
    results = {}
    with open(job.get_path('foxs.log')) as fh:
        for line in fh:
            if 'Chi^2' in line:
                s = line.split()
                results[s[0]] = (s[4], s[7], s[10])
    return results


def get_pdb_files(job):
    """Get the PDB files used by a job"""
    with open(job.get_path('inputFiles.txt')) as fh:
        return [l.rstrip('\r\n') for l in fh]


def get_input_data(job):
    """Get the pdb file, profile, email used by a job"""
    with open(job.get_path('data.txt')) as fh:
        return fh.readline().split()[:3]
