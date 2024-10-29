from threading import Timer
from packet import Packet

class TransportLayer:
    def __init__(self):
        self.timer = None
        self.logger = None
        self.network_layer = None
        self.timeout = 0.4  # Timeout for retransmissions
        self.window_size = 4  # GBN window size
        self.sent_packets = {}  # Store sent but not yet acknowledged packets
        self.seq_num = 0  # The next sequence number to send
        self.acknowledged = 0  # Last acknowledged packet number (window base)

    def with_logger(self, logger):
        self.logger = logger
        return self

    def register_above(self, layer):
        self.application_layer = layer

    def register_below(self, layer):
        self.network_layer = layer

    def from_app(self, binary_data):
        """Receive data from the application layer and send it as packets."""
        if self.seq_num < self.acknowledged + self.window_size:
            packet = Packet(binary_data, self.seq_num)  
            self.sent_packets[self.seq_num] = packet  
            self.network_layer.send(packet) 
            self.logger.info(f"Packet {self.seq_num} sent: {packet}")

            if self.seq_num == self.acknowledged:
                self.start_timer()

            self.seq_num += 1  
        else:
            self.logger.info(f"Window is full. Waiting for ACKs before sending more packets.")

    def from_network(self, packet):
        """Handle packets received from the network layer."""
        if packet.is_corrupted():  
            self.logger.warning(f"Packet {packet.seq} is corrupted, ignored.")
            return  
        if packet.ack:  
            if packet.seq >= self.acknowledged:  
                self.logger.info(f"ACK {packet.seq} received")
                self.acknowledged = packet.seq + 1  
                self.logger.info(f"Window moved forward. New base: {self.acknowledged}")

                if self.acknowledged == self.seq_num:
                    self.logger.info("All packets acknowledged. Stopping timer.")
                    self.stop_timer()
                else:
                    self.reset_timer(self.restransmit_window)

            else:
                self.logger.info(f"Duplicate ACK or out-of-order ACK for {packet.seq}, ignoring")

        else:
            self.application_layer.receive_from_transport(packet.data)
            self.logger.info(f"Data packet {packet.seq} received: {packet}")
            ack_packet = Packet(b'', packet.seq)  
            ack_packet.make_ack()  
            self.network_layer.send(ack_packet)
            self.logger.info(f"ACK {ack_packet.seq} sent back")

    def start_timer(self):
        self.logger.info("Starting timer")
        self.reset_timer(self.restransmit_window)

    def stop_timer(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None  
            self.logger.info("Timer stopped")

    def restransmit_window(self):
        if self.acknowledged == self.seq_num:
            self.logger.info("All packets have been acknowledged. Stopping retransmission.")
            self.stop_timer()
            return

        self.logger.warning(f"Timeout: retransmitting packets from {self.acknowledged}")

        for seq in range(self.acknowledged, min(self.seq_num, self.acknowledged + self.window_size)):
            if seq in self.sent_packets:
                packet = self.sent_packets[seq]
                self.network_layer.send(packet)  
                self.logger.info(f"Packet {seq} retransmitted: {packet}")

        self.start_timer()

    def reset_timer(self, callback, *args):
        if self.timer:
            if self.timer.is_alive():
                self.timer.cancel()
        self.timer = Timer(self.timeout, callback, *args)
        self.timer.start()
