import saliweb.backend
import os
from . import run_foxs


class LogError(Exception):
    pass


class Job(saliweb.backend.Job):

    runnercls = saliweb.backend.LocalRunner

    def run(self):
        # Simply run the run_foxs Python file in the job directory
        foxs_path = os.path.abspath(os.path.dirname(run_foxs.__file__))
        cmd = ['python2', os.path.join(foxs_path, run_foxs.__name__ + '.py')]
        return self.runnercls(cmd)

    def postprocess(self):
        # Check for errors in foxs.log
        with open('foxs.log') as fh:
            for line in fh:
                if 'Traceback' in line:
                    raise LogError("Error in foxs.log: " + line)


def get_web_service(config_file):
    db = saliweb.backend.Database(Job)
    config = saliweb.backend.Config(config_file)
    return saliweb.backend.WebService(config, db)
