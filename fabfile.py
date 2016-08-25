#!/usr/bin/env python
# -*- coding:utf-8 -*-

from management import test, web, docs
from management.settings import update_settings


update_settings({
    'assets' : {
        'material-icons': {
            'source':'./web_src/bower_components/mdi/fonts/',
            'target':'./www/fonts/',
            'pattern':'.*'
        },
        'html':{
            'source':'./web_src/',
            'target':'./www/',
            'pattern':'.*\.html'
        }
    },
    'sass_files': [ "./web_src/sass/base.scss",
                    "./web_src/sass/widgets.scss",
                    "./web_src/bower_components/mdi/scss/materialdesignicons.scss"],
    'css_files':[],
    'css_asset_dir':'./www/css'
},'web')

from management import *

