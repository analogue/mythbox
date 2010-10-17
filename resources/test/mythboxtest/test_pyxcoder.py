#
#  MythBox for XBMC - http://mythbox.googlecode.com
#  Copyright (C) 2010 analogue@yahoo.com
# 
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import logging
import unittest
import ffmpeg.metadata

log = logging.getLogger('mythbox.unittest')

class FFMPEGMetadataParserTest(unittest.TestCase):

    def setUp(self):
        self.parser = ffmpeg.metadata.FFMPEGMetadataParser(None)
        self.parser.metadata = ffmpeg.metadata.Metadata()
  
    def test_issue_124_ffmpeg_parsing_failure(self):
        input = 'Stream #0.0[0x800]: Video: mpeg2video, yuv420p, 1920x1080 [PAR 1:1 DAR 16:9], 38810 kb/s, 29.97 fps, 29.97 tbr, 90k tbn, 59.94 tbc'
        self.parser.parse_video_stream(input)
        self.assertEqual('29.97', self.parser.metadata.frame_rate)

    def test_parse_video_line_ota(self):
        input = 'Stream #0.0[0x31]: Video: mpeg2video, yuv420p, 1280x720 [PAR 1:1 DAR 16:9], 65000 kb/s, 59.94 tbr, 90k tbn, 119.88 tbc' 
        self.parser.parse_video_stream(input)
        self.assertEqual('59.94', self.parser.metadata.frame_rate)

    def test_parse_video_line_hdpvr(self):
        input = 'Stream #0.0[0x1011]: Video: h264, yuv420p, 1280x720 [PAR 1:1 DAR 16:9], 59.94 tbr, 90k tbn, 119.88 tbc' 
        self.parser.parse_video_stream(input)
        self.assertEqual('59.94', self.parser.metadata.frame_rate)

    def test_parse_video_line_hdpvr2(self):
        input = 'Stream #0.0[0x1011]: Video: h264, yuv420p, 1280x720, 59.94 fps(r)' 
        self.parser.parse_video_stream(input)
        self.assertEqual('59.94', self.parser.metadata.frame_rate)

    def test_parse_video_line_mpeg2(self):
        input = 'Stream #0.0[0x31]: Video: mpeg2video, yuv420p, 1280x720, 80000 kb/s, 59.94 fps(r)' 
        self.parser.parse_video_stream(input)
        self.assertEqual('59.94', self.parser.metadata.frame_rate)

if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('mythbox_log.ini')
    unittest.main()
