import asyncio
import json
from pathlib import Path
import subprocess
import aiohttp.web
import aiortc.mediastreams
import aiortc
import aiortc.contrib.media
import av
import av.frame
import av.packet
import av.video
import fractions
import ssl
import threading
import queue
import time
import os
from typing import Union
import cv2
import logging
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FeedableVideoStreamTrack(aiortc.mediastreams.MediaStreamTrack):
    kind = 'video'

    def __init__(self):
        super().__init__()
        self.VIDEO_CLOCK_RATE = 90000
        self.q = queue.LifoQueue(maxsize=1)
        self.last_time = time.time()

    async def recv(self) -> Union[av.frame.Frame, av.packet.Packet]:
        if self.readyState != "live":
            raise aiortc.mediastreams.MediaStreamError
        
        image_with_timestamp = await asyncio.get_running_loop().run_in_executor(None, self.q.get)
        self.q.task_done()
        image, timestamp_sec, timestamp_nsec = image_with_timestamp
        frame = av.video.VideoFrame.from_ndarray(image) # shape: (height, width, channel) dtype: np.uint8 [0,255]

        frame.pts = int((timestamp_sec + timestamp_nsec / 1000000000) * self.VIDEO_CLOCK_RATE)
        frame.time_base = fractions.Fraction(1, self.VIDEO_CLOCK_RATE)

        return frame
    
    def feed(self, image_with_timestamp):
        try:
            self.q.put_nowait(image_with_timestamp)
        except queue.Full:
            try:
                self.q.get_nowait()
                self.q.task_done()
                logger.debug('lost one image')
            except queue.Empty:
                logger.debug('times fly!')
                pass
            self.q.put_nowait(image_with_timestamp) # Should not throw any error

def asyncio_run_thread_in_new_loop(coroutine):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(coroutine)
    loop.run_forever()

class WebServer:
    def __init__(self):
        self.track = {
            "head": None,
            "wrist_left": None,
            "wrist_right": None,
        }
        
        self.datachannel = {
            "control": None,
        }
        
        self.on_hand = None
        self.on_pedal = None
        self.on_control = None

        self.t = threading.Thread(target=asyncio_run_thread_in_new_loop, args=(self.run_server(), ), daemon=True)
        self.t.start()

    async def run_server(self):
        self.loop = asyncio.get_running_loop()
        self.app = aiohttp.web.Application()

        self.pc: dict[str, aiortc.RTCPeerConnection] = {}

        async def on_shutdown(app):
            # close peer connections
            await asyncio.gather(*[pc.close() for pc in self.pc])
            self.pc.clear()
        self.app.on_shutdown.append(on_shutdown)

        self.app.router.add_post("/offer", self.offer)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.app.router.add_static('/', os.path.join(script_dir, 'static'), show_index=True, )
        
        async def on_prepare(request, response):
            response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
            response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        self.app.on_response_prepare.append(on_prepare)

        # aiohttp.web.run_self.app(self.app, host="0.0.0.0", port=8088, loop=asyncio.get_event_loop())
        # See: https://github.com/aiortc/aiortc/issues/1116

        if not Path("cert.pem").exists():
            logger.info("generating certs")
            subprocess.check_call(
                "openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 3650 -nodes -subj '/CN=astra-teleop-web'",
                shell=True
            )
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain('cert.pem', 'key.pem')

        runner = aiohttp.web.AppRunner(self.app)
        await runner.setup()

        site = aiohttp.web.TCPSite(runner, '0.0.0.0', 9443, ssl_context=ssl_context)
        await site.start()
        
        logger.info("start teleop at https://localhost:9443/index.html")

    async def offer(self, request):
        params = await request.json()

        offer = aiortc.RTCSessionDescription(sdp=params["sdp"], type=params["type"])
        
        if 'head' in self.pc:
            raise aiohttp.web.HTTPBadRequest(reason="Multiple connection! Wait for last connection is done")

        self.pc['head'] = pc = aiortc.RTCPeerConnection()

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()

                del self.pc['head']
                self.datachannel["control"] = None
                self.track["head"] = None
                self.track["wrist_left"] = None
                self.track["wrist_right"] = None
            elif pc.connectionState == "closed":
                del self.pc['head']
                self.datachannel["control"] = None
                self.track["head"] = None
                self.track["wrist_left"] = None
                self.track["wrist_right"] = None
                
        @pc.on("datachannel")
        def on_datachannel(channel: aiortc.RTCDataChannel):
            logger.info("channel(%s) - %s" % (channel.label, repr("created by remote party")))
            if channel.label == "hand":
                @channel.on("message")
                async def on_message(msg):
                    camera_matrix, distortion_coefficients, corners, ids = json.loads(msg)
                    if self.on_hand:
                        self.on_hand(camera_matrix, distortion_coefficients, corners, ids)
            elif channel.label == "pedal":
                @channel.on("message")
                async def on_message(msg):
                    pedal_real_values = json.loads(msg)
                    if self.on_pedal:
                        self.on_pedal(pedal_real_values)
            elif channel.label == "control":
                self.datachannel["control"] = channel

                @channel.on("message")
                async def on_message(msg):
                    control_type = json.loads(msg)
                    if self.on_control:
                        asyncio.create_task(self.on_control(control_type))
            else:
                raise Exception("Unknown label")

        self.track["head"] = FeedableVideoStreamTrack()
        pc.addTransceiver(self.track["head"], "sendonly") # mid: 0
        self.track["wrist_left"] = FeedableVideoStreamTrack()
        pc.addTransceiver(self.track["wrist_left"], "sendonly") # mid: 1
        self.track["wrist_right"] = FeedableVideoStreamTrack()
        pc.addTransceiver(self.track["wrist_right"], "sendonly") # mid: 2

        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return aiohttp.web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )
    
    def control_datachannel_log(self, message):
        if self.datachannel["control"] is not None:
            self.datachannel["control"].send(json.dumps(message))
    
    def track_feed(self, name, image_with_timestamp):
        if self.track[name] is not None:
            try:
                self.track[name].feed(image_with_timestamp)
            except:
                pass

