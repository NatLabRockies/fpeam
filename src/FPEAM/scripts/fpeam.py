"""Executes FPEAM against given datasets and configuration files."""
import argparse
import logging
import os
from datetime import datetime

from FPEAM import (IO, FPEAM, utils)


def main():
    parser = argparse.ArgumentParser(
        description='Execute FPEAM model against a given equipment'
                    ' group set, production'
                    ' dataset, and configuration files')

    parser.add_argument('run_config', type=str, help='execution configuration')

    config_group = parser.add_argument_group('configuration files')
    config_group.add_argument('--fpeam_config', type=str,
                              default=None,
                              help='FPEAM model configuration options')
    config_group.add_argument('--moves_config', type=str,
                              default=None,
                              help='MOVES model configuration options')
    config_group.add_argument('--nonroad_config', type=str,
                              default=None,
                              help='NONROAD configuration options')
    config_group.add_argument('--emissionfactors_config', type=str,
                              default=None,
                              help='emission factors module configuration options')
    config_group.add_argument('--fugitivedust_config', type=str,
                              default=None,
                              help='fugitive dust module configuration options')

    run_group = parser.add_argument_group('run options')
    run_group.add_argument('-v', dest='verbose', action='store_true',
                           help='print more messages')
    run_group.add_argument('--l', '--log', dest='log', type=str,
                           default=os.path.abspath(os.path.join(os.path.curdir,
                                                                'fpeam_%s.log' %
                                                                (datetime.now().strftime('%Y%m%d_%H%M')))),
                           help='log file path (default: %(default)s')

    args = parser.parse_args()

    # create shared logger
    logging.basicConfig(level='DEBUG', format='%(asctime)s, %(levelname)-8s'
                                              ' [%(filename)s:%(module)s.'
                                              '%(funcName)s.%(lineno)d] %(message)s',
                        filename=args.log,
                        filemode='w')

    _console = logging.StreamHandler()

    if args.verbose:
        _console.setLevel(logging.DEBUG)
    else:
        _console.setLevel(logging.INFO)
    _console.setFormatter(logging.Formatter('%(name)-12s %(lineno)s: %(levelname)-8s: %(message)s'))
    logging.getLogger('').addHandler(_console)

    # load config options
    _config = IO.load_configs(args.fpeam_config,
                              args.moves_config,
                              args.nonroad_config,
                              args.emissionfactors_config,
                              args.fugitivedust_config,
                              args.run_config)

    with FPEAM(run_config=_config) as _fpeam:
        _fpeam.run()

        # save the raw results to the project path folder specified in run_config
        _fpath = os.path.join(_fpeam.config['project_path'],
                              '%s_raw.csv' % _fpeam.config['scenario_name'])
        _fpeam.results.to_csv(_fpath, index=False)

        # save several summarized results files to the project folder
        _fpeam.summarize()


if __name__ == '__main__':
    main()
