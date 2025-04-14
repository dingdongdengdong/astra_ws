import cv2
import cv2.aruco as aruco
import time
import json

def capture():
    # Open video capture (using the default camera)
    cap = cv2.VideoCapture(0)
    # Set the desired resolution and frame rate
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    if not cap.isOpened():
        print("Error: Unable to open video capture")
        return

    # Retrieve and display camera settings
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Using camera: Device 0, {int(width)}x{int(height)} @ {fps} FPS")
    
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector_parameters = cv2.aruco.DetectorParameters()
    detector_parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    # detector_parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_APRILTAG # Most accurate but also slowest with ~200-300ms
    # detector_parameters.aprilTagQuadDecimate = 2
    # detector_parameters.cornerRefinementWinSize = 2
    detector = cv2.aruco.ArucoDetector(aruco_dict, detector_parameters)

    avgTime = 0
    while True:
        ret, mat = cap.read()
        if not ret:
            print("Failed to capture frame")
            break

        t2 = time.perf_counter()
        # Detect ArUco markers in the captured frame
        corners, ids, rejected = detector.detectMarkers(mat) # 15ms@1920x1080 9ms@1280x720
        t3 = time.perf_counter()

        # Convert detected marker corners to a list format (similar to corners_list_list in JS)
        corners_list_list = []
        if corners is not None:
            for temp_corners in corners:
                corners_list_list.append(temp_corners.reshape(-1, 2).tolist())
        else:
            corners_list_list = []

        # Convert detected marker IDs to a list (similar to ids_list in JS)
        ids_list = []
        if ids is not None:
            for id_entry in ids:
                ids_list.append([int(x) for x in id_entry])
        else:
            ids_list = []

        print(json.dumps([corners_list_list, ids_list]))

        # Draw detected markers on a copy of the frame for debugging purposes
        debugMat = mat.copy()
        if corners is not None and len(corners) > 0:
            aruco.drawDetectedMarkers(debugMat, corners, ids)

        # Display the debug image
        cv2.imshow("frame", debugMat)

        t4 = time.perf_counter()
        detect_time = (t3 - t2) * 1000     # in milliseconds
        total_time = (t4 - t2) * 1000      # in milliseconds
        avgTime = avgTime * 0.9 + total_time * 0.1
        print(f"detectMarkers time: {detect_time:.2f} ms")
        print(f"time: {total_time:.2f} ms, avg: {avgTime:.2f} ms")

        # Exit loop when 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources and close display windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture()