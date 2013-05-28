# -*- coding: utf-8 -*-
"""
    Controladores de las páginas de búsqueda y de fichero.
"""
import json
from flask import request, render_template, g, current_app, flash, redirect, url_for

from foofind.blueprints.files import search_files
from foofind.blueprints.files.helpers import *

from foofind.services import *
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
def search():
    '''
    Gestiona las URL de busqueda de archivos para la aplicacion.
    '''
    query=request.form.get("q",None)
    filetype=request.form.get("t",None)

    if not query: #si no se ha buscado nada se manda al inicio
        flash("write_something")
        return redirect(url_for(".home"))

    query = query.replace("_"," ") if query is not None else None #para que funcionen la busqueda cuando vienen varias palabras
    filters = {"src":"torrent"}
    if filetype and filetype in CONTENTS_CATEGORY:
        filters["type"] = [filetype]
    args = filters.copy()
    args["q"] = query
    g.args=args

    #sources que se pueden elegir
    fetch_global_data()

    sure = False
    total_found=0

    search_results = search_files(query, filters, min_results=50, last_items=[], non_group=True)
    files_list = []
    files_info = {}
    for index, afile in enumerate(search_results["files"]):
        afile_torrent, torrent_info = torrents_data(afile)
        if not afile_torrent:
            continue
        afile_torrent["index"] = index
        files_list.append(afile_torrent)
        files_info[str(index)] = torrent_info

    return render_template('search.html',
        query=query,
        files=files_list,
        files_info = json.dumps(files_info),
    )

def torrents_data(data):
    valid_torrent = False

    if not data or not "sources" in data["view"]:
        return None, None

    sources_list = []
    torrent_info = {"sources": sources_list}
    for source, item in data["view"]["sources"].iteritems():
        if source == "tmagnet":
            torrent_info["magnet"] = item["urls"][0]
            valid_torrent = True
        elif item["icon"]=="torrent":
            valid_torrent = True
            sources_list.extend(item["urls"])

    # no tiene origenes validos
    if not valid_torrent:
        return None, None

    desc = None
    # organiza mejor la descripcion del fichero
    if "description" in data["view"]["md"]:

        # recupera la descripcion original
        desc = data["view"]["md"]["description"]
        del data["view"]["md"]["description"]

        # inicializa variables
        long_desc = False
        short_desc = None
        acum = []

        # recorre las lineas de la descripcion
        for line in desc.split("\n"):
            # si llega a pasar despues acumular algo, hay que mostrar la desc larga
            if acum:
                long_desc = True

            # ignora lineas con muchos caracteres repetidos
            prev_char = repeat_count = 0
            for char in line:
                if prev_char==char:
                    repeat_count+=1
                else:
                    repeat_count = 0
                if repeat_count>5:
                    line=""
                    break
                prev_char = char

            # si la linea es "corta", la toma como fin de parrafo
            if len(line)<50:
                if acum:
                    if line: acum.append(line)

                    # si el parrafo es mas largo que 110, lo usa
                    paraph = " ".join(acum)
                    acum = [] # antes de seguir reinicia el acum
                    paraph_len = len(paraph)
                    if paraph_len>90:
                        short_desc = paraph
                        if paraph_len>140: # si no es suficientemente larga sigue buscando
                            break
                    continue
            else: # si no, acumula
                acum.append(line)

        # procesa el parrafo final
        if acum:
            paraph = " ".join(acum)
            paraph_len = len(paraph)
            if paraph_len>90:
                short_desc = paraph

        # si hay descripcion corta se muestra y se decide si se debe mostrar la larga tambien
        if short_desc:
            data["view"]["md"]["short_desc"] = short_desc
            long_desc = long_desc or len(short_desc)>400
        else:
            long_desc = True

        if not long_desc and "nfo" in data["file"]["md"]:
            desc = data["file"]["md"]["nfo"]
            long_desc = True

        if long_desc and short_desc!=desc:
            if len(desc)>400:
                data["view"]["md"]["long_desc"] = desc
            else:
                data["view"]["md"]["description"] = desc

    # preview
    if "torrent:thumbnail" in data["file"]["md"]:
        data["view"]["thumbnail"] = data["file"]["md"]["torrent:thumbnail"]

    # salud del torrent
    try:
        seeds = int(float(data['view']['md']['seeds'])) if 'seeds' in data['view']['md'] else 0
    except:
        seeds = 0
    try:
        leechs = int(float(data['view']['md']['leechs'])) if 'leechs' in data['view']['md'] else 0
    except:
        leechs = 0

    base_rating = int(2/(leechs+1.)) if seeds==0 else min(10,int(seeds/(leechs+1.)*5))
    data['view']['health'] = int(base_rating/2.5)
    data['view']['rating'] = base_rating/2

    # informacion para el torrent
    torrent_info["name"] = data['view']['fn']
    torrent_info["seeds"] = seeds
    torrent_info["leechs"] = leechs
    torrent_info["type"] = data['view']['file_type']

    return data, torrent_info
