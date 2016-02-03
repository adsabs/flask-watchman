[![Build Status](https://travis-ci.org/jonnybazookatone/flask-watchman.svg?branch=master)](https://travis-ci.org/jonnybazookatone/flask-watchman)

# Flask Watchman

A flask extension that overlays simple end points for utilities that would normally require accessing the machine (or container) running microservice.

Currently, the following end points are allowed:

  1. `/version`: returns the git commit and release
  2. `/environment`: returns the OS and the running flask application configuration

## requirements

Currently, it is expected the application is running on a system that has `git` installed.

## scopes
It is possible to add scopes to the end point, that are managed by a centralised API layer. Each endpoint can be configured by passing a dictionary as a keyword. For example, the following is allowed:

```python
from flask import Flask
from flask.ext.watchman import Watchman

app = Flask()

environment = {
   'scopes': ['some-scope'],
   'rate_limit': [1000],
   'decorators': []
}

Watchman(app, environment=environment)
```

This will create an `/environment` end point that has the 'some-scope' scope, with rate limit 1000, and no decorators.

**Note**: By default `/version` will be created with no scope. To modify this, pass a `version` keyword to Watchman as described above.




## development

A Vagrantfile and puppet manifest are available for development within a virtual machine. To use the vagrant VM defined here you will need to install *Vagrant* and *VirtualBox*. 

  * [Vagrant](https://docs.vagrantup.com)
  * [VirtualBox](https://www.virtualbox.org)

To load and enter the VM: `vagrant up && vagrant ssh`
