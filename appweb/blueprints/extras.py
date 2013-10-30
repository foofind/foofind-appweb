#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import operator
import sys
import os.path

from flask import g, Blueprint, render_template, url_for, abort, send_file, current_app, request, redirect

extras = Blueprint("extras", __name__)

from foofind.services import plugindb

@extras.route("/<lang>/extras", methods=("GET", "POST"), defaults={"page":0, "category":None}) # TODO(felipe): remove GET method
@extras.route("/<lang>/extras/<category>", methods=("GET", "POST"), defaults={"page":0})
@extras.route("/<lang>/extras/<category>/<int:page>", methods=("GET", "POST"))
def category(category, page):
    '''
    Extras front page
    '''
    if category:
        plugins = plugindb.get_plugins(category, page)
        categories = None
        category = plugins[0].category if plugins else plugindb.get_category(category)
    else:
        plugins, categories = plugindb.get_plugins_with_categories(page=page)
        categories = sorted(categories.itervalues(), key=operator.attrgetter("title"))
        category = None

    reqos = request.user_agent.platform # operative system for params
    return render_template('extras.html', categories=categories, category=category, page=page, reqos=reqos)

@extras.route("/<lang>/extras/info/<category>/<int:page>/<name>")
@extras.route("/<lang>/extras/info/<int:page>/<name>", defaults={"category":None})
@extras.route("/<lang>/extras/info/<name>", defaults={"category":None, "page":0})
def info(category, page, name):
    '''

    '''
    plugin = plugindb.get_plugin(name)
    if plugin is None:
        abort(404)
    if category:
        category = plugindb.get_category(category)
    reqos = request.user_agent.platform # operative system for params
    return render_template('extras.html', plugin=plugin, category=category, page=page, reqos=reqos)

@extras.route("/<lang>/extras/download/<platform>/<name>")
def download(platform, name):
    path = plugindb.get_download(name, platform)
    if path:
        prefix = current_app.config["EXTRAS_DOWNLOAD_PATH"] + os.sep
        if path.startswith(prefix):
            return redirect(url_for(".download_static", path=path[len(prefix):]))
        try:
            return send_file(path)
        except:
            pass
    abort(404)

@extras.route("/static_extras/image/<name>.<image>.png")
def image(name, image):
    '''

    '''
    path = os.path.abspath(plugindb.get_image(name, image))
    if path:
        try:
            return send_file(path, mimetype="image/png")
        except:
            pass
    abort(404)

@extras.route("/static_extras/download/<path:path>")
def download_static(path):
    '''
    Static fallback (server could not be configured to serve downloads statically)
    '''
    prefix = os.path.abspath(current_app.config["EXTRAS_DOWNLOAD_PATH"]) + os.sep
    apath = os.path.normpath(prefix + path)
    if apath.startswith(prefix):
        try:
            return send_file(apath)
        except:
            pass
    abort(404)
