function sleep(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

const handCommTarget = new EventTarget();
const pedalCommTarget = new EventTarget();
const controlCommTarget = new EventTarget();

async function start() {
  if (document.getElementById('start').classList.contains("hidden")) {
    toastr.error("Disconnect first!");
    return;
  }
  document.getElementById('start').classList.add("hidden");
  toastr.info("Connecting...");

  const pc = new RTCPeerConnection({
    sdpSemantics: 'unified-plan'
  });

  // connect audio / video
  pc.addEventListener('track', function (evt) {
    if (evt.track.kind === 'video') {
      if (evt.transceiver.mid === '0') {
        document.getElementById('video-head').srcObject = new MediaStream([evt.track]);
        document.getElementById('video-head').play();
      } else if (evt.transceiver.mid === '1') {
        document.getElementById('video-wrist-left').srcObject = new MediaStream([evt.track]);
        document.getElementById('video-wrist-left').play();
      } else if (evt.transceiver.mid === '2') {
        document.getElementById('video-wrist-right').srcObject = new MediaStream([evt.track]);
        document.getElementById('video-wrist-right').play();
      } else {
        toastr.error("Unsupported mid")
      }
    }
  });

  pc.addTransceiver('video', { direction: 'recvonly' });
  pc.addTransceiver('video', { direction: 'recvonly' });
  pc.addTransceiver('video', { direction: 'recvonly' });

  const handChannel = pc.createDataChannel("hand")

  const handToServerCb = async function (evt) {
    handChannel.send(evt.detail)
  }

  handChannel.addEventListener('open', function (evt) {
    handCommTarget.addEventListener('toServer', handToServerCb);

    handChannel.addEventListener('message', function (evt) {
      handCommTarget.dispatchEvent(new CustomEvent("fromServer", { detail: evt.data }))
    })
  })

  handChannel.addEventListener('close', function (evt) {
    handCommTarget.removeEventListener('toServer', handToServerCb);
  })

  const pedalChannel = pc.createDataChannel("pedal")

  const pedalToServerCb = async function (evt) {
    pedalChannel.send(evt.detail)
  }

  pedalChannel.addEventListener('open', function (evt) {
    pedalCommTarget.addEventListener('toServer', pedalToServerCb);

    pedalChannel.addEventListener('message', function (evt) {
      pedalCommTarget.dispatchEvent(new CustomEvent("fromServer", { detail: evt.data }))
    })
  })

  pedalChannel.addEventListener('close', function (evt) {
    pedalCommTarget.removeEventListener('toServer', pedalToServerCb);
  })

  const controlChannel = pc.createDataChannel("control")

  const controlToServerCb = async function (evt) {
    console.log(evt.detail)
    controlChannel.send(evt.detail)
  }

  controlChannel.addEventListener('open', function (evt) {
    controlCommTarget.addEventListener('toServer', controlToServerCb);

    controlChannel.addEventListener('message', function (evt) {
      controlCommTarget.dispatchEvent(new CustomEvent("fromServer", { detail: evt.data }))
    })
  })

  controlChannel.addEventListener('close', function (evt) {
    controlCommTarget.removeEventListener('toServer', controlToServerCb);
  })

  // Display statistics
  const showPing = async () => {
    const results = await pc.getStats(null)
    
    results.forEach(res => {
      if (res.type === "candidate-pair" && res.nominated) {
        document.getElementById('pc-ping').innerHTML = res.currentRoundTripTime * 1000;
      }
    });
  }
  setInterval(showPing, 1000);

  pc.addEventListener('connectionstatechange', () => {
    document.getElementById('pc-status').innerHTML = pc.connectionState;
    if (pc.connectionState === 'connected') {
      toastr.success("Connected.");
      document.getElementById('player').classList.remove("hidden");
    } else if (pc.connectionState === 'disconnected') {
      toastr.error("Lost connection.");
      clearInterval(showPing)
      document.getElementById('pc-ping').innerHTML = "INF";
      pc.close()
      document.getElementById('player').classList.add("hidden");
      document.getElementById('start').classList.remove("hidden");
    }
  });

  const offer = await pc.createOffer();

  await pc.setLocalDescription(offer);

  // wait for ICE gathering to complete
  await new Promise((resolve) => {
    if (pc.iceGatheringState === 'complete') {
      resolve();
    } else {
      const checkState = () => {
        if (pc.iceGatheringState === 'complete') {
          pc.removeEventListener('icegatheringstatechange', checkState);
          resolve();
        }
      };
      pc.addEventListener('icegatheringstatechange', checkState);
    }
  });

  let response;
  try {
    response = await fetch('/offer', {
      body: JSON.stringify({
        sdp: offer.sdp,
        type: offer.type,
      }),
      headers: {
        'Content-Type': 'application/json'
      },
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`Server response with code ${response.status} message '${await response.text()}'`);
    }
  } catch (err) {
    toastr.error(`Network error: ${err.message}`);
    pc.close()
    document.getElementById('start').classList.remove("hidden");
  }
  const answer = await response.json();

  await pc.setRemoteDescription(answer);
}

class MyCameraCapture {
  // Standard constructor; it simply assigns the mediaStream.
  constructor(captureDevice, width, height, ctx) {
    this.captureDevice = captureDevice;
    this.width = width;
    this.height = height;
    this.ctx = ctx;
  }

  // Async factory method to perform asynchronous initialization.
  static async create() {
    let mediaStream;
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          // frame constraints
          frameRate: { min: 30, ideal: 30, max: 30 },
          width: { min: 1280, ideal: 1280, max: 1280 },
          height: { min: 720, ideal: 720, max: 720 },
        },
      });
    } catch (err) {
      toastr.error(`Error opening video capture (may be your cam have too low resolution): ${err.name} ${err.message}`);
      throw err;
    }

    // Extract video track.
    const videoDevice = mediaStream.getVideoTracks()[0];
    const videoSetting = videoDevice.getSettings();
    toastr.info(`Using camera: ${videoDevice.label} ${videoSetting.width}x${videoSetting.height}@${videoSetting.frameRate}`);
  
    let captureDevice;
    try {
      captureDevice = new ImageCapture(videoDevice, mediaStream);
    } catch (err) {
      toastr.error(`ImageCapture api not supported on your browser`);
      throw err;
    }
  
    const offscreen = new OffscreenCanvas(videoSetting.width, videoSetting.height);
    const ctx = offscreen.getContext("2d", { willReadFrequently: true });

    // const $canvas = document.createElement('canvas');
    // $canvas.width = videoSetting.width;
    // $canvas.height = videoSetting.height;
    // const ctx = $canvas.getContext('2d', { willReadFrequently: true });

    return new MyCameraCapture(captureDevice, videoSetting.width, videoSetting.height, ctx);
  }

  async grabFrame() {
    const frame = await this.captureDevice.grabFrame();
    return frame;
  }

  getImageData(frame) {
    this.ctx.drawImage(frame, 0, 0, frame.width, frame.height);
    const imageData = this.ctx.getImageData(0, 0, frame.width, frame.height); // 5.2ms@1920x1080 2.5ms@1280x720
    return imageData;
  }
}

