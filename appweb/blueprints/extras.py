#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import operator
import sys
import os.path
import functools

from flask import g, Blueprint, render_template, url_for, abort, send_file, current_app, request, redirect

extras = Blueprint("extras", __name__)

from foofind.services import plugindb

def referrer_check(fnc):
    @functools.wraps(fnc)
    def wrapped(*args, **kwargs):
        if request.referrer and request.referrer.startswith(request.url_root):
            return fnc(*args, **kwargs)
        abort(404)
    return wrapped

INFINITE = float("inf")

def category_order(data):
    if data.title.lower() == "featured":
        return -INFINITE
    return data.title

# someone's spaggheti code workaround
from foofind.blueprints.files.helpers import csrf
@extras.route("/<lang>/extras", methods=("POST",))
@csrf.exempt
def home():
    # like category without referer check
    plugins, categories = plugindb.get_plugins_with_categories()
    categories = sorted(categories.itervalues(), key=category_order)
    reqos = request.user_agent.platform # operative system for params
    return render_template('extras.html', categories=categories, page=1, reqos=reqos)

@extras.route("/<lang>/extras", defaults={"page":1, "category":None})
@extras.route("/<lang>/extras/<category>", defaults={"page":1})
@extras.route("/<lang>/extras/<category>/<int:page>")
@referrer_check
def category(category, page):
    '''
    Extras front page
    '''
    page = max(page, 1)
    if category:
        plugins = plugindb.get_plugins(category, page-1)
        categories = None
        category = plugins[0].category if plugins else plugindb.get_category(category)
    else:
        plugins, categories = plugindb.get_plugins_with_categories(page=page-1)
        categories = sorted(categories.itervalues(), key=category_order)
        category = None

    reqos = request.user_agent.platform # operative system for params
    return render_template('extras.html', categories=categories, category=category, page=page, reqos=reqos)

@extras.route("/<lang>/list", methods=("POST",))
def list():
    '''

    '''
    if "plugins" in request.form:
        plugins = plugindb.get_plugins_by_name(request.form["plugins"].split(","))
    else:
        plugins = []
    reqos = request.user_agent.platform # operative system for params
    return render_template('extras.html', plugins=plugins, reqos=reqos)

@extras.route("/<lang>/extras/info/<name>", defaults={"page":1, "category":None})
@extras.route("/<lang>/extras/<category>/<int:page>/<name>")
@referrer_check
def info(category, page, name):
    '''

    '''
    page = max(page, 1)
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
