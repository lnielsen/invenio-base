# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

"""Invenio application."""

from __future__ import absolute_import, print_function

import logging
import os.path
import sys
import warnings

from flask import Flask
from flask_cli import FlaskCLI


def _(x):
    return x


def configure_warnings():
    """Configure warnings by routing warnings to the logging system.

    It also unhides ``DeprecationWarning``.
    """
    if not sys.warnoptions:
        # Route warnings through python logging
        logging.captureWarnings(True)

        # DeprecationWarning is by default hidden, hence we force the
        # "default" behavior on deprecation warnings which is not to hide
        # errors.
        warnings.simplefilter("default", DeprecationWarning)


def create_app(instance_path=None, static_folder=None,
               static_url_path='/static/', **kwargs):
    """Invenio application factory."""
    configure_warnings()

    prefix = "INVENIO_"
    app_name = "invenio"

    # Detect instance path
    instance_path = instance_path or \
        os.getenv(prefix + 'INSTANCE_PATH') or \
        os.path.join(sys.prefix, 'var', app_name + '-instance')

    # Detect static files path
    static_folder = static_folder or \
        os.getenv(prefix + 'STATIC_FOLDER') or \
        os.path.join(instance_path, 'static')

    # Create instance path if it doesn't exists
    try:
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
    except Exception:  # pragma: no cover
        pass

    # Create the Flask application instance
    app = Flask(
        app_name,
        instance_path=instance_path,
        instance_relative_config=True,
        static_folder=static_folder,
        static_url_path=static_url_path,
    )
    FlaskCLI(app)

    # Configuration loading
    from invenio_assets import InvenioAssets
    from invenio_celery import InvenioCelery
    from invenio_config import InvenioConfigDefault, \
        InvenioConfigEnvironment, InvenioConfigInstanceFolder, \
        InvenioConfigModule
    from invenio_theme import InvenioTheme, bundles

    InvenioConfigModule(app=app, entrypoint='invenio.config_modules')
    InvenioConfigInstanceFolder(app)
    app.config.update(**kwargs)
    InvenioConfigEnvironment(app, prefix=prefix)
    InvenioConfigDefault(app)

    # Explicit dependency and registration
    InvenioCelery(app)

    theme = InvenioTheme()
    theme.init_app(app)

    assets = InvenioAssets()
    assets.init_app(app)
    assets.init_cli(app.cli)

    # Bind
    theme.init_assets(assets.env)

    # or
    #assets.env.register('invenio_theme_css', theme_bundles.css)
    #assets.env.register('invenio_theme_js', theme_bundles.js)

    return app
