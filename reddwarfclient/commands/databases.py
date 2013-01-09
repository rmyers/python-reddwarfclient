from reddwarfclient import base
from reddwarfclient import common
from reddwarfclient.common import check_for_exceptions
from reddwarfclient.common import limit_url
from reddwarfclient.common import Paginated
import exceptions
import urlparse


class Database(base.Resource):
    """
    According to Wikipedia, "A database is a system intended to organize,
    store, and retrieve
    large amounts of data easily."
    """
    def __repr__(self):
        return "<Database: %s>" % self.name


class Databases(base.ManagerWithFind):
    """
    Manage :class:`Databases` resources.
    """
    resource_class = Database
    name = 'databases'

    def create(self, instance_id, databases):
        """
        Create new databases within the specified instance
        """
        body = {"databases": databases}
        url = "/instances/%s/databases" % instance_id
        resp, body = self.api.client.post(url, body=body)
        check_for_exceptions(resp, body)

    def delete(self, instance_id, dbname):
        """Delete an existing database in the specified instance"""
        url = "/instances/%s/databases/%s" % (instance_id, dbname)
        resp, body = self.api.client.delete(url)
        check_for_exceptions(resp, body)

    def _list(self, url, response_key, limit=None, marker=None):
        resp, body = self.api.client.get(limit_url(url, limit, marker))
        check_for_exceptions(resp, body)
        if not body:
            raise Exception("Call to " + url +
                            " did not return a body.")
        links = body.get('links', [])
        next_links = [link['href'] for link in links if link['rel'] == 'next']
        next_marker = None
        for link in next_links:
            # Extract the marker from the url.
            parsed_url = urlparse.urlparse(link)
            query_dict = dict(urlparse.parse_qsl(parsed_url.query))
            next_marker = query_dict.get('marker', None)
        databases = body[response_key]
        databases = [self.resource_class(self, res) for res in databases]
        return Paginated(databases, next_marker=next_marker, links=links)

    def list(self, instance, limit=None, marker=None):
        """
        Get a list of all Databases from the instance.

        :rtype: list of :class:`Database`.
        """
        return self._list("/instances/%s/databases" % base.getid(instance),
                          "databases", limit, marker)


class DatabaseCommands(common.AuthedCommandsBase):
    """Database CRUD operations on an instance"""

    params = [
              'name',
              'id',
              'limit',
              'marker',
             ]

    def create(self):
        """Create a database"""
        self._require('id', 'name')
        databases = [{'name': self.name}]
        print self.dbaas.databases.create(self.id, databases)

    def delete(self):
        """Delete a database"""
        self._require('id', 'name')
        print self.dbaas.databases.delete(self.id, self.name)

    def list(self):
        """List the databases"""
        self._require('id')
        self._pretty_paged(self.dbaas.databases.list, self.id)


common.cli_commands.register('database', DatabaseCommands)