async function capture() {
  if (localStorage.getItem("camera_matrix") === null) {
    toastr.error("You need calibrate camera first");
    return;
  }
  const camera_matrix_list = JSON.parse(localStorage.getItem("camera_matrix"));
  const distortion_coefficients_list = JSON.parse(localStorage.getItem("distortion_coefficients"));

  if (window.cv2 === undefined) {
    window.cv2 = await cv;
  }
  
  const cap = await MyCameraCapture.create();

  document.getElementById('capture').classList.add("hidden");
  document.getElementById('calibrate').classList.add("hidden");

  const $outCanvas = document.getElementById('canvas-imshow');
  $outCanvas.width = cap.width;
  $outCanvas.height = cap.height;
  const outCtx = $outCanvas.getContext("2d");

  const aruco_dict = cv2.getPredefinedDictionary(cv2.DICT_4X4_50);
  const aruco_detection_parameters = new cv2.aruco_DetectorParameters();
  aruco_detection_parameters.cornerRefinementMethod = cv2.CORNER_REFINE_SUBPIX; // Faster
  // aruco_detection_parameters.cornerRefinementMethod = cv2.CORNER_REFINE_APRILTAG; // Provide subpixel accuracy
  // aruco_detection_parameters.aprilTagQuadDecimate = 2; // Speed up for wasm
  const refine_parameters = new cv2.aruco_RefineParameters(10, 3, true)
  const detector = new cv2.aruco_ArucoDetector(aruco_dict, aruco_detection_parameters, refine_parameters);

  const fromServerCb = async function (evt) {
    console.dir(evt.detail);
  }
  handCommTarget.addEventListener('fromServer', fromServerCb);

  let avgTime = 0;
  while (true) {
    const frame = await cap.grabFrame();

    const t0 = performance.now();
    const imageData = cap.getImageData(frame);
    const t1 = performance.now();

    const mat = cv2.matFromImageData(imageData);

    const corners = new cv2.MatVector();
    const ids = new cv2.Mat();
    const rejected = new cv2.MatVector();

    const t2 = performance.now();
    detector.detectMarkers(mat, corners, ids, rejected); // 63ms@1920x1080 40ms@1280x720
    const t3 = performance.now();

    const corners_list_list = [];
    for (let l = 0; l < corners.size(); ++l) {
      const temp_corners = corners.get(l);
      const corners_list = [];
      const rows = temp_corners.rows;
      const cols = temp_corners.cols;
      const channels = Math.trunc(temp_corners.type() / 8) + 1;
      for (let i = 0; i < rows; ++i) {
        const row = [];
        for (let j = 0; j < cols; ++j) {
          const point = [];
          for (let k = 0; k < channels; ++k) {
            point.push(temp_corners.data32F[(i * cols + j) * channels + k]);
          }
          row.push(point);
        }
        corners_list.push(row);
      }
      corners_list_list.push(corners_list);
    }
    
    const ids_list = [];
    for (let i = 0; i < ids.rows; ++i) {
      const row = [];
      for (let j = 0; j < ids.cols; ++j) {
        row.push(ids.data32S[i * ids.cols + j]);
      }
      ids_list.push(row);
    }

    // console.log(JSON.stringify([
    //   corners_list_list,
    //   ids_list
    // ]));

    handCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify([
      camera_matrix_list,
      distortion_coefficients_list,
      corners_list_list,
      ids_list
    ]) }))

    cv2.cvtColor(mat, mat, cv2.COLOR_RGBA2BGR);
    cv2.drawDetectedMarkers(mat, corners, ids);

    cv2.cvtColor(mat, mat, cv2.COLOR_BGR2RGBA);
    const debugImageData = new ImageData(new Uint8ClampedArray(mat.data), mat.cols, mat.rows);
    outCtx.putImageData(debugImageData, 0, 0);

    corners.delete();
    ids.delete();
    rejected.delete();

    mat.delete();

    const t4 = performance.now();
    avgTime = avgTime * 0.9 + (t4 - t0) * 0.1;  
    // console.log(`imageData time: ${(t1 - t0).toFixed(2)}`);
    // console.log(`detectMarkers time: ${(t3 - t2).toFixed(2)}`);
    // console.log(`time: ${(t4 - t0).toFixed(2)}, avg: ${avgTime.toFixed(2)}`); // 50ms@1280x720
    document.getElementById('aruco-timing').innerHTML = (t4 - t0).toFixed(2);
  }
  
  handCommTarget.removeEventListener('fromServer', fromServerCb);

  aruco_dict.delete();
  aruco_detection_parameters.delete();
  refine_parameters.delete();
  detector.delete();

  document.getElementById('capture').classList.remove("hidden");
  document.getElementById('calibrate').classList.remove("hidden");
}

