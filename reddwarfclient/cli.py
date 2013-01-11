#!/usr/bin/env python

#    Copyright 2011 OpenStack LLC
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Reddwarf Command line tool
"""

import os
import sys

# FIXME (rmyers): What is this really for?
# If ../reddwarf/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'reddwarfclient',
                               '__init__.py')):
    sys.path.insert(0, possible_topdir)


from reddwarfclient import common

COMMANDS = common.cli_commands.commands

def main():
    # Parse arguments
    load_file = True
    for index, arg in enumerate(sys.argv):
        if (arg == "auth" and len(sys.argv) > (index + 1)
            and sys.argv[index + 1] == "login"):
            load_file = False

    oparser = common.CliOptions.create_optparser(load_file)
    for k, v in COMMANDS.items():
        v._prepare_parser(oparser)
    (options, args) = oparser.parse_args()

    if not args:
        common.print_commands(COMMANDS)

    if options.verbose:
        os.environ['RDC_PP'] = "True"
        os.environ['REDDWARFCLIENT_DEBUG'] = "True"

    # Pop the command and check if it's in the known commands
    cmd = args.pop(0)
    if cmd in COMMANDS:
        fn = COMMANDS.get(cmd)
        command_object = None
        try:
            command_object = fn(oparser)
        except Exception as ex:
            if options.debug:
                raise
            print(ex)

        # Get a list of supported actions for the command
        actions = common.methods_of(command_object)

        if len(args) < 1:
            common.print_actions(cmd, actions)

        # Check for a valid action and perform that action
        action = args.pop(0)
        if action in actions:
            if not options.debug:
                try:
                    getattr(command_object, action)()
                except Exception as ex:
                    if options.debug:
                        raise
                    print ex
            else:
                getattr(command_object, action)()
        else:
            common.print_actions(cmd, actions)
    else:
        common.print_commands(COMMANDS)


if __name__ == '__main__':
    main()
