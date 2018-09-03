# -*- coding:utf-8 -*-
import configparser
from datetime import datetime


class ResultParser(object):

    def get_chart_data(self):
        return self.wave_chart

    def get_video_data(self):
        return self.upload_mp4

    # hole_number 目前没用
    def __init__(self, fname, mine_code, workface_id, workface_loc, pole_length, rtsp_num):
        self.file_name = fname      # 日志名称
        self.upload_mp4 = []        # 待上传的mp4列表
        self.start_unload = False   # 是否卸管
        self.pole_length = pole_length  # 管长度
        self.rtsp_num = rtsp_num        # 视频通道编号
        self.wave_chart = {"start_time": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), "data": [], 'json':{}}        # 卸管图表数据
        conf = configparser.ConfigParser()  # 读取配置信息
        conf.read("config.cfg")
        self.api_server = conf.get('config', 'api_server')
        self.video_server = conf.get('config', 'video_server')

        self.item_model = {
            "cs_mine_code": mine_code,
            "cs_workface_id": workface_id,
            "cs_workface_location": int(workface_loc),
            "drilling": {
                "cs_drill_waveform": "",
                "cs_drill_num": 0,
                "cs_drill_live_url": '{}{}-{}-{}-{}/live.m3u8'.format(self.video_server, mine_code, workface_id, workface_loc, rtsp_num),
                "cs_drill_full_video": "{}mp4/{}-{}-{}-{}.mp4".format(self.video_server, mine_code, workface_id, workface_loc, rtsp_num),
                "cs_drill_code": '0',
                "drill": []
            }
        }

    def parser(self):
        """
            每次对日志文件进行全量分析
        :return:
        """
        with open(self.file_name) as f:
            end_file = False
            drill = {
                "cs_drill_serial_num": 0,
                "cs_drill_person_num": 0,
                "cs_drill_starttime": "",
                "cs_drill_endtime": "",
                "cs_drill_video": ""
            }
            self.wave_chart['data'] = []
            self.item_model['drilling']['drill'] = []

            for num, txt in enumerate(f):
                # 日志文件结束标记
                if 'output_complete_video_writer closed' in txt:
                    end_file = True
                # 开始卸钻标记
                if 's_time' in txt and ':' in txt:
                    self.start_unload = True
                    drill['cs_drill_starttime'] = txt.split('e:')[1].strip()
                if 'n_person' in txt and ':' in txt and not self.start_unload:
                    try:
                        p_num = int(txt.split(':')[1].strip())
                        drill['cs_drill_person_num'] = p_num if p_num > 0 else 1
                    except:
                        pass
                if 'n_tube_pre' in txt and ':' in txt and not self.start_unload and '%' not in txt:
                    try:
                        drill['cs_drill_serial_num'] = int(txt.split(':')[1].strip()) + 1
                    except:
                        drill['cs_drill_serial_num'] = len(self.item_model['drilling']['drill']) + 1

                    drill['cs_drill_video'] = "{}mp4/{}-{}-{}-{}-{}.mp4".format(
                        self.video_server,
                        self.item_model['cs_mine_code'],
                        self.item_model['cs_workface_id'],
                        self.item_model['cs_workface_location'],
                        self.rtsp_num,
                        drill['cs_drill_serial_num']
                    )
                if 'e_time' in txt and ':' in txt:
                    self.start_unload = False
                    if drill['cs_drill_video']:
                        self.upload_mp4.append(drill['cs_drill_video'].split('/')[-1])
                    drill['cs_drill_endtime'] = txt.split('e:')[1].strip()
                    self.item_model['drilling']['drill'].append(drill)
                    drill = {
                        "cs_drill_serial_num": 0,
                        "cs_drill_person_num": 0,
                        "cs_drill_starttime": "",
                        "cs_drill_endtime": "",
                        "cs_drill_video": ""
                    }

                # 每发现一个Objects将0 or 1 写入实时曲线数组
                if self.start_unload:
                    if 'Objects:' in txt:
                        self.wave_chart['data'].append(1)
                else:
                    if 'Objects:' in txt:
                        self.wave_chart['data'].append(0)

        self.item_model['drilling']['cs_drill_num'] = len(self.item_model['drilling']['drill'])
        self.wave_chart['json'] = self.item_model
        return self.item_model, end_file

