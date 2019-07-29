import saliweb.backend
import os


class Job(saliweb.backend.Job):

    runnercls = saliweb.backend.LocalRunner

    def run(self):
        with open('data.txt') as fh:
            line = fh.readline().rstrip('\r\n')
        (prot_file_name, profile_file_name, email, q, psize,
         hlayer, exvolume, ihydrogens, residue, offset,
         background, hlayer_value, exvolume_value, model_option,
         unit_option) = line.split()
        q = float(q)
        psize = int(psize)
        hlayer = hlayer == "1"
        exvolume = exvolume == "1"
        ihydrogens = ihydrogens == "1"
        residue = residue == "1"
        offset = offset == "1"
        background = background == "1"
        hlayer_value = float(hlayer_value)
        exvolume_value = float(exvolume_value)
        model_option = int(model_option)
        unit_option = int(unit_option)
        with open('inputFiles.txt') as fh:
            files = [f.strip() for f in fh]

        cmd = ("foxs -j -g -m %(model_option)d -u %(unit_option)d "
               "-q %(q)f -s %(psize)d " % locals()
               + " ".join(files))
        mf_cmd = ("multi_foxs -u %(unit_option)d -q %(q)f "
                  "%(profile_file_name)s " % locals()
                  + " ".join(files))
        if profile_file_name != '-':
            cmd += " %s -p" % profile_file_name
        if not hlayer:
            c = " --min_c2 %f --max_c2 %f" % (hlayer_value, hlayer_value)
            cmd += c
            mf_cmd += c
        if not exvolume:
            c = " --min_c1 %f --max_c1 %f" % (exvolume_value, exvolume_value)
            cmd += c
            mf_cmd += c
        if not ihydrogens:
            cmd += " -h "
        if residue:
            cmd += " -r "
        if offset:
            cmd += " -o "
            mf_cmd += " -o "
        if background:
            cmd += " -b 0.2"
            mf_cmd += " -b 0.2"

        script = """#!/bin/sh
echo STARTED > job-state
. /etc/profile
module load imp gnuplot
%s
gnuplot *.plt >& glog
echo DONE > job-state
""" % cmd
        with open('run.sh', 'w') as fh:
            fh.write(script)
        os.chmod('run.sh', 0755)
        return self.runnercls("cd %s; ./run.sh >& foxs.log" % os.getcwd())


def get_web_service(config_file):
    db = saliweb.backend.Database(Job)
    config = saliweb.backend.Config(config_file)
    return saliweb.backend.WebService(config, db)

