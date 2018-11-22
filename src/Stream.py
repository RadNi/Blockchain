from src.tools.simpletcp.tcpserver import TCPServer

from src.tools.simpletcp.clientsocket import ClientSocket
import threading


class Node:
    def __init__(self, server_address, set_root=False, set_register=False):
        """

        :param server_address: Nodes server address.
        """

        self.server_ip = Node.parse_ip(server_address[0])
        self.server_port = Node.parse_port(server_address[1])

        print( "                    inja, ", self.server_port)
        print(server_address)

        self.in_buff = []
        self.out_buff = []
        self.is_root = set_root
        self.is_register_connection = set_register

        try:
            self.client = ClientSocket(self.server_ip, int(self.server_port, 10), single_use=False)
        except:
            print("Node was detached.")
            self.out_buff.clear()
            self.in_buff.clear()

    def send_message(self):
        """
        Final function to send buffer to the clients socket.

        :return:
        """
        # print("in sending message: ", self.out_buff)
        for b in self.out_buff:
            print("In sending message buffer: ", b)
            # print(b)
            response = self.client.send(b)
            print("Response: ", response, " ", type(response))
            if response != b'ACK':
                print("The ", self.get_server_address()[0], ": ", self.get_server_address()[1],
                      " did not response with b'ACK'.")

        self.out_buff.clear()

    def add_message_to_out_buff(self, message):
        """
        Here we will add new message to the server out_buff, then in 'send_message' will send them.

        :param message: The message we want to add to out_buff
        :return:
        """
        self.out_buff.append(message)

    def close(self):
        """
        Closing client object.
        :return:
        """
        self.client.close()

    def get_server_address(self):
        """

        :return: Server address in a pretty format.
        :rtype: tuple
        """
        return self.server_ip, self.server_port

    def get_standard_server_address(self):
        """

        :return: Server address in standard format.
        :rtype: tuple
        """

        ip_prime = '.'.join(str(int(part)) for part in self.server_ip.split('.'))
        port_prime = int(self.server_port)

        return self.server_ip, port_prime

    @staticmethod
    def parse_ip(ip):
        """
        Automatically change the input IP format like '192.168.001.001'.
        :param ip: Input IP
        :type ip: str

        :return: Formatted IP
        :rtype: str
        """
        return '.'.join(str(int(part)).zfill(3) for part in ip.split('.'))

    @staticmethod
    def parse_port(port):
        """
        Automatically change the input IP format like '05335'.
        :param port: Input IP
        :type port: str

        :return: Formatted IP
        :rtype: str
        """
        return str(int(port)).zfill(5)


class Stream:

    def __init__(self, ip, port):
        """
        :param ip: 15 characters
        :param port: 5 characters
        """
        if not self.is_valid(ip, port):
            raise Exception("Invalid format of ip or port for TCPServer.")
            #   TODO    Error handling

        self.messages_dic = {}
        self._server_in_buf = []
        # self.parent = None
        #   TODO    Parent should be in Peer object not here

        def cb(ip, queue, data):
            queue.put(bytes('ACK', 'utf8'))
            print("In callback: ", data)
            # self.messages_dic.update({ip: self.messages_dic.get(ip).append(data)})
            self._server_in_buf.append(data)

        print("Binding server: ", ip, ": ", port)
        self._server = TCPServer(ip, port, cb)
        tcpserver_thread = threading.Thread(target=self._server.run)
        # self._server.run()
        tcpserver_thread.start()
        self.nodes = []
        self.ip = ip
        self.port = port

    def get_server_address(self):
        return Node.parse_ip(self._server.ip), Node.parse_port(self._server.port)

    def clear_in_buff(self):
        self._server_in_buf = []

    def add_node(self, server_address, set_root=False, set_register_connection=False):
        # node = None
        # try:
        node = Node(server_address, set_register=set_register_connection)
        # except:
        #     print("Node was detached.")
        #     # self.remove_node()
        # if node is not None:
        self.nodes.append(node)

    def is_valid(self, ip, port):
        if len(str(ip)) != 15 or len(str(port)) > 5:
            return False
        return True

    def remove_node(self, cl):
        self.nodes.remove(cl)
        cl.close()

    def get_node_by_server(self, ip, port):
        """

        :param ip:
        :param port:
        :return:
        :rtype: Node
        """
        port = Node.parse_port(port)
        ip = Node.parse_ip(ip)
        for nd in self.nodes:
            if nd.get_server_address()[0] == ip and nd.get_server_address()[1] == port:
                return nd

    def add_message_to_out_buff(self, address, message):
        print("add message to out buff: ", address, " ", message)
        n = self.get_node_by_server(address[0], address[1])
        # if n is None:
        #     n = self.get_node_by_client(address[0], address[1])
        if n is None:
            raise Exception("Unexpected address to add message to out buffer.")

        n.add_message_to_out_buff(message)

    def remove_node_by_server_info(self, ip, port):
        rem_client = None
        for nd in self.nodes:
            if nd.get_server_address[0] == ip and nd.get_server_address[1] == port:
                rem_client = nd
                break
        if rem_client is not None:
            self.remove_node(rem_client)

    def read_in_buf(self):
        return self._server_in_buf

    def send_messages_to_node(self, node):
        """
        Send buffered messages to the 'node'

        :param node:
        :type node Node

        :return:
        """

        node.send_message()

    def send_out_buf_messages(self):
        """
        In this function we will send hole out buffers to their own clients.

        :return:
        """

        for n in self.nodes:
            self.send_messages_to_node(n)
