# This code and all components (c) Copyright 2019-2020, Wowza Media Systems, LLC. All rights reserved.
# This code is licensed pursuant to the BSD 3-Clause License.

APP_VERSION = '2.0.7'

import hashlib
import hmac
import optparse
import sys
import time


class TokenError(Exception):
    def __init__(self, text):
        self._text = text

    def __str__(self):
        return ':%s' % self._text

    def _getText(self):
        return str(self)
    text = property(_getText, None, None,
        'Formatted error text.')

class TokenConfig:
    def __init__(self):
        self.vod_stream_id = ''
        self.ip = ''
        self.start_time = None
        self.end_time = None
        self.lifetime = None
        self.secret = ''
        self.stream_id = ''

class Token:
    def __init__(self, vod_stream_id=None, ip=None, start_time=None, end_time=None,
            lifetime=None, secret=None, stream_id=None):
        self._vod_stream_id = vod_stream_id
        self._ip = ip
        self._start_time = start_time
        self._end_time = end_time
        self._lifetime = lifetime
        self._secret = secret
        self._stream_id = stream_id

    def generateToken(self):

        if self._secret is None or len(self._secret) <= 0:
            raise TokenError('You must provide a secret.')

        if self._stream_id is None:
            raise TokenError('You must provide a stream ID.')

        if str(self._start_time).lower() == 'now':
            self._start_time = int(time.time())
        elif self._start_time is not None:
            try:
                self._start_time = int(self._start_time)
            except:
                raise TokenError('start_time must be numeric or \'now\'')

        if self._end_time is not None:
            try:
                self._end_time = int(self._end_time)
            except:
                raise TokenError('end_time must be numeric.')

        if self._lifetime is not None:
            try:
                self._lifetime = int(self._lifetime)
            except:
                raise TokenError('lifetime must be numeric.')

        if self._end_time is not None:
            if self._start_time is not None and self._start_time >= self._end_time:
                raise TokenError('Token start time is equal to or after expiration time.')
        else:
            if self._lifetime is not None:
                if self._start_time is None:
                    self._end_time = time.time() + self._lifetime
                else:
                    self._end_time = self._start_time + self._lifetime
            else:
                raise TokenError('You must provide an expiration time '
                    '--end_time or a lifetime --lifetime.')

        hash_source = ''
        new_token = ''
        if self._vod_stream_id is not None:
            new_token += 'vod=%s~' % (self._vod_stream_id)

        if self._ip is not None:
            new_token += 'ip=%s~' % (self._ip)

        if self._start_time is not None:
            new_token += 'st=%d~' % (self._start_time)

        new_token += 'exp=%d' % (self._end_time)

        hash_source += new_token
        hash_source += '~stream_id=%s' % (self._stream_id)

        token_hmac = hmac.new(
            self._secret,
            hash_source,
            getattr(hashlib, 'sha256')).hexdigest()

        return 'hdnts=%s~hmac=%s' % (new_token, token_hmac)

if __name__ == '__main__':
    usage = 'gen_token: A short script to generate valid authentication tokens for\n'\
  'Fastly stream targets in Wowza Streaming Cloud.\n\n'\
  'To access to a protected stream target, requests must provide\n'\
  'a parameter block generated by this script, otherwise the request\n'\
  'will be blocked.\n\n'\
  'Any token is tied to a specific stream id and has a limited lifetime.\n'\
  'Optionally, additional parameters can be factored in, for example the\n'\
  'client\'s IP address, or a start time denoting from when on the token is valid.\n'\
  'See below for supported values. Keep in mind that the stream target\n'\
  'configuration has to match these optional parameters in some cases.\n\n'\
  'Examples:\n\n'\
  '# Generate a token that is valid for 1 hour (3600 seconds)\n'\
  '# and protects the stream id YourStreamId with a secret value of\n'\
  '# demosecret123abc\n'\
  './gen_token.py -l 3600 -u YourStreamId -k demosecret123abc\n'\
  'hdnts=exp=1579792240~hmac=efe1cef703a1951c7e01e49257ae33487adcf80ec91db2d264130fbe0daeb7ed\n\n'\
  '# Generate a token that is valid from 1578935505 to 1578935593\n'\
  '# seconds after 1970-01-01 00:00 UTC (Unix epoch time)\n'\
  './gen_token.py -s 1578935505 -e 1578935593 -u YourStreamId -k demosecret123abc\n'\
  'hdnts=st=1578935505~exp=1578935593~hmac=aaf01da130e5554eeb74159e9794c58748bc9f6b5706593775011964612b6d99\n'
    parser = optparse.OptionParser(usage=usage, version=APP_VERSION)
    parser.add_option(
        '-l', '--lifetime',
        action='store', type='string', dest='lifetime',
        help='Token expires after SECONDS. --lifetime or --end_time is mandatory.')
    parser.add_option(
        '-e', '--end_time',
        action='store', type='string', dest='end_time',
        help='Token expiration in Unix Epoch seconds. --end_time overrides --lifetime.')
    parser.add_option(
        '-u', '--stream_id',
        action='store', type='string', dest='stream_id',
        help='STREAMID to validate the token against.')
    parser.add_option(
        '-k', '--key',
        action='store', type='string', dest='secret',
        help='Secret required to generate the token. Do not share this secret.')
    parser.add_option(
        '-s', '--start_time',
        action='store', type='string', dest='start_time',
        help='(Optional) Start time in Unix Epoch seconds. Use \'now\' for the current time.')
    parser.add_option(
        '-i', '--ip',
        action='store', type='string', dest='ip_address',
        help='(Optional) The token is only valid for this IP Address.')
    parser.add_option(
        '-v', '--vod',
        action='store', type='string', dest='vod_stream_id',
        help='(Optional) The token is only valid for this VOD Stream.')
    (options, args) = parser.parse_args()
    try:
        generator = Token(
            options.vod_stream_id,
            options.ip_address,
            options.start_time,
            options.end_time,
            options.lifetime,
            options.secret,
            options.stream_id)

        new_token = generator.generateToken()
        print('%s' % new_token)
    except TokenError, ex:
        print('%s\n' % ex)
        sys.exit(1)
    except Exception, ex:
        print(str(ex))
        sys.exit(1)