async function calibrate() {
  document.getElementById('capture').classList.add("hidden");
  document.getElementById('calibrate').classList.add("hidden");

  if (window.cv2 === undefined) {
    window.cv2 = await cv;
  }
  
  const cap = await MyCameraCapture.create();

  const $outCanvas = document.getElementById('canvas-imshow');
  $outCanvas.width = cap.width;
  $outCanvas.height = cap.height;
  const outCtx = $outCanvas.getContext("2d");

  // Aruco Board
  const aruco_dict = cv2.getPredefinedDictionary(cv2.DICT_5X5_1000);
  const empty_mat = new cv2.Mat();
  const aruco_board = new cv2.aruco_CharucoBoard(new cv2.Size(5, 7), 0.04, 0.02, aruco_dict, empty_mat);

  const charuco_parameters = new cv2.aruco_CharucoParameters();
  const detector_parameters = new cv2.aruco_DetectorParameters();
  const refine_parameters = new cv2.aruco_RefineParameters(10, 3, true);
  const charuco_detector = new cv2.aruco_CharucoDetector(aruco_board, charuco_parameters, detector_parameters, refine_parameters);

  let number_of_points = 0;
  const all_object_points = new cv2.MatVector();
  const all_image_points = new cv2.MatVector();
  
  let cnt = 0;
  let last_cnt = performance.now();
  
  const max_cnt = 40;
  const min_cnt_interval = 1000;
  
  let avgTime = 0;
  while (cnt < max_cnt) {
    const frame = await cap.grabFrame();

    const t0 = performance.now();
    const imageData = cap.getImageData(frame);
    const t1 = performance.now();

    const mat = cv2.matFromImageData(imageData);
    cv2.cvtColor(mat, mat, cv2.COLOR_RGBA2BGR);
    
    const charuco_corners = new cv2.Mat();
    const charuco_ids = new cv2.Mat();
    const marker_corners = new cv2.MatVector();
    const marker_ids = new cv2.Mat();
  
    const t2 = performance.now();
    charuco_detector.detectBoard(mat, charuco_corners, charuco_ids, marker_corners, marker_ids);
    const t3 = performance.now();
  
    // console.log('len(charuco_ids) =', charuco_ids.rows);
    
    if (charuco_ids.rows > 0) {
      // console.dir(charuco_corners.data32F) // type(): cv2.CV_32FC2
      // console.dir(charuco_ids.data32S) // type(): cv2.CV_32SC1
  
      // matchImagePoints require complicated type convert
      const detected_corners = new cv2.MatVector();
      for (let i = 0; i < charuco_corners.rows; ++i) {
        const charuco_corner = new cv2.Mat(1, 1, cv2.CV_32FC2);
        charuco_corner.data.set(charuco_corners.data.subarray(i * 8, i * 8 + 8));
        detected_corners.push_back(charuco_corner);
      }
  
      const object_points = new cv2.Mat();
      const image_points = new cv2.Mat();
      aruco_board.matchImagePoints(detected_corners, charuco_ids, object_points, image_points);
      
      // console.log('len(object_points) =', object_points.rows);
  
      if (object_points.rows >= 8 && performance.now() - last_cnt > min_cnt_interval) {
        last_cnt = performance.now();
        ++cnt;
        number_of_points += object_points.rows;
        all_object_points.push_back(object_points);
        all_image_points.push_back(image_points);
        toastr.info(`Collecting image (${cnt}/${max_cnt})`, undefined, { timeOut: min_cnt_interval, showDuration: 0, hideDuration: 0 });
      }
  
      cv2.drawDetectedCornersCharuco(mat, charuco_corners, charuco_ids);

      detected_corners.delete();
      object_points.delete();
      image_points.delete();
    }

    // aruco_board.generateImage(new cv2.Size(1280, 720), dstFrame, 0, 1);

    cv2.cvtColor(mat, mat, cv2.COLOR_BGR2RGBA);
    const debugImageData = new ImageData(new Uint8ClampedArray(mat.data), mat.cols, mat.rows);
    outCtx.putImageData(debugImageData, 0, 0);
  
    charuco_corners.delete();
    charuco_ids.delete();
    marker_corners.delete();
    marker_ids.delete();

    mat.delete();

    const t4 = performance.now();
    avgTime = avgTime * 0.9 + (t4 - t0) * 0.1;  
    console.log(`imageData time: ${(t1 - t0).toFixed(2)}`);
    console.log(`detectBoard time: ${(t3 - t2).toFixed(2)}`);
    console.log(`time: ${(t4 - t0).toFixed(2)}, avg: ${avgTime.toFixed(2)}`); // 50ms@1280x720
    document.getElementById('aruco-timing').innerHTML = (t4 - t0).toFixed(2);
  }
  
  // console.dir(number_of_points)
  
  toastr.success(`Collection done. It may take about 3 minutes to do calibration. number_of_points: ${number_of_points}`);
  
  await sleep(1000);
  
  const camera_matrix = new cv2.Mat();
  const distortion_coefficients = new cv2.Mat();
  const rotation_vectors = new cv2.MatVector();
  const translation_vectors = new cv2.MatVector();
  const empty_mat2 = new cv2.Mat();
  const empty_mat3 = new cv2.Mat();
  const empty_mat4 = new cv2.Mat();

  const projection_error = cv2.calibrateCameraExtended(
    all_object_points,
    all_image_points,
    new cv2.Size(cap.width, cap.height),
    camera_matrix, 
    distortion_coefficients, 
    rotation_vectors, 
    translation_vectors,
    empty_mat2,
    empty_mat3,
    empty_mat4
  );

  // console.dir(camera_matrix.rows); // type(): cv2.CV_64FC1
  // console.dir(camera_matrix.cols); // type(): cv2.CV_64FC1
  // console.dir(camera_matrix.data64F); // type(): cv2.CV_64FC1
  // console.dir(distortion_coefficients.rows); // type(): cv2.CV_64FC1
  // console.dir(distortion_coefficients.cols); // type(): cv2.CV_64FC1
  // console.dir(distortion_coefficients.data64F); // type(): cv2.CV_64FC1
  // console.dir(projection_error);

  const camera_matrix_list = [];
  for (let i = 0; i < camera_matrix.rows; ++i) {
    const row = [];
    for (let j = 0; j < camera_matrix.cols; ++j) {
      row.push(camera_matrix.data64F[i * camera_matrix.cols + j]);
    }
    camera_matrix_list.push(row);
  }
  
  const distortion_coefficients_list = [];
  for (let i = 0; i < distortion_coefficients.rows; ++i) {
    const row = [];
    for (let j = 0; j < distortion_coefficients.cols; ++j) {
      row.push(distortion_coefficients.data64F[i * distortion_coefficients.cols + j]);
    }
    distortion_coefficients_list.push(row);
  }

  localStorage.setItem("camera_matrix", JSON.stringify(camera_matrix_list));
  localStorage.setItem("distortion_coefficients", JSON.stringify(distortion_coefficients_list));
  
  toastr.success(`Calibration result saved! projection_error: ${projection_error}, camera_matrix: ${JSON.stringify(camera_matrix_list)}, distortion_coefficients ${JSON.stringify(distortion_coefficients_list)}`);

  aruco_dict.delete();
  aruco_board.delete();
  empty_mat.delete();

  charuco_parameters.delete();
  detector_parameters.delete();
  refine_parameters.delete();
  charuco_detector.delete();

  all_object_points.delete();
  all_image_points.delete();

  camera_matrix.delete();
  distortion_coefficients.delete();
  rotation_vectors.delete();
  translation_vectors.delete();
  empty_mat2.delete();
  empty_mat3.delete();
  empty_mat4.delete();

  document.getElementById('capture').classList.remove("hidden");
  document.getElementById('calibrate').classList.remove("hidden");
}

