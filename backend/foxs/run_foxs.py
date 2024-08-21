from __future__ import print_function
import sys
import os
import contextlib
import subprocess
import glob
import traceback
import ihm.format


class JobParameters(object):
    """Store job parameters read from files created by the frontend"""
    def __init__(self):
        with open('data.txt') as fh:
            line = fh.readline().rstrip('\r\n')
        (prot_file_name, self.profile_file_name, email, q, psize, hlayer,
         exvolume, ihydrogens, residue, offset, background, hlayer_value,
         exvolume_value, model_option, unit_option) = line.split()
        if self.profile_file_name == '-':
            self.profile_file_name = None
        self.q = float(q)
        self.psize = int(psize)
        self.hlayer = hlayer == "1"
        self.exvolume = exvolume == "1"
        self.ihydrogens = ihydrogens == "1"
        self.residue = residue == "1"
        self.offset = offset == "1"
        self.background = background == "1"
        self.hlayer_value = float(hlayer_value)
        self.exvolume_value = float(exvolume_value)
        self.model_option = int(model_option)
        self.unit_option = int(unit_option)
        with open('inputFiles.txt') as fh:
            self.pdb_file_names = [f.strip() for f in fh]


def set_job_state(state):
    """Write the current state of the job to the job-state file"""
    with open('job-state', 'w') as fh:
        fh.write(state + '\n')


def setup_environment():
    """Set up the environment for the job so we can find FoXS, etc."""
    # Typically we don't run from a login shell so module paths aren't set.
    # Get these by running a login shell (which sources /etc/profile)
    # and asking it to print the needed environment variables.
    modout = subprocess.check_output(
        ['/bin/sh', '-l', '-c', 'echo $MODULESHOME; echo $MODULEPATH'],
        universal_newlines=True)
    moduleshome, modulepath, _ = modout.split('\n')
    os.environ['MODULEPATH'] = modulepath
    sys.path.insert(0, os.path.join(moduleshome, 'init'))

    # Add IMP and gnuplot to the path, using modules
    from python import module
    module('load', 'imp/last_ok_build', 'gnuplot')


def get_command_options(p):
    """Get command line options for FoXS and MultiFoXS"""
    foxs_opts = ['-j', '-g', '-m', str(p.model_option),
                 '-u', str(p.unit_option), '-q', str(p.q),
                 '-s', str(p.psize)]
    mf_opts = ['-u', str(p.unit_option), '-q', str(p.q)]

    if p.profile_file_name:
        foxs_opts.append('-p')
    if not p.hlayer:
        c = ['--min_c2', str(p.hlayer_value), '--max_c2', str(p.hlayer_value)]
        foxs_opts.extend(c)
        mf_opts.extend(c)
    if not p.exvolume:
        c = ['--min_c1', str(p.exvolume_value),
             '--max_c1', str(p.exvolume_value)]
        foxs_opts.extend(c)
        mf_opts.extend(c)
    if not p.ihydrogens:
        foxs_opts.append('-h')
    if p.residue:
        foxs_opts.append('-r')
    if p.offset:
        foxs_opts.append('-o')
        mf_opts.append('-o')
    if p.background:
        foxs_opts.extend(('-b', '0.2'))
    # Don't get confused if files names start with "-"
    foxs_opts.append('--')
    foxs_opts.extend(p.pdb_file_names)
    if p.profile_file_name:
        foxs_opts.append(p.profile_file_name)
    return foxs_opts, mf_opts


def setup_multimodel(params):
    """If we're using multi-model PDBs, make PDBs for each submodel"""
    if params.model_option != 2:
        return
    mmpdbs = []
    for pdb in params.pdb_file_names:
        mmpdbs.extend(make_multimodel_pdb_or_cif(pdb))
    with open('multi-model-files.txt', 'w') as fh:
        fh.write("\n".join(mmpdbs))


