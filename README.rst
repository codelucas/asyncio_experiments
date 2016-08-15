**Motivation**:

I'm curious on the relationship between the # of HTTP `Range requests` to download latency.
Is it more efficient to download a huge file, say an image, in one request?  Or to split it up among 5 requests? How about 10? *At what threshold is it not worth it to continue splitting the request up?*

**Results**:

I ran the code myself with 10 iterations on a 10MB image and tested the split sizes
`1, 4, 10, 16, 25, 50, 100, 200` and found that:

.. code-block:: pycon

    200 request splits resulted in average 5.8094 sec over 10 iterations ; 55,437 bytes per split
    100 request splits resulted in average 5.9908 sec over 10 iterations ; 110,875 bytes per split
    50 request splits resulted in average 6.5629 sec over 10 iterations ; 221,750 bytes per split
    25 request splits resulted in average 7.2891 sec over 10 iterations ; 443,500 bytes per split
    16 request splits resulted in average 8.1770 sec over 10 iterations ; 692,969 bytes per split
    10 request splits resulted in average 8.6593 sec over 10 iterations ; 1,108,751 bytes per split
    4 request splits resulted in average 11.6698 sec over 10 iterations ; 2,771,878 bytes per split
    1 request splits resulted in average 14.7066 sec over 10 iterations ; 11,087,513 bytes per split


Interesting! Even though our data sample size wasn't massive we can already see patterns:

- More splits --> smaller payload per request --> faster concurrent downloading via asyncio
- Going from 100 -> 200 splits seemed to have largely depreciating returns in latency!
  - Thus, 110KB -> 55KB per request isn't that big of a saving (200ms) and perhaps the sweet spot is somewhere neat 50kb per request.

**Try it yourself**:

This code uses python3's new asyncio features; *You must run this code with python 3.5+!*

Feel free to toggle the ```NUM_ITERATIONS``` split sizes, and ```VERBOSE``` variables to get your own experiment going :) Don't forget to install aiohttp

.. code-block:: pycon

    virtualenv asyncio-experiments
    cd asyncio-experiments
    source bin/activate
    git clone https://github.com/codelucas/asyncio_experiments.git
    cd asyncio_experiments
    pip3 install aiohttp
    python3.5 main.py


**Caveats**:

- This experiment is kinda undeveloped, there are still many variables that matter but are not measured, such as:
   - The location of the server hosting the file, I just picked an arbitrary large img hosted on wikipedia
   - Your internet connection
   - Implementation of webserver hosting the file
   - I wanted to use a more granular set of split sizes but didn't for the sake of time
   - Any split size above 100 caused wikipedia's server to give me error response codes for too many sockets
- If a site doesn't accept range requests, this api will fail with a printed error message
- To not put burden on targeted sites, I set a sleep timer to 3 seconds between every iteration
   - Try using this api to just target big websites that can probably handle the load
   - You might get rate limited depending on the site hosting the url

By Lucas Ou-Yang, *lucasyangpersonal@gmail.com*

http://codelucas.com
