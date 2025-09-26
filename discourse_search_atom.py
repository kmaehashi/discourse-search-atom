#!/usr/bin/env python

import argparse
import urllib.parse
from datetime import datetime
import json

from feedgen.feed import FeedGenerator
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--query', required=True)
    parser.add_argument('--name')
    parser.add_argument('--output')
    params = parser.parse_args()

    name = params.name if params.name is not None else params.url

    records = get_records(params.url, params.query)
    feed = generate_atom_feed(records, params.url, name)
    if params.output is None:
        print(feed.decode('utf-8'))
    else:
        with open(params.output, 'wb') as f:
            f.write(feed)


def get_records(url, query):
    search_url = '{url}/search.json?q={query}'.format(
        url=url,
        query=urllib.parse.quote(query),
    )
    resp = requests.get(search_url)
    try:
        data = json.loads(resp.text)
    except Exception as e:
        raise RuntimeError(f'failed to parse: {resp.text}') from e

    topics = {x['id']: x for x in data['topics']}
    records = []
    for post in data['posts']:
        title = '{title} [{post_number}]'.format(
            title=topics[post['topic_id']]['fancy_title'],
            post_number=post['post_number'],
        )
        author = post['name'] if post['name'] is not None else post['username']
        snippet = '{author}: {blurb}'.format(
            author=author,
            blurb=post['blurb'],
        )
        post_date = datetime.strptime(
            post['created_at'], '%Y-%m-%dT%H:%M:%S.%f%z')
        post_url = '{url}/t/{topic_id}/{post_number}'.format(
            url=url,
            topic_id=post['topic_id'],
            post_number=post['post_number'],
        )
        records.append((title, post_url, snippet, post_date))
    return records


def generate_atom_feed(records, url, name):
    last_modified = None
    fg = FeedGenerator()
    fg.title(name)
    fg.id(url)
    for (title, post_url, snippet, post_date) in records:
        fe = fg.add_entry()
        fe.title(title)
        fe.id(post_url)
        fe.link(href=post_url)
        fe.content(snippet)
        fe.updated(post_date)

        if last_modified is None or (last_modified < post_date):
            last_modified = post_date
    if last_modified is not None:
        fg.updated(last_modified)
    return fg.atom_str(pretty=True)


if __name__ == '__main__':
    main()
