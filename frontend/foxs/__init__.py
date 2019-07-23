from flask import render_template
import saliweb.frontend

parameters = []
app = saliweb.frontend.make_application(__name__, parameters)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/help')
def help():
    return render_template('help.html')

