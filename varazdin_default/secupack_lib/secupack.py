# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------------
#
#    Copyright (C) 2017  jeo Software  (http://www.jeosoft.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# -----------------------------------------------------------------------------------
import pprint

pp = pprint.PrettyPrinter(indent=4)

import requests
from bunch import bunchify

API_VERSION = 'v1.0'
API_ENDPOINT = 'https://rest.secupack.com.ar/api'


class SecupackClient(object):
    def __init__(self, user=False, password=False, debug=False):
        self._debug = debug
        self._token = False
        r = requests.post(self._base_url('login'), data={'username': user, 'password': password})
        if r.status_code == 200 and r.json()['success']:
            self._token = r.json()['token']
            if self._debug: print '-- Logged onto secupack ' + user

    def logged(self):
        return True if self._token else False

    @staticmethod
    def _base_url(resource, id=False):
        if id:
            return API_ENDPOINT + '/' + API_VERSION + '/' + resource + '/' + id
        else:
            return API_ENDPOINT + '/' + API_VERSION + '/' + resource

    def get_couriers(self):
        """ Devuelve todos los couriers """
        if self._debug: print '-- getting couriers'
        r = requests.get(self._base_url('couriers'),
                         headers={'x-access-token': self._token})
        if r.status_code == 200:
            return r.json()['couriers']

    def get_user(self):
        """ Trae los datos del usuario """
        if self._debug: print '-- getting user'
        r = requests.get(self._base_url('user'),
                         headers={'x-access-token': self._token})
        if r.status_code == 200:
            return r.json()['user']

    def set_courier(self, data, id=False):
        """ Alta o Modifica courier """
        if self._debug: print '-- setting courier with', data, id, self._token
        verb = 'courier' if id else 'couriers'
        r = requests.post(self._base_url(verb, id), data=data,
                          headers={'x-access-token': self._token})
        if r.status_code != 200:
            if self._debug:
                print '--------------------------------- ERROR'
                print 'status_code', r.status_code
                print r.json()
            raise Exception()
        return False  # deberia devolver el _id

    def del_courier(self, data, id=False):
        """ Baja de courier """
        if not id:
            raise Exception('Debe tener un id')
        if self._debug: print '-- deleting courier'
        r = requests.delete(self._base_url('couriers', id),
                            headers={'x-access-token': self._token})

    def get_packtypes(self):
        """ Trae los paquetes y requisitos """
        if self._debug: print '-- getting packtypes'
        r = requests.get(self._base_url('packtypes'),
                         headers={'x-access-token': self._token})
        if r.status_code == 200:
            if self._debug: print pp.pprint(r.json()['packtypes'])
            return r.json()['packtypes']

    def set_packtypes(self, data):
        """ Alta de un paquete """
        if self._debug: print '-- setting packtypes'
        r = requests.post(self._base_url('packtypes'), data,
                          headers={'x-access-token': self._token})
        print r.json()
        return r.status_code == 200

    def get_courier_packages(self, filter):
        """ Trae las definiciones de los viajes """
        if self._debug: print '-- getting courier_packages'
        r = requests.get(self._base_url('courierPackages'), params=filter,
                         headers={'x-access-token': self._token})
        if r.status_code == 200 and r.json()['success']:
            return r.json()['packs']
        else:
            raise Exception(r.json())

    def set_courier_package(self, data):
        """ Alta de la definiciones de un viaje """
        if self._debug: print '-- setting courier_packages'
        r = requests.post(self._base_url('courierPackage'), data=data,
                          headers={'x-access-token': self._token})
        return r.json()['message']
