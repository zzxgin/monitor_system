"""
监控数据采集客户端
"""

import psutil
import requests
import time
import sys
import os
import socket


class MonitorClient:
    def __init__(self, api_url, api_key=None, collect_interval=30, ip_address=None):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.collect_interval = collect_interval
        self.ip_address = ip_address or self._get_local_ip()
        self.running = False

        print(f"服务器IP: {self.ip_address}")
        self._test_connection()

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _test_connection(self):
        try:
            base_url = self.api_url.replace('/api', '')
            response = requests.get(f"{base_url}/home", timeout=5)
            if response.status_code == 200:
                print("API连接成功")
            else:
                print(f"API响应异常: {response.status_code}")
        except Exception as e:
            print(f"API连接失败: {e}")
            sys.exit(1)

    def collect_cpu(self):
        try:
            return round(psutil.cpu_percent(interval=1), 2)
        except:
            return None

    def collect_memory(self):
        try:
            return round(psutil.virtual_memory().percent, 2)
        except:
            return None

    def collect_disk(self):
        try:
            path = 'C:\\' if os.name == 'nt' else '/'
            disk = psutil.disk_usage(path)
            return round((disk.used / disk.total) * 100, 2)
        except:
            return None

    def send_data(self, metrics):
        if not metrics:
            return False

        data = {
            "metrics": metrics,
            "ip_address": self.ip_address
        }

        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['X-API-Key'] = self.api_key

            response = requests.post(
                f"{self.api_url}/monitor/data",
                json=data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"数据发送成功: {list(metrics.keys())}")
                    return True
                else:
                    print(f"数据发送失败: {result.get('message')}")
                    return False
            else:
                print(f"数据发送失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"数据发送异常: {e}")
            return False

    def collect_and_send(self):
        metrics = {}

        cpu_value = self.collect_cpu()
        if cpu_value is not None:
            metrics["cpu"] = cpu_value

        memory_value = self.collect_memory()
        if memory_value is not None:
            metrics["memory"] = memory_value

        disk_value = self.collect_disk()
        if disk_value is not None:
            metrics["disk"] = disk_value

        if metrics:
            self.send_data(metrics)

    def run(self):
        print(f"监控客户端启动 - 服务器IP: {self.ip_address}, 采集间隔: {self.collect_interval}秒")
        self.running = True

        try:
            while self.running:
                start_time = time.time()
                self.collect_and_send()

                elapsed_time = time.time() - start_time
                sleep_time = max(0, self.collect_interval - elapsed_time)

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    print("采集耗时超过间隔时间，立即进行下次采集")

        except KeyboardInterrupt:
            print("收到停止信号，正在关闭监控客户端...")
            self.running = False
        except Exception as e:
            print(f"监控客户端运行异常: {e}")
            self.running = False


def main():
    API_URL = "http://192.168.10.161:5000/api"
    API_KEY = "dev-api-key-123456"
    COLLECT_INTERVAL = 30
    IP_ADDRESS = None

    if len(sys.argv) > 1:
        API_URL = sys.argv[1]
    if len(sys.argv) > 2:
        API_KEY = sys.argv[2]
    if len(sys.argv) > 3:
        COLLECT_INTERVAL = int(sys.argv[3])
    if len(sys.argv) > 4:
        IP_ADDRESS = sys.argv[4]

    client = MonitorClient(API_URL, API_KEY, COLLECT_INTERVAL, IP_ADDRESS)
    client.run()


if __name__ == "__main__":
    main()