async function getSerial() {
  let port;
  try {
    const usbVendorId = 0x10c4; // Silicon Labs
    port = await navigator.serial.requestPort({ filters: [{ usbVendorId }] })

    await port.open({ baudRate: 921600 });
  } catch (error) {
    toastr.error(`Failed to open port: ${error.message}`);
    throw error;
  }
  
  const writer = port.writable.getWriter();

  async function* gen() {
    let isClose;
    while (port.readable) {
      // see: https://web.dev/articles/streams?hl=zh-cn#creating_a_readable_byte_stream
      const reader = port.readable.getReader({ mode: "byob" });
      try {
        while (true) {
          // fixed length 
          let buffer = new ArrayBuffer(16 + 2); // package length = 16
          let offset = 0

          const { value, done } = await reader.read(new Uint8Array(buffer, 0, 1));
          if (done) throw Error('done'); // |reader| has been canceled.
          console.assert(value.byteLength > 0);

          buffer = value.buffer;

          // syncing
          while ((new Uint8Array(buffer, 0, 1))[0] != 0x5a) {
            console.log("syncing..." + (new Uint8Array(buffer, 0, 1))[0]);
            const { value, done } = await reader.read(new Uint8Array(buffer, 0, 1));
            if (done) throw Error('done'); // |reader| has been canceled.
            console.assert(value.byteLength > 0);

            buffer = value.buffer;
          }
          offset += 1;

          // read remain package
          while (offset < buffer.byteLength) {
            const { value, done } = await reader.read(new Uint8Array(buffer, offset, buffer.byteLength - offset));
            if (done) throw Error('done'); // |reader| has been canceled.
            console.assert(value.byteLength > 0);

            buffer = value.buffer;
            offset += value.byteLength;
          }
          
          isClose = yield buffer;
          if (isClose) throw Error('Close');
        }
      } catch (error) {
        // Handle |error|...
        if (error.message !== "Close") {
          toastr.error("oops")
          toastr.error(error)
        }
      } finally {
        reader.releaseLock();
      }
      if (isClose) break;
    }
    writer.releaseLock();

    port.close();
  }
  
  const g = await gen();

  return { serialRead: (close) => g.next(close), serialWrite: writer.write };
}

