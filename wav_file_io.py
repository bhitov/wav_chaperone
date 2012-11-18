import optparse
import os
import time, datetime

__author__ = 'ben'

from twisted.internet import reactor, protocol

from twisted.protocols import basic
from twisted.protocols.policies import TimeoutMixin
import wave

from common import display_message #, validate_file_md5_hash, get_file_md5_hash, read_bytes_from_file, clean_and_split_input
def dt2unix():
    dt = datetime.datetime.now()
    return str(time.mktime(dt.timetuple()) + (dt.microsecond / 100 ** 6))

class WavReceiveProtocol(basic.LineReceiver, TimeoutMixin):
    delimiter = '\n'

    def connectionMade(self):
        self.factory.clients.append(self)
        self.file_handler = None
        self.file_data = ()
        self.file_contents = ''
        self.setTimeout(10)

        display_message('Connection from: %s (%d clients total)' % (self.transport.getPeer().host, len(self.factory.clients)))

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        if self.file_handler is not None:
            self.file_handler.close()
            self.file_handler = None
        #self.file_handler = None
        self.file_data = ()

        f = wave.open('stuff/m_%s.wav' % dt2unix(), 'wb')
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)

        f.writeframes(self.file_contents)
        f.close()

        self.file_contents = ''

        display_message('Connection from %s lost (%d clients left)' % (self.transport.getPeer().host, len(self.factory.clients)))

    def timeoutConnection(self):
        display_message("Connection timeout")
        self.transport.loseConnection()

    def lineReceived(self, line):
        display_message('Received the following line from the client [%s]: %s' % (self.transport.getPeer().host, line))
        self.file_data = ("derpy.wav",)
        self.setRawMode()

    def rawDataReceived(self, data):
        self.resetTimeout()
        #self.file_contents += data
        #filename = self.file_data[0]
        #file_path = os.path.join(self.factory.files_path, filename)

        display_message('Receiving file chunk (%d KB)' % (len(data)))

        #if not self.file_handler:
        #    self.file_handler = open(file_path, 'wb')

        if data.endswith('\r\n'):
            # Last chunk
            data = data[:-2]
            self.file_contents += data
            self.setLineMode()

            #self.file_handler.close()
            #self.file_handler = None

        else:
            self.file_contents += data
            #self.file_handler.write(data)

    def _cleanAndSplitInput(self, input):
        input = input.strip()
        input = input.split(' ')

        return input

class WavReceiveServerFactory(protocol.ServerFactory):

    protocol = WavReceiveProtocol

    def __init__(self, files_path):
        self.files_path = files_path

        self.clients = []
        self.files = None

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-p', '--port', action = 'store', type = 'int', dest = 'port', default = 1234, help = 'server listening port')
    parser.add_option('--path', action = 'store', type = 'string', dest = 'path', help = 'directory where the incoming files are saved')
    (options, args) = parser.parse_args()

    display_message('Listening on port %d, serving files from directory: %s' % (options.port, options.path))

    reactor.listenTCP(options.port, WavReceiveServerFactory(options.path))
    reactor.run()
