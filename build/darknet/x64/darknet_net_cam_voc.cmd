# Download for Android phone mjpeg-stream: IP Webcam / Smart WebCam
#
# Smart WebCam - preferably: https://play.google.com/store/apps/details?id=com.acontech.android.SmartWebCam
# IP Webcam: https://play.google.com/store/apps/details?id=com.pas.webcam
#
# Replace the address below, on shown in the phone application

darknet.exe detector demo data/voc.data cfg/yolov2-voc.cfg yolo-voc.weights http://192.168.0.80:8080/video?dummy=param.mjpg -i 0 


pause