def make_multimodel_pdb_or_cif(fname):
    """If the given file is a multimodel PDB or mmCIF, make PDB/mmCIF files for
       each submodel and return them. Mimic FoXS itself; i.e. number the
       models sequentially (ignore the number on the MODEL line) and skip
       any model that contains no atoms."""
    if fname.endswith('.cif'):
        submodels = _make_multimodel_cif(fname)
    else:
        submodels = _make_multimodel_pdb(fname)
    # If only one model, FoXS just uses the original file
    if len(submodels) == 1:
        os.unlink(submodels[0])
        del submodels[0]
    return submodels or [fname]


class _AtomSiteSplitHandler:
    """Read the _atom_site table from an mmCIF file, and split it between
       multiple output files, one for each unique pdbx_pdb_model_num"""

    not_in_file = omitted = None
    unknown = ihm.unknown

    def __init__(self, stack, out_fname_stem):
        self._model_map = {}
        self._stack = stack
        self._out_fname_stem = out_fname_stem
        self.submodels = []

    # We read and write only the data items that IMP's mmCIF reader uses
    def __call__(self, label_atom_id, label_comp_id, label_asym_id,
                 auth_asym_id, type_symbol, label_seq_id, group_pdb, id,
                 occupancy, b_iso_or_equiv, pdbx_pdb_ins_code, cartn_x,
                 cartn_y, cartn_z, pdbx_pdb_model_num, auth_seq_id,
                 label_alt_id):
        if pdbx_pdb_model_num not in self._model_map:
            fname = "%s_m%d.cif" % (self._out_fname_stem,
                                    len(self._model_map) + 1)
            fh = self._stack.enter_context(
                open(fname, 'w', encoding='latin1'))
            writer = ihm.format.CifWriter(fh)
            lw = self._stack.enter_context(
                writer.loop("_atom_site",
                            ["group_PDB", "id", "type_symbol", "label_atom_id",
                             "label_alt_id", "label_comp_id", "label_seq_id",
                             "auth_seq_id", "pdbx_PDB_ins_code",
                             "label_asym_id", "Cartn_x", "Cartn_y", "Cartn_z",
                             "occupancy", "auth_asym_id",
                             "B_iso_or_equiv", "pdbx_PDB_model_num"]))
            self._model_map[pdbx_pdb_model_num] = lw
            self.submodels.append(fname)
        else:
            lw = self._model_map[pdbx_pdb_model_num]
        lw.write(group_PDB=group_pdb, id=id, type_symbol=type_symbol,
                 label_atom_id=label_atom_id, label_alt_id=label_alt_id,
                 label_comp_id=label_comp_id, label_seq_id=label_seq_id,
                 auth_seq_id=auth_seq_id, pdbx_PDB_ins_code=pdbx_pdb_ins_code,
                 label_asym_id=label_asym_id, Cartn_x=cartn_x, Cartn_y=cartn_y,
                 Cartn_z=cartn_z, occupancy=occupancy,
                 auth_asym_id=auth_asym_id, B_iso_or_equiv=b_iso_or_equiv,
                 pdbx_PDB_model_num=pdbx_pdb_model_num)


def _make_multimodel_cif(fname):
    out_fname_stem = os.path.splitext(fname)[0]
    with contextlib.ExitStack() as stack:
        ash = _AtomSiteSplitHandler(stack, out_fname_stem)
        with open(fname, encoding='latin1') as fh:
            c = ihm.format.CifReader(fh, category_handler={'_atom_site': ash})
            c.read_file()  # read first block
        return ash.submodels


def _make_multimodel_pdb(pdb):
    nmodel = 0
    natom = 0
    fname, ext = os.path.splitext(pdb)
    subpdbs = []
    outfh = None
    with open(pdb) as fh:
        for line in fh:
            if line.startswith('MODEL '):
                if outfh is not None:
                    outfh.close()
                    if natom == 0:
                        del subpdbs[-1]
                        nmodel -= 1
                natom = 0
                nmodel += 1
                modelfn = "%s_m%d.pdb" % (fname, nmodel)
                subpdbs.append(modelfn)
                outfh = open(modelfn, 'w')
            elif line.startswith('ENDMDL'):
                continue
            elif outfh is not None:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    natom += 1
                outfh.write(line)
    if outfh is not None:
        outfh.close()
        if natom == 0:
            os.unlink(subpdbs[-1])
            del subpdbs[-1]
    return subpdbs


