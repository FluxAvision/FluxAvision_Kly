客流数据推送概要
客流相机支持 http/https post 方式推送数据至客户平台，使用时只需指定服务器地址和端口即可，推送模式：数据上传和心跳上传：

心跳上传：设备上电后每分钟一次上传，用于监测设备在线；
数据上传：有人进出时上传客流进出计数数据，可精确至秒。
推送接口说明
心跳上传接口
固定每分钟定期通过http post方式上报心跳数据，主要用于数据获取和设备在线状态判断。
http地址：http://XXXX.XXXX.XXXX.XXXX:XX/klyun/kl/equipapi/binocular/heartBeat
https地址：https://XXXX.XXXX.XXXX.XXXX:XX/klyun/kl/equipapi/binocular/heartBeat
上传格式：
{
	"version": 1,
	"macAddress": "4C:BC:98:60:10:8E",
	"ipAddress": "192.168.8.210",
	"connectionType": "Wired",
	"ipAddressMethod": "DHCP",
	"hostName": "Cam-13889",
	"timeZone": 8,
	"hwPlatform": "V3.0",
	"swRelease": "V6.3.6",
	"reportDate": "2023-04-17",
	"sn": "2010012104250097",
	"time": 1631947237
}

各个字段含义如下：
1.version: 接口版本；
2.macAddress: 设备MAC地址；
3.ipAddress: 设备IP地址；
4.connectionType: 设备连接方式，有线或者无线连接；
5.wifiSSID: WiFi连接的SSID【仅连接WiFi时有效】
6.wifiPassword: WiFi连接的密码【仅连接WiFi时有效】
7.ipAddressMethod: 设备获取IP方式，DHCP或者STATIC；
8.hostName: 设备hostname;
9.timeZone: 设备时区；
10.hwPlatform: 设备硬件平台版本；
11.swRelease: 设备固件版本；
12.reportDate: 上报日期；
13.sn: 设备SN；
14.time: Unix 时间戳，心跳上传时设备时间戳；
响应格式：
{
  "code": 0,
  "msg": "success"，
  "data": {
      "sn": "2010012104250097",
      "time": 1631947237
  }
}
各个字段含义如下：
1.code: 返回状态值，0为成功，其他则为失败；
2.msg：返回信息，描述错误信息；
3.data.sn: 设备SN；
4.data.time: Unix 时间戳，服务器端设备时间戳，设备收到后会跟进这个时间进行设备端时间同步；
数据上传接口
通过http post方式上传客流数据：
间隔设置为0时为实时上报模式，客流相机检测到有人经过时会触发上传，数据可以精确到秒；
间隔设置为大于0的整数时为间隔上报模式，客流相机会在指定间隔判断当前间隔时间段是否有数据，有数据则上传。
http地址：http://XXXX.XXXX.XXXX.XXXX:XX/klyun/kl/equipapi/binocular/dataUpload
https地址：https://XXXX.XXXX.XXXX.XXXX:XX/klyun/kl/equipapi/binocular/dataUpload
上传格式
{
  "version": 1,
  "macAddress": "4C:BC:98:60:10:8E",
  "ipAddress": "192.168.8.210",
  "connectionType": "Wired",
  "ipAddressMethod": "DHCP",
  "hostName": "Cam-13889",
  "timeZone": 8,
  "hwPlatform": "V3.0",
  "swRelease": "V6.3.6",
  "reportDate": "2023-04-17",
  "sn": "2010012104250097",
  "time": 1631947237,
  "startTime": 161231947237,
  "endTime": 1631947237,
  "in": 1,
  "out": 2,
  "passby": 2,
  "turnback": 3,
  "avgStayTime": 2000
}
各个字段含义如下：
1.version: 接口版本；
2.macAddress: 设备MAC地址；
3.ipAddress: 设备IP地址；
4.connectionType: 设备连接方式，有线或者无线连接；
5.wifiSSID: WiFi连接的SSID【仅连接WiFi时有效】
6.wifiPassword: WiFi连接的密码【仅连接WiFi时有效】
7.ipAddressMethod: 设备获取IP方式，DHCP或者STATIC；
8.hostName: 设备hostname;
9.timeZone: 设备时区；
10.hwPlatform: 设备硬件平台版本；
11.swRelease: 设备固件版本；
12.reportDate: 上报日期；
13.sn: 设备SN
14.time: 当前上传数据的最新时间
15.startTime: 当前上传数据的起始时间
16.endTime: 当前上传数据的结束时间
17.in: 当前上传时间段内的进入人数
18.out: 当前上传时间段内的离开人数
19.passby: 当前上传时间段内的经过人数
20.turnback: 当前上传时间段内的折返人数
21.avgStayTime: 当前上传时间段内的在客流相机视场内的平均逗留时间
响应格式
{
  "code": 0,
  "msg": "success"，
  "data": {
      "sn": "2010012104250097",
      "time": 1631947237
  }
}
各个字段含义如下：
1.code: 返回状态值，0为成功，其他则为失败；
2.msg：返回信息，描述错误信息；
3.data.sn: 设备SN；
4.data.time: Unix 时间戳，服务器端设备时间戳；
客户端设置

设置选项说明
客户端设置支持两个推送地址，勾选设置服务器、端口、上传间隔后点击设置按钮后，设备就开始根据设置的参数进行上传。


示意图上设置的是上传地址1【http://example1.com:8080/klyun/kl/equipapi/binocular/dataUpload】：5分钟上传一次数据；上传地址2【http://example2.com:8080/klyun/kl/equipapi/binocular/dataUpload】：实时推送数据。设置选型具体说明如下：
服务器：服务器地址，支持IP和域名
端口：服务器端口；
上传间隔：设置为0，则为实时上传；设置为大于0的整数则为固定间隔上传。
注：不支持地址1实时上报地址2间隔上报模式。

