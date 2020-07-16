#!/usr/bin/python3

import hashlib
import datetime
import export_pb2 # https://github.com/google/exposure-notifications-server/blob/main/internal/pb/export/export.proto
import json
import os
import urllib.parse
import urllib.request
import zipfile

cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'cache'))
os.makedirs(cache_dir, exist_ok=True)

cdn_prefix = 'https://covid19radar-jpn-prod.azureedge.net/c19r/'
list_urls = [
    ('list1.json', cdn_prefix + '440/list.json'),
    ('list2.json', cdn_prefix + '441/list.json'),
]

def cached_fetch(name, url):
    path = os.path.join(cache_dir, name)
    cache_hit = False
    try:
        rv = os.stat(path)
        cached = datetime.datetime.fromtimestamp(rv.st_mtime)
        now = datetime.datetime.now()
        cache_hit = now < cached + datetime.timedelta(hours=1)
    except FileNotFoundError as e:
        pass

    if not cache_hit:
        urllib.request.urlretrieve(url, path)
    return path

file_urls = []
for name, url in list_urls:
    with open(cached_fetch(name, url)) as fd:
        for item in json.load(fd):
            file_urls.append(item['url'])

# i = 0
for url in file_urls:
    # i += 1
    name = hashlib.sha256(url.encode()).hexdigest()[:8]
    # name = os.path.basename(urllib.parse.urlparse(url).path)
    # print(name)
    with zipfile.ZipFile(cached_fetch(name, url)) as zip:
        with zip.open('export.bin') as bin:
            assert(bin.read(16) == b'EK Export v1    ')
            teke = export_pb2.TemporaryExposureKeyExport.FromString(bin.read())
            # print(teke)
            for key in teke.keys:
                # print('  key_data: {}'.format(key.key_data))
                ts = key.rolling_start_interval_number * 10 * 60
                print('{}: timestamp: {}'.format(name, datetime.datetime.fromtimestamp(ts)))
                if key.HasField('report_type'):
                    name = export_pb2.TemporaryExposureKey.ReportType.Name(key.report_type)
                    print(' report_type: {}'.format(name))
                # print(key)