def run_job(params):
    setup_multimodel(params)

    print("Start profile computation analysis")

    foxs_opts, multi_foxs_opts = get_command_options(params)
    # Run FoXS
    run_subprocess(['foxs'] + foxs_opts)
    # Make plots
    run_subprocess(['gnuplot'] + glob.glob('**/*.plt', recursive=True))

    png_files = glob.glob("**/*.png", recursive=True)
    if len(png_files) == 0:
        raise RuntimeError("No plot pngs produced")

    # Run MultiFoXS if necessary
    dat_files = (glob.glob("**/*.pdb.dat", recursive=True)
                 + glob.glob("**/*.cif.dat", recursive=True))
    if ((len(params.pdb_file_names) > 1 or len(dat_files) > 1)
            and params.profile_file_name):
        run_multifoxs(params, multi_foxs_opts)


def run_multifoxs(params, mf_opts):
    # validate exp. profile, add error if needed
    run_subprocess(['validate_profile', params.profile_file_name,
                    '-q', str(params.q)])
    validated_profile_name = (os.path.splitext(params.profile_file_name)[0]
                              + '_v.dat')

    file_counter = 0
    with open('filenames2.txt', 'w') as fh:
        for pdb in params.pdb_file_names:
            for dat_file in dat_files_for_pdb(pdb):
                fh.write(dat_file + '\n')
                file_counter += 1
    # determine maximal subset size
    max_subset_size = min(5, file_counter)

    print("Start Ensemble computation")
    run_subprocess(['multi_foxs', validated_profile_name, 'filenames2.txt',
                    '-s', str(max_subset_size)] + mf_opts)
    if not os.path.exists('ensembles_size_1.txt'):
        raise RuntimeError("No MultiFoXS ensembles produced")
    make_multifoxs_plots(params.profile_file_name)

    print("Calculate Rg")
    with open('rg', 'w') as fh:
        run_subprocess(['compute_rg', '-m', str(params.model_option)]
                       + params.pdb_file_names, stdout=fh)


def make_multifoxs_plots(profile_file_name):
    max_states = 4
    plot_states_histogram(max_states=max_states, max_models=10)
    make_gnuplot_canvas_plot(max_states, profile_file_name)


def make_gnuplot_canvas_plot(max_states, profile):
    """Prepare gnuplot canvas plot for profiles"""
    colors = ("#1a9850",  # green
              "#e26261",  # red
              "#3288bd",  # blue
              "#00FFFF",
              "#A6CEE3")
    with open('canvas_ensemble.plt', 'w') as fh:
        fh.write('set terminal canvas solid butt size 300,250 fsize 10 '
                 'lw 1.5 fontscale 1 name "jsoutput_3" jsdir "."\n')
        fh.write("set output 'jsoutput.3.js'; set multiplot; set origin 0,0;"
                 "set size 1,0.3; set tmargin 0;set xlabel 'q';"
                 "set ylabel ' ' offset 1;set format y '';set xtics nomirror;"
                 "set ytics nomirror;unset key;set border 3;"
                 "set style line 11 lc rgb '#808080' lt 1;"
                 "set border 3 back ls 11;f(x)=1\n")
        residuals = ["plot f(x) lc rgb '#333333'"]
        plots = ["plot '%s' u 1:2 lc rgb '#333333' pt 6 ps 0.8" % profile]
        for state_num in range(max_states):
            out_file = "multi_state_model_%d_1_1.fit" % (state_num + 1)
            residuals.append("'%s' u 1:(($2-$4)/$3) w lines lw 2.5 lc rgb '%s'"
                             % (out_file, colors[state_num]))
            plots.append("'%s' u 1:4 w lines lw 2.5 lc rgb '%s'"
                         % (out_file, colors[state_num]))
        fh.write(", ".join(residuals) + '\n')
        fh.write("set origin 0,0.3;set size 1,0.69; set bmargin 0;"
                 "set xlabel ''; set format x ''; "
                 "set ylabel 'intensity (log-scale)' offset 1; set log y\n")
        fh.write(", ".join(plots) + '\n')
        fh.write("unset multiplot\n")

    run_subprocess(['gnuplot', 'canvas_ensemble.plt'])


