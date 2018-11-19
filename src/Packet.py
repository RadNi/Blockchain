"""

    This is the format of packets in our network:
    
                 ** Packet Format **
     ________________________________________________
    | Version(1 char)| Type(2 char) | Length(5 char) |
    |------------------------------------------------|
    |                      ....                      |
    |                      BODY                      |
    |                      ....                      |
    |________________________________________________|
    
    
    Version:
        For now version is 1
    
    Type:
        01: Register
        02: Advertise
        03: Join
        04: Message
        05: Reunion
                e.g: type = '02' => advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.
        
    
    Packet descriptions:
    
        Register:
            Request:
        
                                ** Packet Format **
                 ________________________________________________
                |                 IP (15 char)                   |
                |------------------------------------------------|
                |                 Port (5 char)                  |
                |________________________________________________|
                
                For sending IP/Port of current node to the root to ask if it can register to network or not.
            Response:
        
                                ** Packet Format **
                 ________________________________________________
                |                       ACK                      |
                |________________________________________________|
                
                For now only should just send an 'Ack' from the root  to inform a node that it 
                has been registered in the root if the 'Register Request' was successful.
                
        Advertise:
            Request:
            
                                ** Packet Format **
                 ________________________________________________
                |                      REQ                       |
                |________________________________________________|
                
                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.
            Response:
        
                                ** Packet Format **
                 ________________________________________________
                |                      RES                       |
                |------------------------------------------------|
                |                 IP (15 char)                   |
                |------------------------------------------------|
                |                 Port (5 char)                  |
                |________________________________________________|
                
                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.
                
        Join:
            
                                ** Packet Format **
                 ________________________________________________
                |                     JOIN                       |
                |________________________________________________|
            
            New node after getting Advertise Response from root must send this packet to specified peer 
            to tell him that they should connect together; When receiving this packet we should update our 
            Client Dictionary in Stream object.
            
            For next version Join packet must contain a field for validation the joining action.
            
        Message:
                                ** Packet Format **
                 ________________________________________________
                |                     Message                    |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.
        
        Reunion:
            Hello:
        
                                ** Packet Format **
                 ________________________________________________
                |                      REQ                       |
                |------------------------------------------------|
                |            Number of Entries(2 char)           |
                |------------------------------------------------|
                |                 IP0 (15 char)                  |
                |------------------------------------------------|
                |                 Port0 (5 char)                 |
                |------------------------------------------------|
                |                 IP1 (15 char)                  |
                |------------------------------------------------|
                |                 Port1 (5 char)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 char)                  |
                |------------------------------------------------|
                |                 PortN (5 char)                 |
                |________________________________________________|
                
                In every intervals (for now 20 seconds) peers must send this message to the root.
                Every other peers that received this packet should append their (ip, port) to 
                the packet and update Length.
            Hello Back:
        
                                ** Packet Format **
                 ________________________________________________
                |                      RES                       |
                |------------------------------------------------|
                |            Number of Entries(2 char)           |
                |------------------------------------------------|
                |                 IPN (15 char)                  |
                |------------------------------------------------|
                |                 PortN (5 char)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 char)                  |
                |------------------------------------------------|
                |                 Port1 (5 char)                 |
                |________________________________________________|

                Root in answer of the Reunion Hello message will send this packet to the target node.
                In this packet all the nodes (ip, port) exist in order by path traversal to target.
            
    
"""


class Packet:

    def __init__(self, buf):
        self.buf = buf
        self.header = buf[0:8]
        self.version = int(buf[0], 10)
        self.type = int(buf[1:3], 10)
        self.length = int(buf[3:8], 10)
        self.body = buf[8:]

    def get_header(self):
        """

        :return: Packet header
        :rtype: str
        """

        return self.header

    def get_version(self):
        """

        :return: Packet Version
        :rtype: int
        """
        return self.version

    def get_type(self):
        """

        :return: Packet type
        :rtype: int
        """
        return self.type

    def get_length(self):
        """

        :return: Packet length
        :rtype: int
        """
        return self.length

    def get_body(self):
        """

        :return: Packet body
        :rtype: str
        """
        return self.body

    def get_buf(self):
        """

        :return Packet buffer
        :return: str
        """
        return self.buf


class PacketFactory:

    def parse_buffer(self, buffer):

        """
        :param buffer: The buffer that should be parse to a validate packet format

        :return new packet
        :rtype Packet

        """
        pass

    def new_reunion_packet(self, destination, nodes_array):
        """
        :param destination: (ip, port) of destination want to send reunion packet.
        :param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

        :return New reunion packet.
        :rtype Packet

        """
        pass

    def new_advertise_packet(self, type, neighbor=None):
        """
        :param type: Type of Advertise packet
        :param neighbor: The neighbor for advertise response packet; The format is like ('192.168.001.001', '05335').

        :type type: str
        :type neighbor: tuple

        :return New advertise packet.
        :rtype Packet

        """
        version = '1'
        packet_type = '02'

        if type == 'Request':
            body = 'REQ'
            length = '00003'
            return Packet(version + packet_type + length + body)

        elif type == 'Response':
            try:
                body = 'RES'
                body += neighbor[0]
                body += neighbor[1]
                length = '00023'
                return Packet(version + packet_type + length + body)
            except Exception as e:
                print(str(e))
        else:
            raise Exception("Type is incorrect")

    def new_join_packet(self):
        """
        :return New join packet.
        :rtype Packet

        """
        version = '1'
        packet_type = '03'
        length = '00004'
        body = 'JOIN'

        return Packet(version + packet_type + length + body)

    def new_register_packet(self):
        # make a new register packet.
        pass
