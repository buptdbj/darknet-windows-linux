# -*- coding:utf-8 -*-
import configparser
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from threading import Thread

import requests

sys.path.append(os.path.dirname(os.getcwd()))
from video_log_parser import ResultParser


def upload_file(fname):
    print('上传数据文件:', fname)
    f = {"file": open(fname, "rb")}
    r = requests.post(api_server + 'file', files=f)
    print('上传数据文件结果:', r.text)


def upload_status(stat):
    print('上传状态:', stat)
    r = requests.post(api_server + 'status', json=stat)
    print('上传状态结果:', r.text)


def save_local(fname, data):
    # 保存结果数据到本地
    with open(fname, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)


def parser_log(code, id, loc, pole_length, rtsp_num):
    # 分析日志
    rp = ResultParser('result_log/{}-{}-{}-{}.log'.format(code, id, loc, rtsp_num), code, id, loc, pole_length, rtsp_num)
    while True:
        json_result, end_file = rp.parser()
        # 上传图表数据
        fname = 'result_log/{}-{}-{}-{}-chart.log'.format(code, id, loc, rtsp_num)
        save_local(fname, rp.get_chart_data())
        upload_file(fname)
        # 上传结果json文件
        fname = 'result_log/{}-{}-{}-{}-result.json'.format(code, id, loc, rtsp_num)
        save_local(fname, json_result)
        upload_file(fname)
        # 上传卸钻视频
        list_upload_mp4 = rp.get_video_data()
        while len(list_upload_mp4):
            fn = list_upload_mp4.pop(0)
            if fn not in mp4_uploaded_cache:
                upload_file('result_mp4/{}'.format(fn))
                mp4_uploaded_cache.append(fn)
        # 结束分析
        if end_file:
            # 上传完整的视频文件
            upload_file('result_mp4/{}-{}-{}-{}.mp4'.format(code, id, loc, rtsp_num))
            print('----------结束分析----------\n----------{}-{}-{}-{}----------'.format(code, id, loc, rtsp_num))
            return
        time.sleep(10)


if __name__ == '__main__':
    """
        1. 从服务器获取任务Json
        2. 启动分析服务
        3. 开线程分析结果日志
        4. 开启直播服务
        5. 动态上传结果
    """
    ports = [23333, 23334, 23335, 23336, 23337, 23338, 23339, 23340, 23341, 23342, 23343, 23344, 23345, 23346, 23347, 23348, 23349, 23350]
    conf = configparser.ConfigParser()  # 读取配置信息
    conf.read("config.cfg")
    api_server = conf.get('config', 'api_server')
    data_path = conf.get('cmd', 'data_path')
    cfg_path = conf.get('cmd', 'cfg_path')
    weight_path = conf.get('cmd', 'weight_path')
    mp4_uploaded_cache = []  # 缓存已经上传的mp4，防止重复上传

    while True:
        resp = requests.get(api_server + 'job')  # 从服务器获取任务Json
        resp_json = json.loads(resp.text)
        if resp_json['data']:
            print('{}   拿到任务信息:{},开始执行任务.\n'.format(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), resp.text))

            mine_code = resp_json['data']['cs_mine_code']
            work_location = resp_json['data']['cs_workface_location']
            work_id = resp_json['data']['cs_workface_id']
            pole_length = resp_json['data']['cs_pole_length']
            # hole_num = resp_json['data']['cs_hole_number'] if 'cs_hole_number' in resp_json['data'].keys() else 1

            gpu_num = 0
            for rtsp in resp_json['data']['cs_rtsp_list']:  # 启动多路视频监测分析
                # 根据任务参数生成日志文件（cs_mine_code-cs_workface_id-cs_workface_location-rtsp_number.log）
                log_name = 'result_log/{}-{}-{}-{}.log'.format(mine_code, work_id, work_location, rtsp['cs_channel_number'])

                # 生成分析指令
                cmd_training = 'nohup ./darknet detector demo {0} {1} {2} -i 0 -thresh 0.25 {9} -dont_show -http_port {10} -out_filename result_mp4/{3}-{4}-{5}-{6} -gpus {7} > {8} &'.format(
                    data_path, cfg_path, weight_path, mine_code, work_id, work_location, rtsp['cs_channel_number'], gpu_num, log_name, rtsp['cs_rtsp'], ports[gpu_num])

                print(cmd_training)
                subprocess.Popen(cmd_training, shell=True)

                upload_status({'name': '{}-{}-{}-{}'.format(mine_code, work_id, work_location, rtsp['cs_channel_number']), 'value': {'result': '检测程序启动成功', 'date': datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}})
                time.sleep(6)

                # 开线程分析结果日志并启动直播服务
                Thread(target=parser_log, args=(mine_code, work_id, work_location, pole_length, rtsp['cs_channel_number'])).start()
                subprocess.Popen('nohup ./enlive_mul {0} {1} {2} {3} {4}&'.format(mine_code, work_id, work_location, rtsp['cs_channel_number'], ports[gpu_num]), shell=True)
                upload_status({'name': '{}-{}-{}-{}'.format(mine_code, work_id, work_location, rtsp['cs_channel_number']), 'value': {'result': '检测程序启动成功，直播服务启动成功', 'date': datetime.strftime(datetime.now(),
                                                                                                                                                                                              "%Y-%m-%d %H:%M:%S")}})
                gpu_num += 1
        time.sleep(3)

