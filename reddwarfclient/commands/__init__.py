# Copyright (c) 2011 OpenStack, LLC.
# All Rights Reserved.
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

import logging
from pkg_resources import iter_entry_points

from reddwarfclient.commands.versions import Versions
from reddwarfclient.commands.databases import Databases
from reddwarfclient.commands.flavors import Flavors
from reddwarfclient.commands.instances import Instances
from reddwarfclient.commands.users import Users
from reddwarfclient.commands.root import Root
from reddwarfclient.commands.hosts import Hosts
from reddwarfclient.commands.storage import StorageInfo
from reddwarfclient.commands.management import Management
from reddwarfclient.commands.accounts import Accounts
from reddwarfclient.commands.diagnostics import DiagnosticsInterrogator
from reddwarfclient.commands.diagnostics import HwInfoInterrogator


class ResourceRegisty(object):
    
    entry_point = 'reddwarfclient.resources'
    
    def __init__(self):
        self._resources = {}

    def all_resources(self):
        """Print out all resources."""
        for key, value in self._resources.iteritems():
            print 'Resource %s registered at %s' % (value, key)

    def load(self, client):
        for key, klass in self._resources.iteritems():
            setattr(client, key, klass(client))

    def register(self, resource):
        if resource.name in self._resources:
            return
        self._resources[resource.name] = resource


# Global resources registry
resources = ResourceRegisty()

# Register all the default resources
resources.register(Versions)
resources.register(Databases)
resources.register(Flavors)
resources.register(Instances)
resources.register(Users)
resources.register(Root)
resources.register(Hosts)
resources.register(StorageInfo)
resources.register(Management)
resources.register(Accounts)
resources.register(DiagnosticsInterrogator)
resources.register(HwInfoInterrogator)

# Register resources from entry points
loaded = {}
for ep in iter_entry_points('reddwarfclient.resources'):
    if ep.name in loaded:
        continue
    loaded[ep.name] = True
    klass = ep.load()
    try:
        resources.register(klass)
    except Exception:
        logging.exception("Unable to load extention %s" % klass)