import argparse
import logging
import os
import tempfile
import shutil

from puppet_compiler import nodegen, prepare, directories, puppet, utils


parser = argparse.ArgumentParser(
    description="Puppetdb filler - this script allows to properly populate PuppetDB with data useful for the puppet compiler"
)
parser.add_argument(
    '--basedir',
    default='/var/lib/catalog-differ',
    help='The base dir of the compiler installation',
)
parser.add_argument('--debug', action='store_true', default=False, help="Print debug output")


def main():
    opts = parser.parse_args()
    if opts.debug:
        lvl = logging.DEBUG
    else:
        lvl = logging.INFO

    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        level=lvl,
        datefmt='[ %Y-%m-%dT%H:%M:%S ]'
    )

    config = {
        'puppet_var': os.path.join(opts.basedir, 'puppet'),
        'puppet_src': os.path.join(opts.basedir, 'production'),
        'puppet_private': os.path.join(opts.basedir, 'private')
    }
    # Do the whole compilation in a dedicated directory.
    tmpdir = tempfile.mkdtemp(prefix='fill-puppetdb')
    jobid = '1'
    directories.FHS.setup(jobid, tmpdir)
    m = prepare.ManageCode(config, jobid, None)
    os.mkdir(m.base_dir, 0755)
    os.makedirs(m.prod_dir, 0755)
    m._prepare_dir(m.prod_dir)
    srcdir = os.path.join(m.prod_dir, 'src')
    with prepare.pushd(srcdir):
        m._copy_hiera(m.prod_dir, 'production')

    for node in nodegen.get_nodes(config):
        print "=" * 80
        print "Compiling catalog for {}".format(node)

        utils.refresh_yaml_date(utils.facts_file(config['puppet_var'], node))
        succ, out, err = puppet.compile_storeconfigs(node, config['puppet_var'])
        if succ:
            print "OK"
        else:
            for line in err:
                print line
    shutil.rmtree(tmpdir)


if __name__ == '__main__':
    main()
