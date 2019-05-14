REGEXS = {
    'uri': r'/(?!(dev|proc))([\w\.]+/)+\w+\.php',
    'url': r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)',
    'email': r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
    'device': r'/dev(/[\w\.]+)+',
    'process': r'/proc(/[\w\.]+)+',
    'ip_address': r'(tcp/)?([0-9]{1,3}\.){3}[0-9]{1,3}((\+[0-9]{1,3})|:[0-9]{1,5})?',
    'memory_address': r'0x[a-zA-Z0-9]+((-|\s)[a-zA-Z0-9]+)?',
    'uuid': r'\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-\b[0-9a-fA-F]{12}\b',
    'memory_k': r'\b\d+[kK][bB]?\b',
    'disk_mb': r'\b\d+[mM][bB]?\b',
    'disk_gb': r'\b\d+[gG][bB]?\b',
    'clock_speed': r'\b\d+(\.\d+)?GHz\b',
    # put these last
    'file': r'/(?!(dev|proc))([\w\.]+/)+\w+(?!\.php)(\.\w+)?',
    'version': r'\b[vV]?\d+(\.\d+)+(-[0-9a-zA-Z]+)?\b',
    'number': r'\b(?<=\s)\d+(?=\s)\b',
}
