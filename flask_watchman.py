"""
Flask Watchman
"""
import os
import json
import datetime
import subprocess

from flask import current_app, Response


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
            encoded_object =json.JSONEncoder.default(self, obj)
        return encoded_object


class Watchman(object):
    """
    Watchman class
    """
    def __init__(self, app=None):
        """
        Constructor
        :param app: flask app
        """
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

        with app.app_context():
            current_app.add_url_rule(
                '/version',
                'version',
                lambda: self.app_version()
            )
            current_app.add_url_rule(
                '/environment',
                'environment',
                self.app_config
            )

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

        for key, cmd in git_params.iteritems():
            process = subprocess.Popen(
                [cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, err = process.communicate()

            version[key] = out

        return Response(json.dumps(version), mimetype='application/json')

    def app_config(self):
        """
        Get the current OS and application configuration
        """

        environment = dict(os={}, app={})

        for key in os.environ.keys():
            environment['os'].setdefault(key, os.environ.get(key))

        with self.app.app_context():

            if hasattr(current_app, 'config'):
                for key in current_app.config.keys():
                    environment['app'].setdefault(key, current_app.config[key])

        r = Response(
            json.dumps(environment, cls=DateTimeEncoder),
            mimetype='application/json'
        )
        return r
