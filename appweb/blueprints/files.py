# -*- coding: utf-8 -*-
"""
    Controladores de las páginas de búsqueda y de fichero.
"""
import urllib, json, unicodedata, random, sys, bson
from flask import request, render_template, g, current_app, jsonify, flash, redirect, url_for, abort, Markup

from foofind.blueprints.files import search_files, share
from foofind.blueprints.files.fill_data import secure_fill_data, get_file_metadata, init_data, choose_filename
from foofind.blueprints.files.helpers import *
from foofind.services import *
from foofind.utils import url2mid, mid2bin, mid2hex, mid2url, bin2hex, u, canonical_url, logging, is_valid_url_fileid
from foofind.utils.content_types import *
from foofind.utils.fooprint import Fooprint

files = Fooprint('files', __name__)

@files.route('/<lang>/<license>', methods=["POST"])
@csrf.exempt
def home():
    '''
    Renderiza la portada de la pestaña find de la aplicación.
    '''
    return render_template('index.html')

@files.route('/<lang>/<license>/search', methods=["POST"])
def search(query=None,filters=None):
    '''
    Gestiona las URL de busqueda de archivos para la aplicacion.
    '''

    url_with_get_params=False
    if query is None:
        query=request.form.get("q",None)
        if not query: #si no se ha buscado nada se manda al inicio
            flash("write_something")
            return redirect(url_for("files.home"))
        else: #sino se reemplazan los espacios que venian antes con un + en el query string y se extraen los filtros
            query = query.replace("+"," ").replace("/"," ")
            filters=filters2url(request.form)
            url_with_get_params=True

    query = query.replace("_"," ") if query is not None else None #para que funcionen la busqueda cuando vienen varias palabras
    dict_filters, has_changed = url2filters(filters) #procesar los parametros

    # obtiene parametros de busqueda de la url
    if query:
        args = dict_filters.copy()
        args["q"] = query
        g.args=args

    #sources que se pueden elegir
    fetch_global_data()

    sure = False
    total_found=0

    search_results = search_files(query, dict_filters, min_results=request.args.get("min_results",0), last_items=[])

    return render_template('search.html',
        query=query,
        files=search_results["files"],
        share_url=url_for(".search", query=query.replace(" ","_"), filters=filters2url(dict_filters),_external=True),
    )

