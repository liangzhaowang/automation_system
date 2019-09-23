#!/usr/bin/python
import os
import re
import requests


def get_build_date_number(lines, index_number):
    """
    get_aimed_build_number
    """
    build_date = lines[index_number].split('/')[0]
    return build_date


def read_html(headers, url):
    html = ''
    try:
        requests.packages.urllib3.disable_warnings()
        html = requests.get(url, proxies={}, verify=False, headers=headers).content
    except Exception, e:
        print e
    return html


def read_new_aimed_date(headers, top_level_url, build_number=''):
    """
    date ready
    """
    if build_number == '':
        pattern = re.compile(r'<[^>]+>', re.S)
        html_page = read_html(headers, top_level_url)
        html_content = pattern.sub('', html_page)
        lines = html_content.split('\n')
        lines.reverse()
        index_number = 2
        return get_build_date_number(lines, index_number)
    else:
        return build_number


def find_image(headers, url):
    """
    find new image
    """
    pattern = re.compile(r'<[^>]+>', re.S)
    child_html = read_html(headers, url)
    html_content = pattern.sub('', child_html)
    child_lines = html_content.split('\n')
    for line in child_lines:
        if 'flashfiles' in line and '.zip' in line:
            for word in line.split(' '):
                if word.count("flashfiles"):  # modify by yuwei@20161117 word == 'MB' or 'GB' == word:
                    download_url = os.path.join(url, line.split(' ')[0].strip('->'))
                    print 'download_url', download_url
                    return download_url


def output_download_url(headers, top_level_url, build_info, build_number=''):
    """
    output_download_url
    """
    url = os.path.join(top_level_url, read_new_aimed_date(headers, top_level_url, build_number)) + '/%s/userdebug/' % build_info
    return find_image(headers, url)