const PEDAL_MAX = 4096;

const pedalNames = ["angular-pos", "angular-neg", "linear-neg", "linear-pos"];
const pedalIds = [0, 1, 2, 3];

function getPedalValues(buffer) {
  let pedalValues = [];
  const data = new DataView(buffer, 2);
  for (const i in pedalNames) {
    pedalValues.push(data.getUint16(2 * pedalIds[i], false) / PEDAL_MAX);
  }
  return pedalValues;
}

async function connectPedal() {
  if (localStorage.getItem("pedalMin") === null) {
    toastr.error("You need calibrate pedal first");
    return;
  }
  const pedalMin = JSON.parse(localStorage.getItem("pedalMin"));
  const pedalMax = JSON.parse(localStorage.getItem("pedalMax"));

  const { serialRead, serialWrite } = await getSerial();
  
  document.getElementById('connect-pedal').classList.add("hidden");
  document.getElementById('calibrate-pedal').classList.add("hidden");
  toastr.success("Pedel connected.");
  
  document.getElementById('pedal-status').innerHTML = 'Pedal connected';

  const fromServerCb = async function (evt) {
    console.dir(evt.detail);
    await serialWrite(evt.detail);
  }

  pedalCommTarget.addEventListener('fromServer', fromServerCb);

  while (true) {
    const { value: buffer, done } = await serialRead();
    if (done) break;

    // see: https://stackoverflow.com/questions/7869752/javascript-typed-arrays-and-endianness
    const pedalValues = getPedalValues(buffer);
    for (const i in pedalNames) {
      document.getElementById('pedal-' + pedalNames[i]).value = pedalValues[i] * 100;
    }

    const pedalRealValues = [];
    for (const i in pedalNames) {
      pedalRealValues.push((pedalValues[i] - pedalMin[i]) / (pedalMax[i] - pedalMin[i]));
    }
    
    pedalCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify(pedalRealValues) }))
  }

  pedalCommTarget.removeEventListener('fromServer', fromServerCb);
  
  document.getElementById('pedal-status').innerHTML = 'Pedal disconnected';

  document.getElementById('connect-pedal').classList.remove("hidden");
  document.getElementById('calibrate-pedal').classList.remove("hidden");
  toastr.success("Pedel disconnected.");
}

