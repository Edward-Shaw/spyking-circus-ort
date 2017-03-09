import json
import zmq

from circusort.base import utils
from circusort.base.proxy import Proxy



class Process(object):
    '''TODO add docstring'''

    def __init__(self, address, log_address):

        object.__init__(self)

        if log_address is None:
            raise NotImplementedError()
            # TODO remove
        self.logger = utils.get_log(log_address, name=__name__)

        # TODO find proper space to define following class
        class Encoder(json.JSONEncoder):

            def default(self, obj):
                if obj is None:
                    obj = json.JSONEncoder.default(obj)
                else:
                    if isinstance(obj, Proxy):
                        obj = obj.encode()
                    else:
                        raise TypeError("Type {t} is not serializable.".format(t=type(obj)))
                return obj

        self.encoder = Encoder

        self.context = zmq.Context()
        # TODO connect tmp socket
        self.logger.debug("connect tmp socket at {a}".format(a=address))
        socket = self.context.socket(zmq.PAIR)
        socket.connect(address)
        # TODO bind rpc socket
        transport = 'tcp'
        host = '127.0.0.1'
        port = '*'
        endpoint = '{h}:{p}'.format(h=host, p=port)
        address = '{t}://{e}'.format(t=transport, e=endpoint)
        self.logger.debug("bind rpc socket at {a}".format(a=address))
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.socket.bind(address)
        self.address = self.socket.getsockopt(zmq.LAST_ENDPOINT)
        self.logger.debug("rpc socket binded at {a}".format(a=self.address))
        # TODO send rpc address
        self.logger.debug("send back rpc address")
        message = {
            'address': self.address,
        }
        socket.send_json(message)

        self.last_obj_id = -1
        self.objs = {}

    def run(self):
        '''TODO add docstring'''

        self.logger.debug("run process")

        while True:
            message = self.receive()
            self.process(message)

        return

    def unwrap_proxy(self, proxy):
        '''TODO add docstring'''

        self.logger.debug("unwrap proxy")

        obj_id = proxy.obj_id
        obj = self.objs[obj_id]

        for attr in proxy.attributes:
            obj = getattr(obj, attr)

        self.logger.debug(dir(obj))

        return obj

    def decode(self, dct):
        '''TODO add docstring'''

        self.logger.debug("decode")

        if isinstance(dct, dict):
            # TODO retrieve obj_type
            obj_type = dct.get('__type__', None)
            if obj_type is None:
                return dct
            elif obj_type == 'proxy':
                # TODO check if correct
                self.logger.debug("dct: {d}".format(d=dct))
                dct['attributes'] = tuple(dct['attributes'])
                dct['process'] = self
                proxy = Proxy(**dct)
                self.logger.debug("proxy address {a}".format(a=proxy.address))
                if self.address == proxy.address:
                    return self.unwrap_proxy(proxy)
                else:
                    return proxy
            else:
                self.logger.debug("unknown object type {t}".format(t=obj_type))
                raise NotImplementedError()
        else:
            self.logger.debug("invalid type {t}".format(t=type(dct)))
            raise NotImplementedError()

    def loads(self, options):
        '''TODO add docstring'''

        self.logger.debug("loads")

        options = json.loads(options.decode(), object_hook=self.decode)

        return options

    def receive(self):
        '''TODO add docstring'''

        self.logger.debug("receive message")

        request_id, request, serialization_type, options = self.socket.recv_multipart()

        request_id = int(request_id.decode())
        request = request.decode()
        serialization_type = serialization_type.decode()
        if options == b'':
            options = None
        else:
            options = self.loads(options)

        message = {
            'request_id': request_id,
            'request': request.decode(),
            'serialization_type': serialization_type.decode(),
            'options': options,
        }

        return message

    def new_object_identifier(self):
        '''TODO add docstring'''

        obj_id = self.last_obj_id + 1
        self.last_obj_id +=1

        return obj_id

    def wrap_proxy(self, obj):
        '''TODO add docstring'''

        self.logger.debug("wrap proxy")

        for t in [type(None), str, int, float, tuple, list, dict, Proxy]:
            if isinstance(obj, t):
                proxy = obj
                return proxy

        obj_id = self.new_object_identifier()
        ref_id = 0 # TODO correct
        obj_type = str(type(obj))
        proxy = Proxy(self.address, obj_id, ref_id, obj_type)

        self.objs[obj_id] = obj

        return proxy

    def process(self, message):
        '''TODO add docstring'''

        self.logger.debug("process message")

        request_id = message['request_id']
        request = message['request']
        options = message['options']

        # TODO invoke requested action
        if request == 'get_module':
            self.logger.debug("request of module")
            name = options['name']
            parts = name.split('.')
            result = __import__(parts[0])
            for part in parts[1:]:
                result = getattr(result, part)
        elif request == 'call_obj':
            self.logger.debug("request of object call")
            obj = options['obj']
            args = options['args']
            kwds = options['kwds']
            self.logger.debug("obj: {o}".format(o=obj))
            result = obj(*args, **kwds)
        else:
            self.logger.debug("unknown request {r}".format(r=request))
            raise NotImplementedError()
            # TODO correct

        result = self.wrap_proxy(result)

        # TODO send result or exception back to proxy
        message = {
            'response': 'return',
            'request_id': request_id,
            'serialization_type': 'json',
            'result': result,
            'exception': None,
        }
        message = self.dumps(message)
        self.socket.send_multipart([message])

        return

    # def dumps(self, message):
    #     '''TODO add docstring'''
    #
    #     dumped_response = str(message['response']).encode()
    #     dumped_request_id = str(message['request_id']).encode()
    #     dumped_serialization_type = str('json').encode()
    #     if message['result'] is None:
    #         dumped_result = b""
    #     else:
    #         dumped_result = json.dumps(message['result'], cls=self.encoder).encode()
    #     if message['exception'] is None:
    #         dumped_exception = b""
    #     else:
    #         raise NotImplementedError()
    #
    #     message = [
    #         dumped_response,
    #         dumped_request_id,
    #         dumped_serialization_type,
    #         dumped_result,
    #         dumped_exception,
    #     ]
    #
    #     return message

    def dumps(self, obj):
        '''TODO add docstring'''

        self.logger.debug("dumps")

        dumped_obj = json.dumps(obj, cls=self.encoder)
        message = dumped_obj.encode()

        self.logger.debug("message: {m}".format(m=message))

        return message


def main(args):

    address = args['address']
    log_address = args['log_address']

    process = Process(address, log_address=log_address)
    process.run()

    return