def feed_webserver(webserver, device):
    cam = cv2.VideoCapture(f"/dev/video_{device}", cv2.CAP_V4L2)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    fourcc_value = cv2.VideoWriter_fourcc(*'MJPG')

    image_height = 360
    image_width = 640

    image_size = (image_height, image_width)

    frames_per_second = 30

    cam.set(cv2.CAP_PROP_FOURCC, fourcc_value)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, image_height)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, image_width)
    cam.set(cv2.CAP_PROP_FPS, frames_per_second)
    
    while True:
        ret, color_image = cam.read()
        image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        assert image.shape[0] == 360 and image.shape[1] == 640
        try:
            t = time.time_ns()
            getattr(webserver, f"track_{device}").feed((image, int(t / 1000000000), int(t % 1000000000)))
        except:
            pass


def feed_webserver_av(webserver, device):
    container = av.open(f"/dev/video_{device}", format="v4l2", options={
        "input_format": "mjpeg",
        "framerate": "30",
        "video_size": "640x360",
    })

    for index, frame in enumerate(container.decode(video=0)):
        if index % 2 != 0:
            # FFmpeg have a 256 length size of buffer for v4l2 mmap
            # Too large for latency
            # https://github.com/FFmpeg/FFmpeg/blob/66c05dc03163998fb9a90ebd53e2c39a4f95b7ea/libavdevice/v4l2.c#L55
            continue
        image = frame.to_rgb().to_ndarray()
        assert image.shape[0] == 360 and image.shape[1] == 640
        try:
            t = time.time_ns()
            getattr(webserver, f"track_{device}").feed((image, int(t / 1000000000), int(t % 1000000000)))
        except:
            pass

if __name__ == '__main__':
    webserver = WebServer()
    
    threading.Thread(target=feed_webserver, args=(webserver, "head"), daemon=True).start()
    threading.Thread(target=feed_webserver, args=(webserver, "wrist_left"), daemon=True).start()
    threading.Thread(target=feed_webserver, args=(webserver, "wrist_right"), daemon=True).start()
    
    webserver.on_hand = print
    webserver.on_pedal = print
    webserver.on_control = print
    
    while True:
        time.sleep(0.1)