async function calibratePedal() {
  const { serialRead } = await getSerial();
  
  document.getElementById('connect-pedal').classList.add("hidden");
  document.getElementById('calibrate-pedal').classList.add("hidden");
  toastr.success("Pedel connected.");
  
  document.getElementById('pedal-status').innerHTML = 'Pedal connected';

  async function wait(prompt) {
    toastr.info(prompt, undefined, { timeOut: 2000, showDuration: 0, hideDuration: 0 });

    const start = performance.now();
    while (true) {
      const { value: buffer, done } = await serialRead();
      if (done) throw new Error;

      // see: https://stackoverflow.com/questions/7869752/javascript-typed-arrays-and-endianness
      const pedalValues = getPedalValues(buffer);
      for (const i in pedalNames) {
        document.getElementById('pedal-' + pedalNames[i]).value = pedalValues[i] * 100;
      }
      
      if (performance.now() - start > 2000) {
        return pedalValues;
      }
    }
  }

  const pedalMin = await wait("Release all the pedals.");
    
  await wait("Min value saved.");

  const pedalMax = [];
  
  for (const i in pedalNames) {
    pedalValue = await wait(`Press pedal ${pedalNames[i]}.`);
    pedalMax.push(pedalValue[i]);
    
    await wait(`Release pedal ${pedalNames[i]}.`);
  }
    
  localStorage.setItem("pedalMin", JSON.stringify(pedalMin));
  localStorage.setItem("pedalMax", JSON.stringify(pedalMax));

  toastr.success(`Pedal calibration saved. <br>Min: ${pedalMin}<br>Max: ${pedalMax}`);

  await serialRead(true);
  
  document.getElementById('pedal-status').innerHTML = 'Pedal disconnected';

  document.getElementById('connect-pedal').classList.remove("hidden");
  document.getElementById('calibrate-pedal').classList.remove("hidden");
}

