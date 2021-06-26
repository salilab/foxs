from flask import request
import saliweb.frontend
from saliweb.frontend import InputValidationError
import os
import zipfile
from werkzeug.utils import secure_filename


def handle_new_job():
    email = request.form.get("email")
    saliweb.frontend.check_email(email, required=False)

    q = request.form.get('q', 0.5, type=float)
    if q <= 0.0 or q >= 1.0:
        raise InputValidationError(
            "Invalid q value; it must be > 0 and < 1.0")

    psize = request.form.get('psize', 500, type=int)
    if psize <= 20 or psize >= 2000:
        raise InputValidationError(
            "Invalid profile size; it must be > 20 and < 2000")

    # hydration layer
    hlayer, hlayer_value = get_float_parameter(
        checkbox="hlayer", parameter="c2", default=0.0, rng=(-1.0, 4.0),
        name="hydration layer density")

    # excluded volume
    exvolume, exvolume_value = get_float_parameter(
        checkbox="exvolume", parameter="c1", default=1.0, rng=(0.95, 1.05),
        name="excluded volume adjustment parameter")

    # hydrogens, residue level, offset, background adjustment
    ihydrogens = 1 if request.form.get('ihydrogens') else 0
    residue = 1 if request.form.get('residue') else 0
    offset = 1 if request.form.get('offset') else 0
    background = 1 if request.form.get('background') else 0

    # MODEL reading option
    opts = {"First MODEL only": 1, "MODELs into multiple structures": 2}
    model_option = opts.get(request.form.get('modelread'), 3)

    # Units option
    opts = {"angstroms": 2, "nanometers": 3}
    unit_option = opts.get(request.form.get('units'), 1)

    job = saliweb.frontend.IncomingJob()

    prot_file_names, archive = handle_pdb(
        request.form.get("pdb"), request.files.get("pdbfile"), job)
    profile_file_name = save_job_nonempty_file(request.files.get("profile"),
                                               job, "profile") or "-"

    with open(job.get_path('inputFiles.txt'), 'w') as fh:
        fh.write("\n".join(prot_file_names))

    with open(job.get_path('data.txt'), 'w') as fh:
        fh.write("%s %s %s %.2f %d %d %d %d %d %d %d %.2f %.2f %d %d\n"
                 % (archive, profile_file_name, email, q, psize,
                    hlayer, exvolume, ihydrogens, residue, offset,
                    background, hlayer_value, exvolume_value, model_option,
                    unit_option))

    job.submit(email)
    return saliweb.frontend.redirect_to_results_page(job)


def handle_pdb(pdb_code, pdb_file, job):
    """Handle input PDB code or file. Return a list of file names plus
       a single archive that contains all files."""
    if pdb_file:
        saved_fname = save_job_nonempty_file(pdb_file, job, "PDB or zip")
        try:
            return handle_zipfile(saved_fname, job), saved_fname
        except zipfile.BadZipfile:
            return [saved_fname], saved_fname
    elif pdb_code:
        fname = saliweb.frontend.get_pdb_chains(pdb_code, job.directory)
        return [os.path.basename(fname)], os.path.basename(fname)
    else:
        raise InputValidationError("Error in protein input: please specify "
                                   "PDB code or upload file")


def handle_zipfile(zfname, job):
    """Extract PDB files from the given zip file"""
    exclude = frozenset((zfname, 'inputFiles.txt'))
    pdbs = []
    fh = zipfile.ZipFile(job.get_path(zfname))
    for zi in fh.infolist():
        fname = secure_filename(os.path.basename(zi.filename))
        if fname not in exclude:
            with open(job.get_path(fname), 'wb') as out_fh:
                out_fh.write(fh.read(zi))
            pdbs.append(fname)
            if len(pdbs) > 100:
                raise InputValidationError(
                    "Only 100 PDB files can run on the server. Please use "
                    "download version for more")
    fh.close()
    return pdbs


def save_job_nonempty_file(fh, job, filetype):
    """Save the given file, if present (which must not be empty) into the
       job directory. Return its name (or None)."""
    if not fh:
        return

    fname = secure_filename(fh.filename)
    full_fname = job.get_path(fname)
    fh.save(full_fname)
    if os.stat(full_fname).st_size == 0:
        raise InputValidationError(
            "You have uploaded an empty %s file: %s" % (filetype, fname))
    return fname


def get_float_parameter(checkbox, parameter, default, rng, name):
    if request.form.get(checkbox):
        return (1, default)
    else:
        value = request.form.get(parameter, default, type=float)
        if value < rng[0] or value > rng[1]:
            raise InputValidationError(
                "Invalid %s value; it must be > %.2f and < %.2f"
                % (name, rng[0], rng[1]))
        return (0, value)
