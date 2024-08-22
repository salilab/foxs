from flask import url_for
import saliweb.frontend
import collections
import os
import re
import glob
from .ensemble import get_multi_state_models, get_bokeh, get_chi_plot


Fit = collections.namedtuple('Fit', ['png', 'dat', 'chi', 'c1', 'c2'])


Profile = collections.namedtuple('Profile', ['png', 'dat'])


Result = collections.namedtuple(
    'Result', ['pdb', 'pdb_file', 'fit', 'profile'])


class JMolTableReader(object):
    """Functor to read jmol info"""
    def __init__(self, job):
        self.job = job

    def __call__(self):
        with open(self.job.get_path('jmoltable.html')) as fh:
            contents = fh.read()
        # Fix link to per-job PDB or mmCIF file
        contents = contents.replace(
            'load jmoltable.pdb',
            'load "' + self.job.get_results_file_url('jmoltable.pdb') + '"')
        contents = contents.replace(
            'load jmoltable.cif',
            'load "' + self.job.get_results_file_url('jmoltable.cif') + '"')
        # Fix URL for our copy of JSmol
        contents = contents.replace('/foxs/jsmol', '/jsmol')
        # Fix bug with show all/hide all checkbox
        contents = re.sub(r'jmolSetCheckboxGroup\(0,([^)]+)\)',
                          r'Jmol.setCheckboxGroup(0,[\1])', contents)
        # Add an ID to the info table so we can style it with CSS
        contents = contents.replace('<table ', '<table id="plotcontrol" ')

        # Fix hard-coded links to help page
        def help_url(match):
            anchor = match.group(1)
            url = url_for("help", _anchor=anchor)
            if anchor == 'c1c2':
                return ('%s" title="This value may indicate data overfitting'
                        % url)
            else:
                return url
        contents = re.sub(r'https:\/\/modbase\.compbio\.ucsf\.edu\/'
                          r'foxs\/help\.html#(\w+)', help_url, contents)

        # Fix links to job results files
        def get_upl(match):
            return self.job.get_results_file_url(match.group(1))
        return re.sub('dirname/([^"]+)', get_upl, contents)


def show_results(job, interactive):
    pdb, profile = get_input_data(job)
    # If no plots were produced, there must be a problem with user inputs
    if len(glob.glob(job.get_path("*.png"))) == 0:
        return saliweb.frontend.render_results_template(
            'results_failed.html', job=job,
            pdb=pdb, profile=profile)
    results = list(get_results(job, profile))
    if results[0].fit:
        png = results[0].fit.png
    else:
        png = results[0].profile.png
    if not os.path.exists(job.get_path(png)):
        return saliweb.frontend.render_results_template(
            'results_failed.html', job=job,
            pdb=pdb, profile=profile)

    allresult = None
    if len(results) > 1:
        fit = None if profile == '-' else Fit(png='fit.png', dat=None,
                                              chi=None, c1=None, c2=None)
        allresult = Result(pdb=None, pdb_file=None, fit=fit,
                           profile=Profile(png='profiles.png', dat=None))
    template = 'results.html' if interactive else 'results_old.html'
    return saliweb.frontend.render_results_template(
        template, job=job,
        pdb=pdb, profile=profile, results=results,
        allresult=allresult, include_jmoltable=JMolTableReader(job))


def show_ensemble(job):
    max_states = 4  # should match that in backend/foxs/run_foxs.py
    pdb, profile = get_input_data(job)
    if not os.path.exists(job.get_path("chis")):
        return saliweb.frontend.render_results_template(
            'ensemble_failed.html', job=job,
            pdb=pdb, profile=profile)
    else:
        return saliweb.frontend.render_results_template(
            'ensemble.html', job=job,
            bokeh=get_bokeh(), chiplot=get_chi_plot(job),
            pdb=pdb, profile=profile, max_states=max_states,
            multi_state_models=list(get_multi_state_models(job, max_states)))


def get_results(job, profile):
    """Get a list of Result objects for the given job"""
    profile = os.path.splitext(profile)[0]
    log_results = parse_log(job)
    for pdb_file in get_pdb_files(job):
        pdb = os.path.splitext(pdb_file)[0]
        if profile != '-':
            chi, c1, c2 = log_results[pdb_file]
            f = Fit(png="%s_%s.png" % (pdb, profile),
                    dat="%s_%s.dat" % (pdb, profile),
                    chi=chi, c1=c1, c2=c2)
        else:
            f = None
        p = Profile(png="%s.png" % pdb, dat="%s.dat" % pdb_file)
        yield Result(pdb=pdb, pdb_file=pdb_file, fit=f, profile=p)


def parse_log(job):
    """Get a dict of (chi, c1, c2) values for PDB-file keys"""
    results = {}
    with open(job.get_path('foxs.log'), encoding='latin1') as fh:
        for line in fh:
            if 'Chi^2' in line:
                s = line.split()
                results[s[0]] = (s[4], s[7], s[10])
    return results


def get_pdb_files(job):
    """Get the PDB files used by a job"""
    fname = job.get_path('multi-model-files.txt')
    if not os.path.exists(fname):
        fname = job.get_path('inputFiles.txt')
    with open(fname) as fh:
        return [line.rstrip('\r\n') for line in fh]


def get_input_data(job):
    """Get the pdb file and profile used by a job"""
    with open(job.get_path('data.txt')) as fh:
        return fh.readline().split()[:2]
