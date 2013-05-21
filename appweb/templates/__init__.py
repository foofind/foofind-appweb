# -*- coding: utf-8 -*-
from foofind.templates import number_format_filter, number_size_format_filter, format_timedelta_filter, urlencode_filter, number_friendly_filter, pformat, numeric_filter, markdown_filter, seoize_filter
from foofind.utils.htmlcompress import HTMLCompress

import foofind.templates
def _(x): return x
foofind.templates._ = _

def register_filters(app):
    '''
    Registra filtros de plantillas
    '''
    app.jinja_env.filters['numberformat'] = number_format_filter
    app.jinja_env.filters['numbersizeformat'] = number_size_format_filter
    app.jinja_env.filters['format_timedelta'] = format_timedelta_filter
    app.jinja_env.filters['urlencode'] = urlencode_filter
    app.jinja_env.filters['numberfriendly'] = number_friendly_filter
    app.jinja_env.filters['pprint'] = pformat
    app.jinja_env.filters['numeric'] = numeric_filter
    app.jinja_env.filters['markdown'] = markdown_filter
    app.jinja_env.filters['seoize'] = seoize_filter
    app.jinja_env.add_extension(HTMLCompress)
