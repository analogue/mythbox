from unittest2 import TestCase
from mythbox.mythtv.protocol import Protocol40


class Protocol40Test(TestCase):
        
    def test_decodeLongLong(self):
        p = Protocol40()
        self.assertEquals(0, p.decodeLongLong(0, 0))
        self.assertEquals(1, p.decodeLongLong(1, 0))
        self.assertEquals(0xffffffff00000001, p.decodeLongLong(1, 0xffffffff))
        self.assertEquals(0x00000000ffffffff, p.decodeLongLong(0xffffffff, 0x0))
        self.assertEquals(0xffffffff00000000, p.decodeLongLong(0x0, 0xffffffff))
        self.assertEquals(0xffffffffffffffff, p.decodeLongLong(0xffffffff, 0xffffffff))
    
    def test_encodeLongLong(self):
        p = Protocol40()
        lowWord, highWord = p.encodeLongLong(0L)
        self.assertEquals(0, lowWord)
        self.assertEquals(0, highWord)

        lowWord, highWord = p.encodeLongLong(1L)
        self.assertEquals(1, lowWord)
        self.assertEquals(0, highWord)
        
        lowWord, highWord = p.encodeLongLong(0xffffffff00000001)
        self.assertEquals(1, lowWord)
        self.assertEquals(0xffffffff, highWord)

        lowWord, highWord = p.encodeLongLong(0x00000000ffffffff)
        self.assertEquals(0xffffffff, lowWord)
        self.assertEquals(0x0, highWord)

        lowWord, highWord = p.encodeLongLong(0xffffffffffffffff)
        self.assertEquals(0xffffffff, lowWord)
        self.assertEquals(0xffffffff, highWord)
