# -*- coding: utf-8 -*-
from babel.numbers import get_decimal_symbol, get_group_symbol
from math import log

from foofind.templates import number_format_filter, format_timedelta_filter, urlencode_filter, number_friendly_filter, pformat, numeric_filter, markdown_filter, seoize_filter
from foofind.utils.htmlcompress import HTMLCompress
from foofind.utils import logging

import foofind.templates
def _(x): return x
foofind.templates._ = _

def register_filters(app):
    '''
    Registra filtros de plantillas
    '''
    app.jinja_env.filters['numberformat'] = number_format_filter
    app.jinja_env.filters['format_timedelta'] = format_timedelta_filter
    app.jinja_env.filters['urlencode'] = urlencode_filter
    app.jinja_env.filters['numberfriendly'] = number_friendly_filter
    app.jinja_env.filters['pprint'] = pformat
    app.jinja_env.filters['numeric'] = numeric_filter
    app.jinja_env.filters['markdown'] = markdown_filter
    app.jinja_env.filters['seoize'] = seoize_filter
    app.jinja_env.globals["number_size_format"] = number_size_format
    app.jinja_env.add_extension(HTMLCompress)

format_cache = {}
def number_size_format(size, lang="en"):
    '''
    Formatea un tamaño de fichero en el idioma actual
    '''
    if not size:
        return ""
    elif int(float(size))==0:
        return "0 B"

    if lang in format_cache:
        decimal_sep, group_sep = format_cache[lang]
    else:
        decimal_sep, group_sep = format_cache[lang] = (get_decimal_symbol(lang), get_group_symbol(lang))

    try:
        if size<1000: # no aplica para los bytes
            return str(size)+" B"
        else:
            size = log(float(size),1000)
            number = 1000**(size-int(size))

            # parte decimal
            dec_part = int((number-int(number))*100)
            dec_part = "" if dec_part==0 else decimal_sep+"0"+str(dec_part) if dec_part<10 else decimal_sep+str(dec_part)

            # genera salida
            return ''.join(
                reversed([c + group_sep if i != 0 and i % 3 == 0 else c for i, c in enumerate(reversed(str(int(number))))])
            ) + dec_part, (("KB","kilobytes"),("MB","megabytes"),("GB","gigabytes"),("TB","terabytes"))[int(size)-1]
    except BaseException as e:
        logging.exception(e)
        return ""
