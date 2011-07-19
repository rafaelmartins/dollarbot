# -*- coding: utf-8 -*-

from contextlib import closing
from datetime import date, datetime, timedelta
from re import compile as re_compile
from urllib import urlencode
from urllib2 import Request, urlopen

_re_rate = re_compile(r'<p class="rate">1 (?P<for>[A-Z]+) = ' + \
                      r'(?P<rate>[0-9.]+) (?P<from>[A-Z]+)</p>')
_user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20110618 ' + \
            'Firefox/4.0.1'
_visa_url = 'http://corporate.visa.com/pd/consumer_services/' + \
          'consumer_ex_results.jsp'


class VisaExchangeRate:

    _rate_cache = None
    _cache_time = None

    def __init__(self, from_cur, for_cur, fee, cache_lifetime=3600):
        self._from_cur = from_cur
        self._for_cur = for_cur
        self._fee = fee
        self._cache_lifetime = cache_lifetime
        assert fee >= 0 and fee <= 5, 'fee should be in the range 0-5.'
        assert isinstance(fee, int), 'fee should be an integer.'
        assert isinstance(cache_lifetime, int), 'cache_lifetime should be an' \
               + ' integer.'

    def _get_rate(self):
        if self._cache_time is not None:
            now = datetime.now()
            lifetime = timedelta(seconds=self._cache_lifetime)
            if self._cache_time + lifetime > now:
                return
        today = date.today()
        today_str = today.strftime('%m/%d/%Y')
        tomorrow = today + timedelta(days=1)
        firstdate = (tomorrow - timedelta(days=365)).strftime('%m/%d/%Y')
        actualdate = today.strftime('%m-%d-%Y')
        headers = {'User-Agent': _user_agent}
        post_data = {'homCur': self._from_cur, 'forCur': self._for_cur,
                     'fee': str(self._fee), 'rate': '0', 'submit.x': '124',
                     'submit.y': '5', 'date': today_str, 'lastDate': today_str,
                     'firstDate': firstdate, 'actualDate': actualdate}
        req = Request(_visa_url, urlencode(post_data), headers)
        html = None
        with closing(urlopen(req)) as fp:
            html = fp.read()
        assert html is not None, 'No content.'
        rv = _re_rate.search(html)
        assert rv is not None, 'Unable to get the rate from the HTML page.'
        pieces = rv.groupdict()
        assert pieces['from'] == self._from_cur, 'unreliable HTML content.'
        assert pieces['for'] == self._for_cur, 'unreliable HTML content.'
        self._rate_cache = float(pieces['rate'])
        self._cache_time = datetime.now()

    def convert(self, value):
        self._get_rate()
        return float(value) / self._rate_cache

    def reverse_convert(self, value):
        self._get_rate()
        return float(value) * self._rate_cache

    @property
    def rate(self):
        self._get_rate()
        return self._rate_cache

if __name__ == '__main__':
    visa = VisaExchangeRate('USD', 'BRL', 3)
    print visa.convert(200)
    print visa.reverse_convert(500)
