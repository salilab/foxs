import saliweb.frontend
import collections
import os


Fit = collections.namedtuple('Fit', ['png', 'dat', 'chi', 'c1', 'c2'])

Profile = collections.namedtuple('Profile', ['png', 'dat'])

Result = collections.namedtuple('Result', ['pdb', 'fit', 'profile'])


def show_results(job, interactive):
    pdb, profile, email = get_input_data(job)
    results = list(get_results(job, profile))
    return saliweb.frontend.render_results_template("results_old.html", job=job,
        pdb=pdb, profile=profile, email=email, results=results)


def get_results(job, profile):
    """Get a list of Result objects for the given job"""
    profile = os.path.splitext(profile)[0]
    log_results = parse_log(job)
    for pdb_file in get_pdb_files(job):
        pdb = os.path.splitext(pdb_file)[0]
        if profile != '-':
            chi, c1, c2 = log_results[pdb]
            f = Fit(png="%s_%s.png" % (pdb, profile),
                    dat="%s_%s.dat" % (pdb, profile),
                    chi=chi, c1=c1, c2=c2)
        else:
            f = None
        p = Profile(png="%s.png" % pdb, dat="%s.dat" % pdb_file)
        yield Result(pdb=pdb, fit=f, profile=p)


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
