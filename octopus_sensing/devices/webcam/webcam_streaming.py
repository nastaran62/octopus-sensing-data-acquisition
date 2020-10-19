# This file is part of Octopus Sensing <https://octopus-sensing.nastaran-saffar.me/>
# Copyright © Nastaran Saffaryazdi 2020
#
# Octopus Sensing is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
#  either version 3 of the License, or (at your option) any later version.
#
# Octopus Sensing is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Foobar.
# If not, see <https://www.gnu.org/licenses/>.

import os
import threading
import cv2
from octopus_sensing.devices.device import Device
from octopus_sensing.common.message_creators import MessageType


class WebcamStreaming(Device):
    def __init__(self, camera_no, **kwargs):
        super().__init__(**kwargs)
        self.output_path = os.path.join(self.output_path, "video")
        os.makedirs(self.output_path, exist_ok=True)
        self._camera_number = camera_no
        self._video_capture = None
        self._fps = None
        self._terminate = False
        self.__out = None

    def _run(self):
        self._recording_event = threading.Event()
        self._recording_event.clear()
        self._video_capture = cv2.VideoCapture(self._camera_number)
        self._fps = self._video_capture.get(cv2.CAP_PROP_FPS)
        threading.Thread(target=self._stream_loop, daemon=True).start()
        while True:
            message = self.message_queue.get()
            if message is None:
                continue
            if message.type == MessageType.START:
                file_name = \
                    "{0}/{1}-{2}-{3}.avi".format(self.output_path,
                                                 self.name,
                                                 message.experiment_id,
                                                 str(message.stimulus_id).zfill(2))
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.__out = cv2.VideoWriter(file_name,
                                             fourcc,
                                             self._fps,
                                             (640, 480))
                self._recording_event.set()
            elif message.type == MessageType.STOP:
                self._recording_event.clear()
                self.__out.release()
            elif message.type == MessageType.TERMINATE:
                self._terminate = True
                break
        print("video terminated")
        self._video_capture.release()

    def _stream_loop(self):
        self._video_capture.read()
        try:
            while self._video_capture.isOpened:
                if self._terminate is True:
                    break
                if self._recording_event.wait(timeout=0.5):
                    ret, frame = self._video_capture.read()
                    if ret:
                        self.__out.write(frame)

        except Exception as error:
            print(error)
