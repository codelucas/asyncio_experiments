# encoding=utf-8

# Lucas Ou-Yang, 2016

import asyncio
import itertools
import time

import aiohttp


NUM_ITERATIONS = 1
VERBOSE = True

class Timer(object):
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.elapsed = self.end - self.start


async def inspect_size(url):
    """Returns an integer content length if the url is range-query-able --> a candidate
    for this experiment, otherwise returns None
    """
    async with aiohttp.head(url) as resp:
        accepted_ranges = resp.headers['Accept-Ranges']
        if accepted_ranges and accepted_ranges.lower() == 'bytes':
            content_length = resp.headers['Content-Length']
            if content_length:
                return int(content_length)
    return None


async def range_get(url, start, end):
    http_headers = {
        'Range': 'bytes={}-{}'.format(start, end - 1 if end else '')
    }
    if VERBOSE:
        print('Performing range-get on bytes: %s-%s' % (str(start), str(end)))
    async with aiohttp.get(url, headers=http_headers) as resp:
        assert resp.status // 100 == 2
        return await resp.read()


async def download(url, num_splits):
    content_length = await inspect_size(url)  # http.head isn't considered / timed in experiment
    if content_length:
        size_request = content_length // num_splits
        ranges = list(range(0, content_length, size_request))
        if VERBOSE:
            print('Performing %s asyncio requests on a url with content-length %s bytes'
                  % (str(num_splits), str(content_length)))
            print('Each split will be %s bytes' % str(size_request))
        with Timer() as t:
            tasks, _ = await asyncio.wait([
                range_get(url, start, end)
                for start, end in itertools.zip_longest(ranges, ranges[1:], fillvalue="")
            ])
        assert len(tasks) == len(ranges)  # this assertions indicates no pending futures
        if VERBOSE:
            print('Function download(num_splits=%d) took %2.4f sec.' %
                  (num_splits, t.elapsed))
        return (num_splits, t.elapsed)
    else:
        print('URL: %s does not accept range GET queries, not candidate for this '
              'experiment')
    return


async def download_many(url, splits):
    tally = {}
    for i in range(NUM_ITERATIONS):
        print('Starting iteration %d' % (i + 1))
        tasks, pending = await asyncio.wait([
            download(url, split) for split in splits
        ])
        assert len(pending) == 0
        current_tally = {}
        for task in tasks:
            _splits, _elapsed = task.result()
            current_tally[_splits] = _elapsed
        tally[i + 1] = current_tally
        await asyncio.sleep(3)  # Give the website a break!
    return tally


if __name__ == '__main__':
    # This is a large (almost 11MB) image
    url = 'http://northwestcoast.ca/wp-content/uploads/2014/07/' \
          'Matier-and-Stonecrop-Glacier-Joffre-Provincial-Park-large.jpg'

    splits = [1, 4, 10, 16, 25, 50, 100]

    loop = asyncio.get_event_loop()
    tally = loop.run_until_complete(download_many(url, splits))

    # aggregate tally
    split_counters = {s: 0 for s in splits}

    for _, dd in tally.items():
        for _split, _elapsed in dd.items():
            split_counters[_split] += _elapsed

    for _split, _total_elapsed in split_counters.items():
        final = float(_total_elapsed) / NUM_ITERATIONS
        print('%d request splits resulted in average %2.4f sec over %d iterations' %
              (_split, final, NUM_ITERATIONS))
