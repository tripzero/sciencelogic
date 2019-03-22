# -*- coding: utf-8 -*-
from requests.auth import HTTPBasicAuth
from sciencelogic.device import Device
import requests

requests.packages.urllib3.disable_warnings()


class Client(object):
    def __init__(self, username, password, uri,
                 auto_connect=True, verify_ssl=False):
        """
        Instantiate a EM7 Client API

        :param username: Your username
        :type  username: ``str``

        :param password: Your password
        :type  password: ``str``

        :param uri: The EM7 URI (excluding the /api)
        :param uri: ``str``

        :param auto_connect: Try an connect and get API data when initializing
        :param auto_connect: ``bool``
        """
        self.username = username
        self.password = password
        self.uri = uri
        self.verify = verify_ssl
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

        if auto_connect:
            self.sysinfo = self._connect()

    def _connect(self):
        info = self.get('api/sysinfo')
        return info.json()

    def get(self, uri, params=None):
        """
        Get a URI from the API

        :param uri: The URI
        :type  uri: ``str``

        :params params: Extra params
        :type   params: ``dict``
        """
        if params is None:
            params = {}
        if uri.startswith('/'):
            uri = uri[1:]
        return self.session.get('%s/%s' % (self.uri, uri),
                                params=params,
                                verify=self.verify)

    def devices(self, details=False, limit=100):
        """
        Get a list of devices

        :param details: Get the details of the devices
        :type  details: ``bool``

        :param limit: Number of devices to retrieve
        :type details: ``int``

        :rtype: ``list`` of :class:`Device`
        """
        response = self.get('api/device', {'extended_fetch': 1, 'limit': limit}
                            if details else {'limit': limit})
        devices = []
        if details:
            for uri, device in response.json()['result_set'].items():
                devices.append(Device(device, uri, self, True))
        else:
            for device in response.json()['result_set']:
                devices.append(Device(device, device['URI'], self, False))
        return devices

    def get_devices_by_device_group(self, group_id):
        """
        Get list of devices by group_id

        :param group_id: description of the device group
        :type group_id: str

        :rtype: ``list`` of :int: device ids that match the
        :param:`group_id` description
        """

        response = self.get('api/device_group').json()

        groups = response.get("result_set", [])

        found_group = None

        for group in groups:
            if group["description"] == group_id:
                found_group = group
                break

        if found_group is None:
            print("count not find device group: {}".format(group_id))
            return []

        device_group = self.get(found_group["URI"]).json()

        devices = []

        for device in device_group["devices"]:
            # print("device found: {}".format(device))
            did = int(device.split("/")[-1])

            devices.append(did)

        return devices

    def get_device(self, device_id):
        """
        Get a devices

        :param device_id: The id of the device
        :type  device_id: ``int``

        :rtype: ``list`` of :class:`Device`
        """
        if not isinstance(device_id, int):
            raise TypeError('Device ID must be integer')
        uri = 'api/device/%s' % device_id
        device = self.session.get('%s/%s' % (self.uri, uri)).json()
        return Device(device, uri, self, True)
