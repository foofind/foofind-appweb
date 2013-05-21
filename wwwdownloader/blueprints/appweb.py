# -*- coding: utf-8 -*-
"""
    Controladores de las páginas de búsqueda y de fichero.
"""
import urllib, json, unicodedata, random, sys, bson
from flask import request, render_template, g, current_app, jsonify, flash, redirect, url_for, abort, Markup
from flask.ext.login import login_required, current_user
from flask.ext.babel import gettext as _
from flaskext.babel import format_datetime
from datetime import datetime
from timelib import strtotime
from struct import pack, unpack
from collections import OrderedDict
from copy import deepcopy
from base64 import b64encode, b64decode

from foofind.blueprints.files import search_files, share
from foofind.blueprints.files.fill_data import secure_fill_data, get_file_metadata, init_data, choose_filename
from foofind.blueprints.files.helpers import *
from foofind.services import *
from foofind.forms.files import SearchForm, CommentForm
from foofind.utils import url2mid, mid2bin, mid2hex, mid2url, bin2hex, u, canonical_url, logging, is_valid_url_fileid
from foofind.utils.content_types import *
from foofind.utils.splitter import split_phrase
from foofind.utils.pagination import Pagination
from foofind.utils.fooprint import Fooprint
from foofind.utils.seo import seoize_text

appweb = Fooprint('appweb', __name__, dup_on_startswith="/<lang>")

@appweb.context_processor
def file_var():
    if request.args.get("error",None)=="error":
        abort(404)

    return {"zone":"files","search_form":SearchForm(request.args),"share":share,"args":g.args,"active_types":g.active_types, "active_srcs":g.active_srcs}


@appweb.route('/')
def app_home(query=None,filters=None):
    '''
    Renderiza la portada de la pestaña find de la aplicación.
    '''
    return render_template('appweb/index.html',form=SearchForm(),lang=current_app.config["ALL_LANGS_COMPLETE"][g.lang],zone="home")

@appweb.route('/<lang>/appwebs')
@appweb.route('/<lang>/appwebs/<query>')
@appweb.route('/<lang>/appwebs/<query>/<path:filters>/')
def search(query=None,filters=None):
    '''
    Gestiona las URL de busqueda de archivos para la aplicacion.
    '''

    url_with_get_params=False
    if query is None:
        query=request.args.get("q",None)
        if not query: #si no se ha buscado nada se manda al inicio
            flash("write_something")
            return redirect(url_for("index.home"))
        else: #sino se reemplazan los espacios que venian antes con un + en el query string y se extraen los filtros
            query = query.replace("+"," ").replace("/"," ")
            filters=filters2url(request.args)
            url_with_get_params=True

    query = query.replace("_"," ") if query is not None else None #para que funcionen la busqueda cuando vienen varias palabras
    dict_filters, has_changed = url2filters(filters) #procesar los parametros
    if url_with_get_params or has_changed: #redirecciona si viene una url con get o si url2filters ha cambiado los parametros y no se mandan filtros si es un bot
        return redirect(url_for(".search", query=query.replace(" ","_"), filters=filters2url(dict_filters)),302)

    # obtiene parametros de busqueda de la url
    if query:
        args = dict_filters.copy()
        args["q"] = query
        g.args=args

    #sources que se pueden elegir
    fetch_global_data()

    sure = False
    total_found=0

    searchd.search(query, filters=dict_filters, start=True)
    search_results = search_files(query, dict_filters, min_results=request.args.get("min_results",0), last_items=[])

    return render_template('appweb/search.html',
        query=query,
        files=search_results["files"],
        share_url=url_for(".search", query=query.replace(" ","_"), filters=filters2url(dict_filters),_external=True),
    )