window.addEventListener('load', function () {
  // Notice: autoplay is restricted when user is not clicked the page
  // start()

  document.addEventListener(
    "keydown",
    (event) => {
      const keyName = event.key;
  
      if (keyName === "Control") {
        // do not alert when only Control key is pressed.
        return;
      }
  
      if (event.ctrlKey) {
        // Even though event.key is not 'Control' (e.g., 'a' is pressed),
        // event.ctrlKey may be true if Ctrl key is pressed at the same time.
        // alert(`Combination of ctrlKey + ${keyName}`);
        return;
      } else {
        if (keyName.toLowerCase() == '0') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("teleop_mode_none") }));
        } else if (keyName.toLowerCase() == '`') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("teleop_mode_base") }));
        } else if (keyName.toLowerCase() == '1') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("teleop_mode_arm") }));
        }else if (keyName.toLowerCase() == '~') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("teleop_mode_base_with_reset") }));
        } else if (keyName.toLowerCase() == '!') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("teleop_mode_arm_with_reset") }));
        } else if (keyName.toLowerCase() == '2') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("percise_mode_false") }));
        } else if (keyName.toLowerCase() == '3') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("percise_mode_true") }));
        } else if (keyName.toLowerCase() == '4') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("percise_mode_more_percise") }));
        } else if (keyName.toLowerCase() == 'r') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("reset") }));
        } else if (keyName.toLowerCase() == 'f') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("done") }));
        } else if (keyName.toLowerCase() == 't') {
          start();
        } else if (keyName.toLowerCase() == 'z') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("gripper_lock_left") }));
        } else if (keyName.toLowerCase() == 'x') {
          controlCommTarget.dispatchEvent(new CustomEvent("toServer", { detail: JSON.stringify("gripper_lock_right") }));
        }
      }
    },
    false,
  );

  controlCommTarget.addEventListener('fromServer', async function (evt) {
    message = JSON.parse(evt.detail);
    toastr.info("Server Message: " + message);

    if (message === "Teleop Mode: None") {
      document.getElementById('teleop-mode').innerHTML = 'None';
      document.getElementById('teleop-mode').style.color = 'black';
    } else if (message === "Teleop Mode: Base") {
      document.getElementById('teleop-mode').innerHTML = 'Base';
      document.getElementById('teleop-mode').style.color = 'red';
    } else if (message === "Teleop Mode: Arm") {
      document.getElementById('teleop-mode').innerHTML = 'Arm';
      document.getElementById('teleop-mode').style.color = 'blue';
    } else if (message === "Teleop Mode: Arm (Percise)") {
      document.getElementById('teleop-mode').innerHTML = 'Arm (Percise)';
      document.getElementById('teleop-mode').style.color = 'blue';
    } else if (message === "Teleop Mode: Arm (More Percise)") {
      document.getElementById('teleop-mode').innerHTML = 'Arm (More Percise)';
      document.getElementById('teleop-mode').style.color = 'blue';
    } else if (message === "Left Gripper Lock: Locked (Ready to Unlock)") {
      document.getElementById('gripper-lock-left').innerHTML = 'Locked (Ready to Unlock)';
    } else if (message === "Right Gripper Lock: Locked (Ready to Unlock)") {
      document.getElementById('gripper-lock-right').innerHTML = 'Locked (Ready to Unlock)';
    } else if (message === "Left Gripper Lock: Unlocked") {
      document.getElementById('gripper-lock-left').innerHTML = 'Unlocked';
    } else if (message === "Right Gripper Lock: Unlocked") {
      document.getElementById('gripper-lock-right').innerHTML = 'Unlocked';
    } else if (message.startsWith("Left Gripper Lock: Locked")) {
      document.getElementById('gripper-lock-left').innerHTML = 'Locked';
    } else if (message.startsWith("Right Gripper Lock: Locked")) {
      document.getElementById('gripper-lock-right').innerHTML = 'Locked';
    } else if (message === "Left Gripper Lock: Locked (Ready to Unlock)") {
      document.getElementById('gripper-lock-left').innerHTML = 'Locked (Ready to Unlock)';
    } else if (message === "Right Gripper Lock: Locked (Ready to Unlock)") {
      document.getElementById('gripper-lock-right').innerHTML = 'Locked (Ready to Unlock)';
    }
  });

  toastr.options = {
    "progressBar": true,
    "positionClass": "toast-bottom-right",
    // "preventDuplicates": true,
  };

  const MAX_TOASTS = 6;
  toastr.subscribe(function(args) {
      if (args.state === 'visible') {
        var toasts = $("#toast-container > *:not([hidden])");
        if (toasts && toasts.length > MAX_TOASTS)
          toasts[toasts.length - 1].hidden = true;
      }
  });

  toastr.success("Click the start stream button, or press `t` to start stream.");
})