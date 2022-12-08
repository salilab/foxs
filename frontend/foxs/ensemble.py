import os
import re
import collections
import bokeh
import bokeh.resources
import bokeh.embed
import bokeh.plotting
from bokeh.models.tools import HoverTool
from bokeh.models.ranges import Range1d


PDB = collections.namedtuple('PDB', ['filename', 'rg', 'weight', 'num'])


class MultiStateModel(object):
    def __init__(self, job, state_num, model_num, ensemble_filename,
                 color, rg):
        self.state_num, self.color = state_num, color
        self.model_num = model_num
        with open(ensemble_filename) as fh:
            self.score, self.c1, self.c2 = self._read_ensemble_file(
                                                    fh, model_num)
            self.pdbs = list(self._get_pdbs(job, fh, rg))
        self.dat_file = "multi_state_model_%d_1_1.dat" % state_num
        self.fit_file = "multi_state_model_%d_1_1.fit" % state_num

    def _get_pdbs(self, job, fh, rg):
        linere = re.compile(r'\| ([\d.]+) \([\d.]+, [\d.]+\) \| (\S+).dat')
        for i in range(self.state_num):
            line = fh.readline()
            m = linere.search(line)
            w1 = float(m.group(1))
            pdb = m.group(2)
            yield PDB(filename=pdb, rg=rg[pdb], weight=w1, num=i)

    def _read_ensemble_file(self, fh, model_num):
        for line in fh:
            if ' x1 ' in line:
                tmp = line.split('|')
                if len(tmp) > 1 and tmp[0].strip().isdigit():
                    if int(tmp[0]) == model_num:
                        score = float(tmp[1])
                        c1c2 = tmp[2].split('(')[1].split(')')[0].split(',')
                        c1 = float(c1c2[0])
                        c2 = float(c1c2[1])
                        return score, c1, c2
        raise ValueError("Could not find ensemble")


def read_rg(fh):
    rgre = re.compile(r'(.*) Rg=\s+([\d.]+)')

    rg = {}
    for line in fh:
        m = rgre.match(line)
        rg[m.group(1).strip()] = float(m.group(2))
    return rg


def get_multi_state_models(job, max_state):
    colors = ["x1a9850",  # green
              "xe26261",  # red
              "x3288bd",  # blue
              "x00FFFF",
              "xA6CEE3"]
    with open(job.get_path("rg")) as fh:
        rg = read_rg(fh)
    for size in range(2, max_state + 1):
        fn = job.get_path("ensembles_size_%d.txt" % size)
        if os.path.exists(fn):
            yield MultiStateModel(job, size, 1, fn, colors[size-1], rg)


def get_bokeh():
    """Return info for getting BokehJS from its CDN"""
    js = 'bokeh-%s.min.js' % bokeh.__version__
    jshash = bokeh.resources.get_sri_hashes_for_version(bokeh.__version__)[js]
    return {'js': js, 'hash': jshash}


def get_chi_plot_source(job):
    """Read the chis file and return a bokeh data source"""
    nstate = []
    val = []
    valerr = []
    desc = []
    with open(job.get_path('chis')) as fh:
        for line in fh:
            s = line.split()
            if len(s) != 3:
                continue
            nstate.append(int(s[0]))
            val.append(float(s[1]))
            err = float(s[2])
            valerr.append(val[-1] + err)
            desc.append("%.2f ± %.2f" % (val[-1], err))
    return bokeh.plotting.ColumnDataSource(
        data={'nstate': nstate, 'val': val, 'desc': desc, 'valerr': valerr})


def get_chi_plot(job):
    """Render the chi vs #state plot using Bokeh"""
    source = get_chi_plot_source(job)
    # If the error bars are huge, truncate them so we can see the best chi
    # in the default view
    ymax = min(max(source.data['val'])*2.,
               max(source.data['valerr'])+0.01)
    p = bokeh.plotting.figure(
        x_axis_label='# of states', y_axis_label='χ²',
        width=300, height=250,
        y_range=Range1d(0, ymax, bounds=(0, None)))
    p.xaxis.ticker = source.data['nstate']
    p.yaxis.axis_label_text_font_style = 'normal'
    p.yaxis.axis_label_text_font_size = '1.2em'
    p.xaxis.axis_label_text_font_style = 'normal'
    p.xaxis.axis_label_text_font_size = '1.2em'
    p.xgrid.visible = p.ygrid.visible = False
    p.toolbar.autohide = True
    p.outline_line_color = None

    p.add_tools(HoverTool(tooltips="@desc"))

    p.segment(x0='nstate', x1='nstate', y0='val', y1='valerr', source=source)
    p.rect('nstate', 'valerr', 0.1, 0.01, source=source)
    p.vbar(x='nstate', top='val', width=0.2, source=source,
           hover_line_color='black', line_color=None)

    script, div = bokeh.embed.components(p)
    return {'js': script, 'div': div}
