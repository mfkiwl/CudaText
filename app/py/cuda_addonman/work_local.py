import json
import os
import collections
import zipfile
import tempfile
from cudatext import *

README_NAMES = (
    'readme.txt',
    'readme.html',
    'readme.htm',
    'readme.md',
    'README.md',
    'readme.rst',
    'README.rst',
    )

HISTORY_NAMES = (
    'history.txt',
    'history.md',
    'history.rst',
    'history',
)

DATA_DIRS = (
    ('autocomplete', '.acp'),
    ('lang', '.ini'),
    ('newdoc', ''),
    ('snippets', ''),
    ('themes', ''),
    )

def _root_item(s):

    n = s.rfind('/')
    return n<0 or n==len(s)-1

def get_props_of_zip_filename(zip_fn):

    temp_dir = tempfile.gettempdir()
    z = zipfile.ZipFile(zip_fn, 'r')

    files = z.namelist()
    if 'install.inf' in files:
        files.remove('install.inf')
    files = [f for f in files if _root_item(f)]

    z.extract('install.inf', temp_dir)
    z.close()
    fn = os.path.join(temp_dir, 'install.inf')

    if os.path.isfile(fn):
        typ = ini_read(fn, 'info', 'type', '')
        subdir = ini_read(fn, 'info', 'subdir', '')

        if typ=='cudatext-plugin':
            d = 'py'
            files = [subdir+'/']
        elif typ=='cudatext-data':
            d = 'data/'+subdir
        elif typ=='lexer':
            d = 'data/lexlib'
        elif typ=='lexer-lite':
            d = 'data/lexliblite'
        else:
            d = ''

        os.remove(fn)
        #print('prop', (d, files, subdir))
        return (d, files, subdir)


def get_readme_of_module(mod):
    for name in README_NAMES:
        fn = os.path.join(app_path(APP_DIR_PY), mod, 'readme', name)
        if os.path.isfile(fn):
            return fn
        fn = os.path.join(app_path(APP_DIR_PY), mod, name)
        if os.path.isfile(fn):
            return fn

def get_history_of_module(mod):
    for name in HISTORY_NAMES:
        fn = os.path.join(app_path(APP_DIR_PY), mod, 'readme', name)
        if os.path.isfile(fn):
            return fn
        fn = os.path.join(app_path(APP_DIR_PY), mod, name)
        if os.path.isfile(fn):
            return fn


def get_installinf_of_module(mod):
    return os.path.join(app_path(APP_DIR_PY), mod, 'install.inf')

def get_initpy_of_module(mod):
    return os.path.join(app_path(APP_DIR_PY), mod, '__init__.py')

def get_name_of_module(mod):
    fn_ini = get_installinf_of_module(mod)
    return ini_read(fn_ini, 'info', 'title', mod)

def get_homepage_of_module(mod):
    fn_ini = get_installinf_of_module(mod)
    return ini_read(fn_ini, 'info', 'homepage', '')


def do_remove_dir(dir):
    """
    move folder to py/__trash
    (make copy with _ suffix if nessesary)
    """
    print('Deleting folder:', dir)
    if not os.path.isdir(dir):
        return

    dir_trash = os.path.join(app_path(APP_DIR_PY), '__trash')
    dir_dest = os.path.join(dir_trash, os.path.basename(dir))
    while os.path.isdir(dir_dest):
        dir_dest += '_'

    if not os.path.isdir(dir_trash):
        os.mkdir(dir_trash)

    try:
        os.rename(dir, dir_dest)
    except OSError:
        msg_box('Cannot remove folder:\n'+dir, MB_OK+MB_ICONERROR)
        return
    return True


def get_installed_modules():
    """
    gets list of py-modules inside "py"
    """
    d = app_path(APP_DIR_PY)
    l = os.listdir(d)
    l = [s for s in l if not s.startswith('__')]
    l = [s for s in l if os.path.isfile(os.path.join(d, s, 'install.inf'))]
    return sorted(l)

def get_installed_lexers():
    """
    gets list of lexer names inside "lexlib" and "lexliblite"
    """
    d = os.path.join(app_path(APP_DIR_DATA), 'lexlib')
    l = os.listdir(d)
    res = [s for s in l if s.endswith('.lcf')]

    d = os.path.join(app_path(APP_DIR_DATA), 'lexliblite')
    l = os.listdir(d)
    res += [s for s in l if s.endswith('.cuda-litelexer')]

    res = [s.replace(' ', '_').split('.')[0] for s in res]
    return sorted(res)

