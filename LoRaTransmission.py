

class LoRaTransmission():

    def __init__(self, _id: int, node_id: int, startSlot: int,
                 payload_size: int, sf: int, channel: int, duration: int) -> None:

        self._id = _id
        self.node_id = node_id
        self.startSlot = startSlot
        self.payload_size = payload_size
        self.channel = channel
        self.sf = sf
        self.duration = duration
    
    def __lt__(self, other) -> bool:
        return self.startSlot < other.startSlot
    