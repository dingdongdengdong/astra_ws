#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <thread>

#include <chrono>
#include <utility>

#include <errno.h>
#include <fcntl.h> /* low-level i/o */
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>
#include <linux/videodev2.h>

#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "rcpputils/endian.hpp"

#include <opencv2/opencv.hpp>

#define CLEAR(x) memset(&(x), 0, sizeof(x))

static int xioctl(int fh, uint32_t request, void *arg) {
    int r;
    do {
        r = ioctl(fh, request, arg);
    } while (-1 == r && EINTR == errno);
    return r;
}

#define CAP_PROP_BUFFERSIZE 2

void cap_thread(
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub, 
    std::string device, 
    int image_width, int image_height, double framerate, 
    int resize_image_width, int resize_image_height
) {
    const char *dev_name = device.c_str();

    // open_device
    struct stat st;
    int ret = stat(dev_name, &st);
    assert(ret != -1); // cannot identify
    assert(S_ISCHR(st.st_mode)); // not a device file

    int fd = open(dev_name, O_RDWR /* required */ | O_NONBLOCK, 0);
    assert(fd != -1); // cannot open

    // init_device
    struct v4l2_capability cap;
    ret = xioctl(fd, VIDIOC_QUERYCAP, &cap);
    assert(ret != -1); // errno == EINVAL ? no V4L2 device : errno_exit("VIDIOC_QUERYCAP");
    assert(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE); // no video capture device

    // using mmap as io method
    assert(cap.capabilities & V4L2_CAP_STREAMING); // not support streaming i/o

    /* Select video input, video standard and tune here. */
    struct v4l2_cropcap cropcap;
    CLEAR(cropcap);
    cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    struct v4l2_crop crop;
    ret = xioctl(fd, VIDIOC_CROPCAP, &cropcap);
    if (ret == 0) {
        crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        crop.c = cropcap.defrect; /* reset to default */
        ret = xioctl(fd, VIDIOC_S_CROP, &crop);
        if (ret == -1) {
            switch (errno) {
            case EINVAL:
                /* Cropping not supported. */
                break;
            default:
                /* Errors ignored. */
                break;
            }
        }
    } else {
        /* Errors ignored. */
    }

    struct v4l2_format fmt;
    CLEAR(fmt);
    fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    /* Preserve original settings as set by v4l2-ctl for example */
    ret = xioctl(fd, VIDIOC_G_FMT, &fmt);
    assert(ret != -1); // errno_exit("VIDIOC_G_FMT");

    // set custom image meta
    fmt.fmt.pix.width = image_width;
    fmt.fmt.pix.height = image_height;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_MJPEG;
    ret = xioctl(fd, VIDIOC_S_FMT, &fmt);
    assert(ret != -1); // errno_exit("VIDIOC_S_FMT");
    ret = xioctl(fd, VIDIOC_G_FMT, &fmt);
    assert(ret != -1); // errno_exit("VIDIOC_G_FMT");
    assert(fmt.fmt.pix.pixelformat == V4L2_PIX_FMT_MJPEG);

    /* Buggy driver paranoia. */
    unsigned int min = fmt.fmt.pix.width * 2;
    if (fmt.fmt.pix.bytesperline < min)
        fmt.fmt.pix.bytesperline = min;
    min = fmt.fmt.pix.bytesperline * fmt.fmt.pix.height;
    if (fmt.fmt.pix.sizeimage < min)
        fmt.fmt.pix.sizeimage = min;

    // ref: https://gist.github.com/TIS-Edgar/e2bd764e5594897d1835
    struct v4l2_streamparm parm;
    parm.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    parm.parm.capture.timeperframe.numerator = 1;
    parm.parm.capture.timeperframe.denominator = framerate;
    ret = xioctl(fd, VIDIOC_S_PARM, &parm);
    assert(ret != -1);

    // init_mmap
    struct v4l2_requestbuffers req;
    CLEAR(req);
    req.count = CAP_PROP_BUFFERSIZE;
    req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    req.memory = V4L2_MEMORY_MMAP;
    ret = xioctl(fd, VIDIOC_REQBUFS, &req);
    assert(ret != -1); // EINVAL == errno ? not support memory mapping : errno_exit("VIDIOC_REQBUFS");
    assert(req.count >= CAP_PROP_BUFFERSIZE); // Insufficient buffer memory

    struct buffer_s {
        void *start;
        size_t length;
    };
    struct buffer_s *buffers = (struct buffer_s *)calloc(req.count, sizeof(*buffers));
    assert(buffers); // Out of memory

    unsigned int n_buffers;
    for (n_buffers = 0; n_buffers < req.count; ++n_buffers) {
        struct v4l2_buffer buf;
        CLEAR(buf);
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index = n_buffers;

        ret = xioctl(fd, VIDIOC_QUERYBUF, &buf);
        assert(ret != -1); // errno_exit("VIDIOC_QUERYBUF");

        buffers[n_buffers].length = buf.length;
        buffers[n_buffers].start = mmap(
            NULL /* start anywhere */,
            buf.length,
            PROT_READ | PROT_WRITE /* required */,
            MAP_SHARED /* recommended */,
            fd,
            buf.m.offset
        );
        assert(buffers[n_buffers].start != MAP_FAILED); // errno_exit("mmap")
    }

    // start_capturing
    for (unsigned int i = 0; i < n_buffers; ++i) {
        struct v4l2_buffer buf;
        CLEAR(buf);
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index = i;

        ret = xioctl(fd, VIDIOC_QBUF, &buf);
        assert(ret != -1); // errno_exit("VIDIOC_QBUF");
    }

    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    ret = xioctl(fd, VIDIOC_STREAMON, &type);
    assert(ret != -1); // errno_exit("VIDIOC_STREAMON");

    // mainloop
    for (;;) {
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(fd, &fds);

        struct timeval tv;
        /* Timeout. */
        tv.tv_sec = 2;
        tv.tv_usec = 0;

        // block until new image
        int r = select(fd + 1, &fds, NULL, NULL, &tv);
        assert(r != 0); // select timeout
        if (r == -1) {
            if (EINTR == errno)
                continue;
            else
                assert(false); // errno_exit("select");
        }

        // read_image
        struct v4l2_buffer buf;
        CLEAR(buf);
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;

        ret = xioctl(fd, VIDIOC_DQBUF, &buf);
        if (ret == -1) {
            if (errno == EAGAIN) { // errno is thread-safe, ref: https://stackoverflow.com/questions/1694164/is-errno-thread-safe
                // nanosleep((const struct timespec[]){{0, 6000000L}}, NULL); // sleep 6ms
                // will cause buffer block up
                continue; /* EAGAIN - continue select loop. */
            } else if (errno == EIO) {
                /* Could ignore EIO, see spec. */
                /* fall through */
            } else {
                assert(false); // errno_exit("VIDIOC_DQBUF"); // 这里出问题一般是摄像头掉了
            }
        }
        assert(buf.index < n_buffers);
        
        // Ref: https://github.com/opencv/opencv/blob/4.x/modules/videoio/src/cap_v4l.cpp
        cv::Mat image(cv::Size(image_width, image_height), CV_8UC3);
        cv::imdecode(cv::Mat(1, buf.bytesused, CV_8U, buffers[buf.index].start), cv::IMREAD_COLOR, &image);
        cv::cvtColor(image, image, cv::COLOR_BGR2RGB);
        
        if (resize_image_width) {
            cv::resize(image, image, cv::Size(resize_image_width, resize_image_height));
        }

        sensor_msgs::msg::Image::SharedPtr msg = std::make_shared<sensor_msgs::msg::Image>();
        msg->header.stamp.sec = buf.timestamp.tv_sec;
        msg->header.stamp.nanosec = buf.timestamp.tv_usec * 1000;
        msg->header.frame_id = "default_cam";
        msg->height = image.rows;
        msg->width = image.cols;
        msg->encoding = "rgb8";
        msg->is_bigendian = (rcpputils::endian::native == rcpputils::endian::big);
        msg->step = image.cols * image.elemSize();
        size_t size = msg->step * image.rows;
        msg->data.resize(size);

        if (image.isContinuous()) {
            memcpy(reinterpret_cast<char *>(&msg->data[0]), image.data, size);
        } else {
            // Copy by row by row
            uchar *ros_data_ptr = reinterpret_cast<uchar *>(&msg->data[0]);
            uchar *cv_data_ptr = image.data;
            for (int i = 0; i < image.rows; ++i) {
                memcpy(ros_data_ptr, cv_data_ptr, msg->step);
                ros_data_ptr += msg->step;
                cv_data_ptr += image.step;
            }
        }
        pub->publish(*msg);

        static std::chrono::high_resolution_clock::time_point last_time;
        std::chrono::high_resolution_clock::time_point this_time = std::chrono::high_resolution_clock::now();
        double duration = std::chrono::duration_cast<std::chrono::nanoseconds>(this_time - last_time).count() / 1000000.0;
        printf("%lfms\n", duration);
        last_time = this_time;

        // give back buffer
        ret = xioctl(fd, VIDIOC_QBUF, &buf);
        assert(ret != -1); // errno_exit("VIDIOC_QBUF");
    }

    // stop_capturing
    type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    ret = xioctl(fd, VIDIOC_STREAMOFF, &type);
    assert(ret != -1); // errno_exit("VIDIOC_STREAMOFF");

    // uninit_device
    unsigned int i;
    for (i = 0; i < n_buffers; ++i) {
        ret = munmap(buffers[i].start, buffers[i].length);
        assert(ret != -1); // errno_exit("munmap");
    }

    free(buffers);

    // close_device
    ret = close(fd);
    assert(ret != -1); // errno_exit("close");

    fd = -1;
}

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::Node::SharedPtr node = std::make_shared<rclcpp::Node>("simple_cap_node");
    
    node->declare_parameter("device", "/dev/video_head");
    node->declare_parameter("image_width", 640);
    node->declare_parameter("image_height", 360);
    node->declare_parameter("framerate", 30.0);
    node->declare_parameter("resize_image_width", 0);
    node->declare_parameter("resize_image_height", 0);

    std::string device = node->get_parameter("device").as_string();
    int image_width = node->get_parameter("image_width").as_int();
    int image_height = node->get_parameter("image_height").as_int();
    double framerate = node->get_parameter("framerate").as_double();
    int resize_image_width = node->get_parameter("resize_image_width").as_int();
    int resize_image_height = node->get_parameter("resize_image_height").as_int();

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher = node->create_publisher<sensor_msgs::msg::Image>("image_raw", 10);

    std::thread th(cap_thread, 
        publisher, 
        device, 
        image_width, image_height, framerate, 
        resize_image_width, resize_image_height
    );
    rclcpp::spin(node);
    rclcpp::shutdown();
    th.join();
    return 0;
}