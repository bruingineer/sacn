# This file is under MIT license. The license file can be obtained in the root directory of this module.

from sacn.messages.data_packet import \
    calculate_multicast_addr, \
    DataPacket


def test_calculate_multicast_addr():
    assert calculate_multicast_addr(1) == "239.255.0.1"
    assert calculate_multicast_addr(63999) == "239.255.249.255"


def test_byte_string_construction_and_deconstruction():
    built_packet = DataPacket(
        cid=(16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8),
        sourceName="Test Name",
        universe=62000,
        dmxData=((255,) + tuple(range(255)) + tuple(range(256, 0, -1))),
        priority=195,
        sequence=34,
        streamTerminated=True,
        previewData=True,
        forceSync=True,
        sync_universe=12000,
        dmxStartCode=12)
    read_packet = DataPacket.make_data_packet(built_packet.getBytes())
    assert built_packet.dmxData == read_packet.dmxData
    assert built_packet == read_packet


def test_property_adjustment_and_deconstruction():
    # Converting DataPacket -> bytes -> DataPacket should produce the same result,
    # but with changed properties that are not the default
    built_packet = DataPacket(
        cid=(16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8),
        sourceName="Test Name",
        universe=30)
    built_packet.cid = tuple(range(16))
    built_packet.sourceName = "2nd Test Name"
    built_packet.universe = 31425
    built_packet.dmxData = ((200,) + tuple(range(255, 0, -1)) + tuple(range(255)) + (0,))
    built_packet.priority = 12
    built_packet.sequence = 45
    built_packet.option_StreamTerminated = True
    built_packet.option_PreviewData = True
    built_packet.option_ForceSync = True
    built_packet.syncAddr = 34003
    built_packet.dmxStartCode = 8
    read_packet = DataPacket.make_data_packet(built_packet.getBytes())
    assert read_packet.cid == tuple(range(16))
    assert read_packet.sourceName == "2nd Test Name"
    assert read_packet.universe == 31425
    assert read_packet.dmxData == ((200,) + tuple(range(255, 0, -1)) + tuple(range(255)) + (0,))
    assert read_packet.priority == 12
    assert read_packet.sequence == 45
    assert read_packet.option_StreamTerminated is True
    assert read_packet.option_PreviewData is True
    assert read_packet.option_ForceSync is True
    assert read_packet.syncAddr == 34003
    assert read_packet.dmxStartCode == 8


def test_sequence_increment():
    # Test that the sequence number can be increased and the wrap around at 255 is correct
    built_packet = DataPacket(
        cid=(16, 1, 15, 2, 14, 3, 13, 4, 12, 5, 11, 6, 10, 7, 9, 8),
        sourceName="Test Name",
        universe=30)
    built_packet.sequence = 78
    built_packet.sequence_increase()
    assert built_packet.sequence == 79
    built_packet.sequence = 255
    built_packet.sequence_increase()
    assert built_packet.sequence == 0


def test_parse_data_packet():
    # Use the example present in the E1.31 spec in appendix B
    raw_data = [
        # preamble
        0x00, 0x01,
        # postamble
        0x00, 0x00,
        # ACN packet identifier
        0x41, 0x53, 0x43, 0x2d, 0x45, 0x31, 0x2e, 0x31, 0x37, 0x00, 0x00, 0x00,
        # flags and length
        0x72, 0x7d,
        # Root vector
        0x00, 0x00, 0x00, 0x04,
        # CID
        0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e,
        # Framing flags and length
        0x72, 0x57,
        # Framing vector
        0x00, 0x00, 0x00, 0x02,
        # Source name "Source_A"
        0x53, 0x6f, 0x75, 0x72, 0x63, 0x65, 0x5f, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        # priority
        0x64,
        # sync address
        0x1f, 0x1a,
        # sequence number
        0x9a,
        # options
        0x00,
        # universe
        0x00, 0x01,
        # DMP flags and length
        0x72, 0x0d,
        # DMP vector
        0x02,
        # address type & data type
        0xa1,
        # first property address
        0x00, 0x00,
        # address increment
        0x00, 0x01,
        # property value count
        0x02, 0x01,
        # DMX start code
        0x00,
    ]
    # DMX data (starting with 0 and incrementing with wrap around at 255)
    dmx_data = [x % 256 for x in range(0, 512)]
    raw_data.extend(dmx_data)

    # parse raw data
    packet = DataPacket.make_data_packet(raw_data)
    assert packet.length == 638
    assert packet._vector == (0x00, 0x00, 0x00, 0x04)
    assert packet.cid == (0xef, 0x07, 0xc8, 0xdd, 0x00, 0x64, 0x44, 0x01, 0xa3, 0xa2, 0x45, 0x9e, 0xf8, 0xe6, 0x14, 0x3e)
    assert packet.sourceName == "Source_A"
    assert packet.priority == 100
    assert packet.syncAddr == 7962
    assert packet.sequence == 154
    assert packet.option_ForceSync is False
    assert packet.option_PreviewData is False
    assert packet.option_StreamTerminated is False
    assert packet.universe == 1
    assert packet.dmxStartCode == 0
    assert packet.dmxData == tuple(dmx_data)