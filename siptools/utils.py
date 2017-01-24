from urllib import quote_plus
from hashlib import md5

def encode_path(path, suffix='', prefix=''):
    return suffix + quote_plus(path) + prefix

def encode_id(id, suffix=''):
    #print encode_path(path, suffix, prefix) + " to " + md5(encode_path(path,
    #    suffix, prefix)).hexdigest()
    return '_' + md5(id).hexdigest()
