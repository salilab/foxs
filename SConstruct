import saliweb.build

vars = Variables('config.py')
env = saliweb.build.Environment(vars, ['conf/live.conf'], service_module='foxs')
Help(vars.GenerateHelpText(env))

env.InstallAdminTools()

Export('env')
SConscript('frontend/foxs/SConscript')
SConscript('backend/foxs/SConscript')
SConscript('test/SConscript')
