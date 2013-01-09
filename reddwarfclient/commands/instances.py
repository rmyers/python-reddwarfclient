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

import urlparse

from reddwarfclient import base
from reddwarfclient import common
from reddwarfclient.common import check_for_exceptions
from reddwarfclient.common import limit_url
from reddwarfclient.common import Paginated
from reddwarfclient import exceptions


REBOOT_SOFT, REBOOT_HARD = 'SOFT', 'HARD'


class Instance(base.Resource):
    """
    An Instance is an opaque instance used to store Database instances.
    """
    def __repr__(self):
        return "<Instance: %s>" % self.name

    def list_databases(self):
        return self.manager.databases.list(self)

    def delete(self):
        """
        Delete the instance.
        """
        self.manager.delete(self)

    def restart(self):
        """
        Restart the database instance
        """
        self.manager.restart(self.id)


class Instances(base.ManagerWithFind):
    """
    Manage :class:`Instance` resources.
    """
    resource_class = Instance
    name = 'instances'

    def create(self, name, flavor_id, volume, databases=None, users=None):
        """
        Create (boot) a new instance.
        """
        body = {"instance": {
            "name": name,
            "flavorRef": flavor_id,
            "volume": volume
        }}
        if databases:
            body["instance"]["databases"] = databases
        if users:
            body["instance"]["users"] = users

        return self._create("/instances", body, "instance")

    def _list(self, url, response_key, limit=None, marker=None):
        resp, body = self.api.client.get(limit_url(url, limit, marker))
        if not body:
            raise Exception("Call to " + url + " did not return a body.")
        links = body.get('links', [])
        next_links = [link['href'] for link in links if link['rel'] == 'next']
        next_marker = None
        for link in next_links:
            # Extract the marker from the url.
            parsed_url = urlparse.urlparse(link)
            query_dict = dict(urlparse.parse_qsl(parsed_url.query))
            next_marker = query_dict.get('marker', None)
        instances = body[response_key]
        instances = [self.resource_class(self, res) for res in instances]
        return Paginated(instances, next_marker=next_marker, links=links)

    def list(self, limit=None, marker=None):
        """
        Get a list of all instances.

        :rtype: list of :class:`Instance`.
        """
        return self._list("/instances", "instances", limit, marker)

    def get(self, instance):
        """
        Get a specific instances.

        :rtype: :class:`Instance`
        """
        return self._get("/instances/%s" % base.getid(instance),
                        "instance")

    def delete(self, instance):
        """
        Delete the specified instance.

        :param instance_id: The instance id to delete
        """
        resp, body = self.api.client.delete("/instances/%s" %
                                            base.getid(instance))
        if resp.status in (422, 500):
            raise exceptions.from_response(resp, body)

    def _action(self, instance_id, body):
        """
        Perform a server "action" -- reboot/rebuild/resize/etc.
        """
        url = "/instances/%s/action" % instance_id
        resp, body = self.api.client.post(url, body=body)
        check_for_exceptions(resp, body)
        if body:
            return self.resource_class(self, body, loaded=True)
        return body

    def resize_volume(self, instance_id, volume_size):
        """
        Resize the volume on an existing instances
        """
        body = {"resize": {"volume": {"size": volume_size}}}
        self._action(instance_id, body)

    def resize_instance(self, instance_id, flavor_id):
        """
        Resize the volume on an existing instances
        """
        body = {"resize": {"flavorRef": flavor_id}}
        self._action(instance_id, body)

    def restart(self, instance_id):
        """
        Restart the database instance.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        body = {'restart': {}}
        self._action(instance_id, body)

    def reset_password(self, instance_id):
        """
        Resets the database instance root password.

        :param instance_id: The :class:`Instance` (or its ID) to share onto.
        """
        body = {'reset-password': {}}
        return self._action(instance_id, body)

Instances.resize_flavor = Instances.resize_instance


class InstanceStatus(object):

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    BUILD = "BUILD"
    FAILED = "FAILED"
    REBOOT = "REBOOT"
    RESIZE = "RESIZE"
    SHUTDOWN = "SHUTDOWN"


class InstanceCommands(common.AuthedCommandsBase):
    """Commands to perform various instances operations and actions"""

    params = [
              'flavor',
              'id',
              'limit',
              'marker',
              'name',
              'size',
             ]

    def create(self):
        """Create a new instance"""
        self._require('name', 'size')
        # flavorRef is not required.
        flavorRef = self.flavor or "http://localhost:8775/v1.0/flavors/1"
        volume = {"size": self.size}
        self._pretty_print(self.dbaas.instances.create, self.name,
                          flavorRef, volume)

    def delete(self):
        """Delete the specified instance"""
        self._require('id')
        print self.dbaas.instances.delete(self.id)

    def get(self):
        """Get details for the specified instance"""
        self._require('id')
        self._pretty_print(self.dbaas.instances.get, self.id)

    def list(self):
        """List all instances for account"""
        # limit and marker are not required.
        limit = self.limit or None
        if limit:
            limit = int(limit, 10)
        self._pretty_paged(self.dbaas.instances.list)

    def resize_volume(self):
        """Resize an instance volume"""
        self._require('id', 'size')
        self._pretty_print(self.dbaas.instances.resize_volume, self.id,
                          self.size)

    def resize_instance(self):
        """Resize an instance flavor"""
        self._require('id', 'flavor')
        self._pretty_print(self.dbaas.instances.resize_instance, self.id,
                          self.flavor)

    def restart(self):
        """Restart the database"""
        self._require('id')
        self._pretty_print(self.dbaas.instances.restart, self.id)

    def reset_password(self):
        """Reset the root user Password"""
        self._require('id')
        self._pretty_print(self.dbaas.instances.reset_password, self.id)


class MgmtInstanceCommands(common.AuthedCommandsBase):
    """List details about an instance."""

    params = [
              'deleted',
              'id',
              'limit',
              'marker',
             ]

    def get(self):
        """List details for the instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.show, self.id)

    def list(self):
        """List all instances for account"""
        deleted = None
        if self.deleted is not None:
            if self.deleted.lower() in ['true']:
                deleted = True
            elif self.deleted.lower() in ['false']:
                deleted = False
        self._pretty_paged(self.dbaas.management.index, deleted=deleted)

    def hwinfo(self):
        """Show hardware information details about an instance."""
        self._require('id')
        self._pretty_print(self.dbaas.hwinfo.get, self.id)

    def diagnostic(self):
        """List diagnostic details about an instance."""
        self._require('id')
        self._pretty_print(self.dbaas.diagnostics.get, self.id)

    def stop(self):
        """Stop MySQL on the given instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.stop, self.id)

    def reboot(self):
        """Reboot the instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.reboot, self.id)

    def migrate(self):
        """Migrate the instance."""
        self._require('id')
        self._pretty_print(self.dbaas.management.migrate, self.id)


common.cli_commands.register('instance', InstanceCommands)
common.mcli_commands.register('instance', MgmtInstanceCommands)
