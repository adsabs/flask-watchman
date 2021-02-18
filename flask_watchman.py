"""
Flask Watchman
"""
import os
import json
import datetime
import subprocess

from flask import current_app, Response
from flask_restful import Resource
from flask_discoverer import advertise


class DateTimeEncoder(json.JSONEncoder):
    """
    JSON encoder for the datetime objects, specifically datetime and timedelta
    """
    def default(self, obj):
        """
        Override the default JSON encoder behaviour to allow other types of
        datetime classes to be encoded properly

        :param obj: object to encode
        :return: encoded object
        """
        if isinstance(obj, datetime.datetime):
            encoded_object = list(obj.timetuple())[0:6]
        elif isinstance(obj, datetime.timedelta):
            encoded_object = obj.microseconds
        else:
            encoded_object = json.JSONEncoder.default(self, obj)
        return encoded_object


class Version(Resource):

    def get(self):
        return Version.app_version()

    @staticmethod
    def app_version():
        """
        Get the current version of the application running using the response
        obtained from git. If the project is not version controlled by git, this
        will not work correctly.
        """
        version = dict(commit=None, release=None)
        git_params = {
            'commit': 'git log --pretty=format:\'%H\' -n 1',
            'release': 'git describe'
        }

        for key, cmd in git_params.items():
            process = subprocess.Popen(
                cmd.split(' '),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = process.communicate()

            version[key] = out

        return Response(json.dumps(version), mimetype='application/json')


class Environment(Resource):

    def get(self):
        return self.app_config()

    def app_config(self):
        """
        Get the current OS and application configuration
        """

        environment = dict(os={}, app={})

        for key in os.environ.keys():
            environment['os'].setdefault(key, os.environ.get(key))

        with current_app.app_context():

            if hasattr(current_app, 'config'):
                for key in current_app.config.keys():
                    environment['app'].setdefault(key, current_app.config[key])

        r = Response(
            json.dumps(environment, cls=DateTimeEncoder),
            mimetype='application/json'
        )
        return r


class Watchman(object):
    """
    Watchman class
    """
    def __init__(self, app=None, **kwargs):
        """
        Constructor
        :param app: flask app
        """

        # Ensure that version is always added with no scopes, unless the user
        # specifies
        self.kwargs = kwargs
        self.kwargs.setdefault('version', {})

        self.allowed_endpoints = {
            'version': {
                'view': Version,
                'route': '/version',
                'methods': ['GET'],
            },
            'environment': {
                'view': Environment,
                'route': '/environment',
                'methods': ['GET']
            }
        }

        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Standard flask-extension initialisation

        :param app: flask app
        """

        if app is not None:
            self.app = app

        if 'watchman' in app.extensions:
            raise RuntimeError('Flask application already initialised')

        app.extensions['watchman'] = self

        for view_name in self.allowed_endpoints.keys():

            if view_name not in self.kwargs.keys():
                continue

            view = self.allowed_endpoints[view_name]['view']
            route = self.allowed_endpoints[view_name]['route']
            methods = self.allowed_endpoints[view_name]['methods']

            # Does the user provide scopes?
            if view_name in self.kwargs and self.kwargs[view_name].get('scopes', None) != None:
                user_config = self.kwargs[view_name]

                view.scopes = user_config.get('scopes', [])
                view.decorators = user_config.get('decorators', ([advertise('scopes', 'rate_limit')]))
                view.rate_limit = [1000, 60*60*24]

            with app.app_context():
                current_app.add_url_rule(
                    route,
                    view_func=view.as_view(view_name),
                    methods=methods
                )