def plot_states_histogram(max_states, max_models):
    """Make a plot of chis against number of states"""
    scores = []
    for i in range(1, max_states + 1):
        ensemble_file = "ensembles_size_%d.txt" % i
        if os.path.exists(ensemble_file):
            scores.append(get_min_max_score(ensemble_file, max_models))

    # prepare chi-size plot
    with open('chis', 'w') as fh:
        for score in scores:
            fh.write('%d %f %f\n' % score)
    _, score, diff = scores[0]
    yrange = score + diff + 0.5
    if diff > score:
        yrange = score * 2.
    with open('plotbar3.plt', 'w') as fh:
        fh.write("""
set terminal png enhanced size 290,240

set output "chis.png"
set style line 11 lc rgb '#808080' lt 1
set border 3 back ls 11
set xtics nomirror;set ytics nomirror

set style line 1 lc rgb 'gray30' lt 1 lw 2
set style line 2 lc rgb '#596E98' lt 1 lw 2
#set style fill solid 1.0 border rgb 'grey30'
set style fill solid 1.0 border rgb '#596E98'
bs = 0.2

set yrange [0:%f];set ylabel 'x^2' offset 1;
set xrange [0.5:4.5]; set xlabel '# of states'
set xtics 1
plot 'chis' u 1:2:3 notitle w yerrorb ls 1, '' u 1:2:(bs) notitle w boxes ls 2
""" % yrange)
    run_subprocess(['gnuplot', 'plotbar3.plt'])


def get_min_max_score(ensemble_file, max_models):
    """Parse an ensembles_size_XX.txt file and return the number of states,
       score of the best model, and difference between the best scoring
       and worst scoring (capped at max_models)"""
    model_num = number_of_states = 0
    first_score = last_score = 0.
    with open(ensemble_file) as fh:
        for line in fh:
            if " x1 " in line:
                spl = line.rstrip('\r\n').split('|')
                if len(spl) > 0 and spl[0].strip().isdigit():
                    model_num = int(spl[0])
                    if model_num > max_models:
                        break
                    last_score = float(spl[1])
                    if first_score == 0.:
                        first_score = last_score
            elif model_num == 1:
                number_of_states += 1
    return number_of_states, first_score, last_score - first_score


def dat_files_for_pdb(pdb):
    """Get all dat files for a given PDB"""
    dat_file = pdb + '.dat'
    if os.path.exists(dat_file):
        yield dat_file
    else:  # multi model file
        pdb_code = os.path.splitext(pdb)[0]
        for i in range(1, 101):
            for ext in ('pdb', 'cif'):
                dat_file = "%s_m%d.%s.dat" % (pdb_code, i, ext)
                if os.path.exists(dat_file):
                    yield dat_file


def run_subprocess(cmd, stdout=None):
    """Run and log a subprocess"""
    if stdout is None:
        stdout = sys.stdout
    # Ensure that output from subprocess shows up in the right place in the log
    sys.stdout.flush()
    subprocess.check_call(cmd, stdout=stdout, stderr=sys.stderr)


def main():
    set_job_state('STARTED')
    try:
        # Send our own error/output to a log file
        sys.stdout = sys.stderr = open('foxs.log', 'w')
        setup_environment()
        params = JobParameters()
        run_job(params)
    except Exception:
        # Don't exit non-zero on exception, as this will automatically fail
        # the job (and some exceptions are caused by user inputs, which they
        # should correct). But print the exception information so that
        # postprocess can determine whether or not to return the error to
        # the user.
        traceback.print_exc()
    finally:
        set_job_state('DONE')


if __name__ == '__main__':
    main()
