from src.Stream import Stream
from src.Packet import Packet, PacketFactory
from src.UserInterface import UserInterface
import time
import random
import threading


class Peer:
    def __init__(self, server_ip, server_port, is_root=False, root_address=None):
        self._is_root = is_root

        self.stream = Stream(server_ip, server_port)

        self.parent = None

        self.packets = []
        self.neighbours = []

        self._user_interface = UserInterface()

        self._broadcast_packets = []

        self.packet_factory = PacketFactory()

        if self._is_root:
            self.network_nodes = []
            self.network_Graph = NetworkGraph(GraphNode((server_ip, server_port)))
        else:
            self.root_address = root_address
            self.stream.add_node(root_address, set_register_connection=True)

        pass

    def start_user_interface(self):
        # Which the user or client sees and works with. run() #This method runs every time to
        #  see whether there is new messages or not.
        #   TODO
        print("Starting UI")
        self._user_interface.start()

        pass

    def handle_user_interface_buffer(self):
        """
        Only handle broadcast messages
        :return:
        """

        # print("user interface handler ", self._user_interface.buffer)
        for buffer in self._user_interface.buffer:
            if len(buffer) == 0:
                continue

            print("User interface handler buffer: ", buffer)

            if buffer[0] == '1':
                print("Handling buffer/1 in UI")
                self.stream.add_message_to_out_buff(self.root_address,
                                                    self.packet_factory.new_register_packet("REQ",
                                                                                            self.stream.get_server_address(),
                                                                                            self.root_address).get_buf())
            elif buffer[0] == '2':
                print("Handling buffer/2 in UI")
                self.stream.add_message_to_out_buff(self.root_address,
                                                    self.packet_factory.new_advertise_packet("REQ",
                                                                                             self.stream.get_server_address()).get_buf())

            elif buffer[0] == '4':
                print("Handling buffer/4 in UI")
                self.send_broadcast_packet(self.packet_factory.new_message_packet(buffer,
                                                                                      self.stream.get_server_address()).get_buf())
        self._user_interface.buffer = []

    def run(self):
        """
        Main loop of the program.
        The actions that should be done in this function listed below:

            1.Parse server in_buf of the stream.
            2.Handle all packets were received from server.
            3.Parse user_interface_buffer to make message packets.
            4.Send packets stored in nodes buffer of stream.
            5.** sleep for some milliseconds **

        :return:
        """

        print("Running the peer...")
        while True:
            for b in self.stream.read_in_buf():
                # print("In main while: ", b)
                p = self.packet_factory.parse_buffer(b)
                self.handle_packet(p)
                # self.packets.remove(p)
            self.stream.clear_in_buff()

            self.handle_user_interface_buffer()
            # print("Main while before user_interface handler")
            # self.send_broadcast_packets()
            self.stream.send_out_buf_messages()

            time.sleep(2)

    def send_broadcast_packet(self, broadcast_packet):
        """
        For setting broadcast packets buffer into Nodes out_buff.
        :return:
        """

        for n in self.stream.nodes:
            # print(n.get_standard_server_address())
            # print(self.root_address)
            # if n.get_standard_server_address() != self.root_address:
            if not n.is_register_connection:
                self.stream.add_message_to_out_buff(n.get_server_address(), broadcast_packet)

    def handle_packet(self, packet):
        """

        In this function we will use the other handle_###_packet methods to handle the 'packet'.

        :param packet: The arrived packet that should be handled.

        :type packet Packet

        """
        if packet.get_length() != len(packet.get_body()):
            print("packet.get_length() = ", packet.get_length(), "  , packet.get_body() = ", len(packet.get_body()))
            raise Exception("Packet Length is incorrect.")
        print("Handling the packet...")
        if packet.get_version() == 1:
            print("Packet version:\t1")
            if packet.get_type() == 1:
                self.__handle_register_packet(packet)
            elif packet.get_type() == 2:
                print("Packet type:\t2")
                self.__handle_advertise_packet(packet)
            elif packet.get_type() == 3:
                print("Packet type:\t3")
                self.__handle_join_packet(packet)
            elif packet.get_type() == 4:
                print("Packet type:\t4")
                self.__handle_message_packet(packet)
            elif packet.get_type() == 5:
                print("Packet type:\t5")
                self.__handle_reunion_packet(packet)
            else:
                print("Unexpected type:\t", packet.get_type())
                # self.packets.remove(packet)

    def __check_registered(self, source_address):

        for n in self.network_nodes:
            if n.get_address() == source_address:
                return True
        return False

    def __handle_advertise_packet(self, packet):
        """
        For advertising peers in network, It is peer discovery message.

        Request:
            We should act as root of the network and reply with a neighbour address in a new Advertise Response packet.

        Response:
            When a Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
            new parent.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """
        print("Handling advertisement packet...")

        flag = False
        if packet.get_body()[0:3] == "REQ":
            print("Packet is in Request type")

            if not self.__check_registered(packet.get_source_server_address()):
                print(packet.get_source_server_address(), " trying to advertise before registering.")
                return

            #TODO Here we should check that is the node was advertised in past then update our GraphNode

            neighbor = self.__get_neighbour(packet.get_source_server_address())
            p = self.packet_factory.new_advertise_packet(type="RES",
                                                         source_server_address=self.stream.get_server_address(),
                                                         neighbor=neighbor)
            server_address = packet.get_source_server_address()
            # self.network_Graph.add_node(server_address[0], server_address[1], neighbor)
            self.stream.add_message_to_out_buff(packet.get_source_server_address(), p.get_buf())

        elif packet.get_body()[0:3] == "RES":
            print("Packet is in Response type")
            server_ip = packet.get_source_server_ip()
            server_port = packet.get_source_server_port()
            self.stream.add_node((packet.get_body()[3:18], packet.get_body()[18:23]))
            if self.parent:
                self.stream.remove_node(self.parent)
            self.parent = self.stream.get_node_by_server(packet.get_body()[3:18], packet.get_body()[18:23])

            addr = self.stream.get_server_address()
            join_packet = self.packet_factory.new_join_packet(addr)
            self.stream.add_message_to_out_buff(self.parent.get_server_address(), join_packet.get_buf())
        else:
            raise Exception("Unexpected Type.")

    def __handle_register_packet(self, packet):
        """
        For registration a new node to the network at first we should make a Node object for 'sender' and save it in
        nodes array.

        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """
        print("Handling register packet body: ", packet.get_body())
        pbody = packet.get_body()
        if pbody[0:3] == "REQ":
            print("Packet is in Request type")
            if not self._is_root:
                raise Exception("Register request packet send to a non root node!")
            else:

                if self.__check_registered(packet.get_source_server_address()):
                    print(packet.get_source_server_address(), " trying to register again")
                    return

                res = self.packet_factory.new_register_packet(type="RES",
                                                              source_server_address=self.stream.get_server_address(),
                                                              address=self.stream.get_server_address())
                self.network_nodes.append(SemiNode(pbody[3:18], pbody[18:23]))
                self.stream.add_node((packet.get_source_server_ip(), packet.get_source_server_port()),
                                     set_register_connection=True)
                # self.stream.add_client(pbody[3:18], pbody[18:23])
                self.stream.add_message_to_out_buff(packet.get_source_server_address(), res.get_buf())
                # self.stream.add_message_to_out_buf((pbody[3:18], pbody[18:23]), res)
                #   TODO    Maybe in other time we should delete this node from our clients array.

        if pbody[0:3] == "RES":
            print("Packet is in Response type")
            if pbody[3:6] == "ACK":
                print("ACK! Registered accomplished")
            else:
                raise Exception("Root did not send ack in the register response packet!")

    def __check_neighbour(self, address):
        if address in self.neighbours == address:
            return True
        return False

    def __handle_message_packet(self, packet):
        """
        For now only broadcast message to the other nodes.
        Do not forget to ignore messages from unknown sources.

        :param packet:

        :type packet Packet

        :return:
        """
        print("Handling message packet...")
        print("The message was just arrived is: ", packet.get_body(), " and source of the packet is: ",
              packet.get_source_server_address())
        new_packet = self.packet_factory.new_message_packet(packet.get_body(), self.stream.get_server_address())
        # for n in self.stream.nodes:
        #     print("From here:\t", n.get_server_address(), " ", n.is_register_connection)

        # if not self.__check_neighbour(packet.get_source_server_address()):
        #     print("The message is from an unknown source.")
        #     return

        for n in self.stream.nodes:
            if not n.is_register_connection:
                if n.get_server_address() != packet.get_source_server_address():
                    print("Node considered to send message to: ", n.get_server_address())
                    self.stream.add_message_to_out_buff(n.get_server_address(), new_packet.get_buf())

        # if self.parent and self.parent.get_server_address() != packet.get_source_server_address():
        #     print("Node considered to send message to: ", self.parent.get_server_address())
        #     self.stream.add_message_to_out_buff(self.parent.get_server_address(), new_packet.get_buf())

    def __handle_reunion_packet(self, packet):
        """
        #TODO   @Ali complete doc please. :\

        :param packet:
        :return:
        """
        print("Handling reunion packet")
        if packet.get_body()[0:3] == "REQ":
            print("Packet is in Request type")
            if self._is_root:
                number_of_entity = int(packet.get_body()[0:2])
                node_array = []
                ip_and_ports = packet.get_body()[2:]
                sender_ip = ip_and_ports[(number_of_entity - 1) * 20: (number_of_entity - 1) * 20 + 15]
                sender_port = ip_and_ports[(number_of_entity - 1) * 20 + 15: (number_of_entity - 1) * 20 + 20]
                for i in range(number_of_entity):
                    ip = ip_and_ports[i * 20:i * 20 + 15]
                    port = ip_and_ports[i * 20 + 15:i * 21]
                    node_array.insert(0, (ip, port))
                self.network_Graph.turn_on_node(packet.get_source_server_address())
                p = self.packet_factory.new_reunion_packet(type='RES', source_address=self.root_address,
                                                           nodes_array=node_array)
                self.stream.add_message_to_out_buff((sender_ip, sender_port), p.get_buf())
            else:
                number_of_entity = int(packet.get_body()[0:2])
                node_array = []
                ip_and_ports = packet.get_body()[2:]
                for i in range(number_of_entity):
                    ip = ip_and_ports[i * 20:i * 20 + 15]
                    port = ip_and_ports[i * 20 + 15:i * 21]
                    node_array.append((ip, port))
                node_array.append((self.stream.ip, self.stream.port))

                p = self.packet_factory.new_reunion_packet(type='REQ',
                                                           source_address=packet.get_source_server_address(),
                                                           nodes_array=node_array)
                self.stream.add_message_to_out_buff((self.parent.get_ip(), self.parent.get_port()), p.get_buf())
        elif packet.get_body()[0:3] == "RES":
            print("Packet is in Response type")
            number_of_entity = int(packet.get_body()[0:2])
            node_array = []
            ip_and_ports = packet.get_body()[2:]
            first_ip = ip_and_ports[0:15]
            first_port = ip_and_ports[15:20]
            sender_ip = ip_and_ports[20:35]
            sender_port = ip_and_ports[35:40]
            if first_ip == self.stream.ip and first_port == self.stream.port:
                for i in range(number_of_entity - 1):
                    ip = ip_and_ports[i * 20:i * 20 + 15]
                    port = ip_and_ports[i * 20 + 15:i * 21]
                    node_array.append((ip, port))
                p = self.packet_factory.new_reunion_packet(type='RES',
                                                           source_address=packet.get_source_server_address(),
                                                           nodes_array=node_array)
                self.stream.add_message_to_out_buff((sender_ip, sender_port), p.get_buf())
            else:
                raise Exception("Unexpected Ip or Port in Reunion's body")
        else:
            raise Exception("Unexpected type")

    def __handle_join_packet(self, packet):
        """
        When a Join packet received we should add new node to our nodes array.
        In future we should add a security level for this section to forbid joining without permission of network root.

        :param packet: Arrived register packet.
                       Latter we will use this for security.


        :type packet Packet

        :return:
        """
        print("Handling join packet...")
        self.neighbours.append(packet.get_source_server_address())
        self.stream.add_node(packet.get_source_server_address())

        pass

    def __get_neighbour(self, sender):
        """
        Finds the best neighbour for the 'sender' from network_nodes array.

        :param sender: Sender of the packet
        :return: The specified neighbor for the sender; The format is like ('192.168.001.001', '05335').
        """

        valid_nodes = []
        for s in self.network_nodes:
            if s.get_address() != sender:
                valid_nodes.append(s)

        if len(valid_nodes) >= 1:
            return random.choice(valid_nodes).get_address()

        else:
            return self.stream.get_server_address()

        #   TODO @Ali it's your version, please fix this
        # return self.network_Graph.find_live_node().address


class SemiNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def get_ip(self):
        return self.ip

    def get_port(self):
        return self.port

    def get_address(self):
        return SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)

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


class GraphNode:
    def __init__(self, address):
        """

        :param address: (ip, port)
        :type address: tuple

        """
        self.parent = None
        self.children = []
        self.ip = address[0]
        self.port = address[1]
        self.address = address
        self.alive = False

    def set_parent(self, parent):
        self.parent = parent

    def set_address(self, new_address):
        self.address = new_address

    def __reset(self):
        self.parent = None
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class NetworkGraph:
    def __init__(self, root):
        self.root = root
        root.alive = True
        self.nodes = [root]

    def find_live_node(self):
        queue = [self.root]
        while len(queue) > 0:
            node = queue[0]
            number_of_live_children = 0
            for child in node.childre:
                if child.alive:
                    number_of_live_children += 1
                    queue.append(child)
            if number_of_live_children < 2:
                return node
            queue.pop(0)
        return self.root

    def find_node(self, ip, port):
        for node in self.nodes:
            if node.ip == ip and node.port == port:
                return node
        return None

    def turn_on_node(self, node_address):
        node = self.find_node(node_address[0], node_address[1])
        if node is not None:
            node.alive = True

    def turn_of_node(self, node_address):
        node = self.find_node(node_address[0], node_address[1])
        if node is not None:
            node.alive = False

    def remove_node(self, node_address):
        node = self.find_node(node_address[0], node_address[1])
        if node is not None:
            self.nodes.remove(node)

    def add_node(self, ip, port, father_address):
        father_node = self.find_node(father_address[0], father_address[1])
        new_node = self.find_node(ip, port)

        if new_node is None:
            new_node = GraphNode((ip, port))
            self.nodes.append(new_node)
        new_node.set_parent(father_node)
        father_node.add_child(new_node)
