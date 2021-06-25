import os
import re
import collections


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
