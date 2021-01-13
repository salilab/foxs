from flask import render_template, request, send_from_directory
import saliweb.frontend
from saliweb.frontend import get_completed_job
from . import submit_page, results_page


parameters = []
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


@app.route('/links')
def links():
    return render_template('links.html')


@app.route('/help')
def help():
    return render_template('help.html')


@app.route('/job', methods=['GET', 'POST'])
def job():
    if request.method == 'GET':
        return saliweb.frontend.render_queue_page()
    else:
        return submit_page.handle_new_job()


@app.route('/job/<name>')
def results(name):
    job = get_completed_job(name, request.args.get('passwd'))
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
