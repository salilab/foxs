import saliweb.backend
import os
from . import run_foxs


class Job(saliweb.backend.Job):

    runnercls = saliweb.backend.LocalRunner

    def run(self):
        # Simply run the run_foxs Python file in the job directory
        foxs_path = os.path.abspath(os.path.dirname(run_foxs.__file__))
        cmd = ['python2', os.path.join(foxs_path, run_foxs.__name__ + '.py')]
        return self.runnercls(cmd)


def get_web_service(config_file):
    db = saliweb.backend.Database(Job)
    config = saliweb.backend.Config(config_file)
    return saliweb.backend.WebService(config, db)

