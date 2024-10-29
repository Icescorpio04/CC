import hashlib

class Packet:
    """Represent a packet of data.
    Note - DO NOT REMOVE or CHANGE the data attribute!
    The simulation assumes this is present!"""

    def __init__(self, binary_data, seq_num):
        """Initialize the packet with data and sequence number."""
        self.data = binary_data  
        self.seq = seq_num       
        self.ack = False        
        self.checksum = self.compute_checksum()  

    def compute_checksum(self):
        """Compute a simple checksum for the packet (used for corruption simulation)."""
        data_string = f'{self.seq}{self.data.decode("utf-8", errors="ignore")}'
        return hashlib.sha256(data_string.encode()).hexdigest()

    def is_corrupted(self):
        """Check if the packet is corrupted by comparing checksums."""
        return self.compute_checksum() != self.checksum

    def make_ack(self):
        """Mark this packet as an acknowledgment packet without changing the data attribute."""
        self.ack = True
        self.checksum = self.compute_checksum()

    def __str__(self):
        """String representation of the packet."""
        if self.ack:
            return f"ACK Packet (Seq: {self.seq}, Checksum: {self.checksum})"
        else:
            return f"Data Packet (Seq: {self.seq}, Data: {self.data}, Checksum: {self.checksum})"