def get_installed_choice(caption, exclude_list=None):
    """
    gets module of addon, from menu of installed addons
    """
    lmod = get_installed_modules()
    if exclude_list:
        lmod = [i for i in lmod if not i in exclude_list]
    ldesc = [get_name_of_module(l) for l in lmod]
    res = dlg_menu(MENU_LIST, ldesc, caption=caption)
    if res is None:
        return None
    return lmod[res]


def get_installed_items_ex(
    exclude_modules, 
    exclude_lexers, 
    exclude_lexers_lite,
    exclude_themes,
    exclude_translations,
    exclude_snippets,
    ):

    d = app_path(APP_DIR_PY)
    l = get_installed_modules()
    l = [i for i in l if not i in exclude_modules]
    res = [{
        'kind': 'plugin',
        'name': get_name_of_module(i),
        'module': i,
        'files': [
            os.path.join(d, i)+'/',
            ],
        } for i in l]

    d = os.path.join(app_path(APP_DIR_DATA), 'lexlib')
    d_acp = os.path.join(app_path(APP_DIR_DATA), 'autocomplete')
    l = os.listdir(d)
    l = [i.split('.')[0] for i in l if i.endswith('.lcf')]
    l = [i for i in l if not i in exclude_lexers]
    l = sorted(l)
    res += [{
        'kind': 'lexer',
        'name': i,
        'files': [
            os.path.join(d, i+'.lcf'),
            os.path.join(d, i+'.cuda-lexmap'),
            os.path.join(d_acp, i+'.acp'),
            ],
        } for i in l]

    d = os.path.join(app_path(APP_DIR_DATA), 'lexliblite')
    l = os.listdir(d)
    l = [i.split('.')[0] for i in l if i.endswith('.cuda-litelexer')]
    l = [i for i in l if not i in exclude_lexers_lite]
    l = sorted(l)
    res += [{
        'kind': 'lexer',
        'name': i+' ^',
        'files': [
            os.path.join(d, i+'.cuda-litelexer'),
            ],
        } for i in l]

    d = os.path.join(app_path(APP_DIR_DATA), 'snippets')
    l = os.listdir(d)
    l = [i for i in l if not i in exclude_snippets]
    l = sorted(l)
    res += [{
        'kind': 'snippets',
        'name': i,
        'files': [
            os.path.join(d, i)+'/',
            ],
        } for i in l]

    d = os.path.join(app_path(APP_DIR_DATA), 'themes')
    l = os.listdir(d)
    l = [i.split('.')[0] for i in l if i.endswith('.cuda-theme-syntax') or i.endswith('.cuda-theme-ui')]
    l = [i for i in l if not i in exclude_themes]
    l = list(set(l)) # del duplicates
    l = sorted(l)
    res += [{
        'kind': 'theme',
        'name': i,
        'files': [
            os.path.join(d, i+'.cuda-theme-syntax'),
            os.path.join(d, i+'.cuda-theme-ui'),
            ],
        } for i in l]

    d = os.path.join(app_path(APP_DIR_DATA), 'lang')
    l = os.listdir(d)
    l = [i.split('.')[0] for i in l if i.endswith('.ini')]
    l = [i for i in l if not i in exclude_translations]
    l = sorted(l)
    res += [{
        'kind': 'translation',
        'name': i,
        'files': [
            os.path.join(d, i+'.ini'),
            ],
        } for i in l]

    return res


def get_packages_ini():

    return os.path.join(app_path(APP_DIR_SETTINGS), 'packages.ini')


def do_save_version(url, fn, version):

    props = get_props_of_zip_filename(fn)
    if props:
        d, f, m = props
        fn = get_packages_ini()
        sec = os.path.basename(url)
        ini_write(fn, sec, 'd', d)
        ini_write(fn, sec, 'f', ';'.join(f))
        ini_write(fn, sec, 'v', version)
        return props


def get_addon_version(url):

    fn = get_packages_ini()
    return ini_read(fn, os.path.basename(url), 'v', '')


def do_remove_version_of_plugin(mod):

    import configparser
    fn = get_packages_ini()
    config = configparser.ConfigParser()
    config.read(fn)
    for sec in config.sections():
        if config[sec]['d'] == 'py' and config[sec]['f'] == mod+'/':
            del config[sec]
            with open(fn, 'w') as f:
                config.write(f, False)
