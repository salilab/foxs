from flask import render_template, request, send_from_directory
import saliweb.frontend
from saliweb.frontend import get_completed_job, Parameter, FileParameter
from . import submit_page, results_page


parameters = [Parameter("jobname", "Job name", optional=True),
              Parameter("pdb", "PDB code and chain ID to fit", optional=True),
              FileParameter("pdbfile", "PDB file to fit", optional=True),
              FileParameter("profile", "Experimental SAXS profile"),
              Parameter("q", "Maximal q value", optional=True),
              Parameter("psize", "Profile size", optional=True),
              Parameter("hlayer", "Use hydration layer to improve fitting",
                        optional=True),
              Parameter("c2", "Fix hydration layer density",
                        optional=True),
              Parameter(
                  "exvolume",
                  "Adjust the protein excluded volume to improve fitting",
                  optional=True),
              Parameter("c1", "Fix excluded volume", optional=True),
              Parameter("ihydrogens", "Implicitly consider hydrogen atoms",
                        optional=True),
              Parameter(
                  "residue",
                  "Perform coarse grained profile computation for "
                  "Ca atoms only", optional=True),
              Parameter(
                  "background",
                  "Adjust the background of the experimental profile",
                  optional=True),
              Parameter("offset", "Use offset in profile fitting",
                        optional=True),
              Parameter("modelread",
                        "Determine how to read PDB files with MODEL records",
                        optional=True),
              Parameter("units", "Experimental profile units", optional=True)]
app = saliweb.frontend.make_application(__name__, parameters)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/download')
def download():
    return render_template('download.html')


@app.route('/links')
def links():
    return render_template('links.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/help_multi')
def help_multi():
    return render_template('help_multi.html')


@app.route('/job', methods=['GET', 'POST'])
def job():
    if request.method == 'GET':
        return saliweb.frontend.render_queue_page()
    else:
        return submit_page.handle_new_job()


@app.route('/job/<name>')
def results(name):
    job = get_completed_job(name, request.args.get('passwd'),
                            still_running_template='running.html')
    return results_page.show_results(job, interactive=True)


@app.route('/job/<name>/old')
def results_old(name):
    job = get_completed_job(name, request.args.get('passwd'))
    return results_page.show_results(job, interactive=False)


@app.route('/job/<name>/ensemble')
def ensemble(name):
    job = get_completed_job(name, request.args.get('passwd'))
    return results_page.show_ensemble(job)


@app.route('/job/<name>/<path:fp>')
def results_file(name, fp):
    job = get_completed_job(name, request.args.get('passwd'))
    return send_from_directory(job.directory, fp)
