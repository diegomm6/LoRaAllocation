import numpy as np
import random
from base import *
from LoRaTransmission import LoRaTransmission

class LoRaNode():

    def __init__(self, id_, minEangle, simTimeslots, timeslot) -> None:

        self.timeslot = timeslot
        self.simTimeslots = simTimeslots

        maxRange = dist2sat_angle(minEangle)
        maxGround_dist = EARTH_R * np.arcsin( maxRange*np.cos(minEangle) / (EARTH_R+SAT_H) )

        self.nodeId = id_
        self.ground_dist = maxGround_dist * np.sqrt(random.uniform(0, 1))
        self.b_angle = random.uniform(0, 2*np.pi)

        self.x = self.ground_dist * np.cos(self.b_angle)
        self.y = self.ground_dist * np.sin(self.b_angle)

        self.TXtime = -self.y / SAT_V
        self.maxE_angle = np.arctan( SAT_H / abs(self.x) )

        doppler_data = doppler(self.maxE_angle, self.TXtime)
        self.doppler_shift = doppler_data[0]  
        self.doppler_rate = doppler_data[1]


    def get_transmissions(self) -> list[LoRaTransmission]:

        sf = random.randrange(7, 13)
        max_packet_duration = int(np.ceil(lora_toa(MAX_PL_LORA[sf-7], sf) / self.timeslot))
        startLimit = self.simTimeslots - max_packet_duration

        startSlot = random.randrange(0, startLimit)
        payload_size = random.randrange(13, 58)
        channel = random.randrange(0, 10)

        duration = int(np.ceil(lora_toa(payload_size, sf) / self.timeslot))

        tx = LoRaTransmission(self.nodeId, self.nodeId, startSlot, payload_size, sf, channel, duration)

        return [tx]
    