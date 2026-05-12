import asyncio
import websockets
import json
import os
import sys
import threading
import http.server
import socketserver
import subprocess
import logging
import glob
import serial
import binascii
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logging.getLogger().setLevel(logging.ERROR)

# 配置文件路径
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# 加载配置
def load_config():
    encoding = 'utf-8'
    default_config = {
        'WEBSOCKET': {'HOST': '0.0.0.0', 'PORT': 8765},
        'HTTP': {'PORT': 8001},
        'SERIAL': {'PORT': '/dev/ttyUSB0', 'MODE': 'tom_modem'}
    }
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding=encoding) as file:
            json.dump(default_config, file, indent=4, ensure_ascii=False)
        return default_config
    with open(config_path, 'r', encoding=encoding) as file:
        config = json.load(file)
    for key in default_config:
        if key not in config:
            config[key] = default_config[key]
        else:
            for sub_key in default_config[key]:
                if sub_key not in config[key]:
                    config[key][sub_key] = default_config[key][sub_key]
    return config

config = load_config()
serial_mode = config['SERIAL']['MODE']
serial_port_config = config['SERIAL']['PORT']
tom_modem_tool = 'tom_modem'  # 用于与调制解调器通信的工具
feature = config['SERIAL']['FEATURE']
tom_arg=' ' # 不使用UBUS特性，默认将参数设为空
if(feature == 'UBUS'):
    tom_arg = '-u'


# 自动检测串口
def detect_serial_port():
    import time
    import serial.tools.list_ports
    ports = [port.device for port in serial.tools.list_ports.comports()]
    for port in ports:
        try:
            if serial_mode == 'direct':
                ser = serial.Serial(port, 115200, timeout=2)
                ser.reset_input_buffer()
                ser.write(b'AT\r')
                time.sleep(0.5)
                response = ser.read_all().decode(errors='ignore')
                ser.close()
                if 'AT' in response:
                    logging.info(f"[direct模式] 检测到AT端口: {port}")
                    return port
            else:
                result = subprocess.run([tom_modem_tool, port, '-c', 'AT',tom_arg], capture_output=True, timeout=2)
                output = result.stdout.decode(errors='ignore')
                if 'AT' in output:
                    logging.info(f"检测到AT端口: {port}")
                    return port
        except Exception as e:
            logging.info(f"检测端口{port}失败: {e}")
            continue
    return None

# 确定串口
if serial_port_config == 'auto':
    detected_port = detect_serial_port()
else:
    detected_port = serial_port_config

if not detected_port:
    print('未检测到AT端口，程序退出')
    sys.exit(1)

# 全局变量
connected_clients = set()  # 存储连接的WebSocket客户端
serial_lock = asyncio.Lock()  # 串口操作锁

# 发送短信的函数
async def send_sms(args):
    if len(args) < 4:
        logging.error('参数不足，格式应为 SEND_SMS,短信中心号码,手机号,"短信内容"')
        return '参数不足，格式应为 SEND_SMS,手机号,"短信内容"'
    sms_center = args[1].strip()
    phone_number = args[2].strip()
    message_content = args[3].strip('"')
    logging.info(f"准备发送短信: 手机号={phone_number}, 内容={message_content}")

    def format_number(number):
        number = re.sub(r'\D', '', number)
        if len(number) % 2 != 0:
            number += 'F'
        formatted = ''
        for i in range(0, len(number), 2):
            formatted += number[i+1] + number[i]
        return formatted

    def encode_message(text):
        return binascii.hexlify(text.encode('utf-16-be')).decode().upper()

    formatted_sms_center = format_number(sms_center)
    sms_center_length = int(len(formatted_sms_center) / 2 + 1)
    sms_center_header = f"{sms_center_length:02X}91{formatted_sms_center}"
    message_type = '11'
    validity_period = '00'
    formatted_phone_number = re.sub(r'\D', '', phone_number)
    phone_number_header = f"{len(formatted_phone_number):02X}91{format_number(formatted_phone_number)}"
    protocol_identifier = '00'
    data_coding_scheme = '08'
    encoded_message = encode_message(message_content)
    message_length = f"{len(encoded_message) // 2:02X}"
    message_body = 'a7' + message_length + encoded_message
    pdu_data = message_type + validity_period + phone_number_header + protocol_identifier + data_coding_scheme + message_body
    pdu = sms_center_header + pdu_data
    pdu_length = len(pdu_data) // 2
    logging.info(f"PDU编码: {pdu}")
    logging.info(f"AT+CMGS长度: {pdu_length}")

    try:
        if serial_mode == 'direct':
            async with serial_lock:
                try:
                    with serial.Serial(detected_port, 115200, timeout=5) as ser:
                        logging.info(f"[direct模式] 新建串口: {detected_port}")
                        ser.write(b'AT+CMGF=0\r')
                        logging.info("发送: AT+CMGF=0")
                        await asyncio.sleep(0.5)
                        response = ser.read_all().decode(errors='ignore')
                        logging.info(f"AT+CMGF=0 返回: {response}")
                        if 'OK' not in response:
                            return 'AT+CMGF=0 未返回OK'
                        ser.write(f"AT+CMGS={pdu_length}\r".encode())
                        logging.info(f"发送: AT+CMGS={pdu_length}")
                        data = b''
                        for _ in range(30):
                            await asyncio.sleep(0.1)
                            chunk = ser.read_all()
                            if chunk:
                                logging.info(f"收到串口数据: {chunk}")
                            data += chunk
                            if b'>' in data:
                                logging.info("收到 > 提示符，准备发送PDU数据")
                                break
                        else:
                            logging.error("未收到 > 提示符，模块无响应")
                            return "未收到 > 提示符，模块无响应"
                        ser.write(pdu.encode() + b'\x1a')
                        logging.info(f"发送PDU+Ctrl+Z: {pdu}")
                        data = b''
                        for _ in range(100):
                            await asyncio.sleep(0.1)
                            chunk = ser.read_all()
                            if chunk:
                                logging.info(f"收到串口数据: {chunk}")
                            data += chunk
                            decoded_data = data.decode(errors='ignore')
                            if '+CMGS:' in decoded_data:
                                logging.info(f"串口返回: {decoded_data}")
                                logging.info("短信发送成功")
                                return 'OK'
                            elif '+CMS ERROR:' in decoded_data:
                                logging.info(f"串口返回: {decoded_data}")
                                logging.error(f"发送失败: {decoded_data}")
                                return f"SEND_FAIL: {decoded_data}"
                        logging.warning(f"未知返回: {decoded_data}")
                        return f"ERROR: {decoded_data}"
                except Exception as e:
                    logging.exception('串口异常')
                    return f"串口异常: {e}"
        else:
            ser = serial.Serial(detected_port, 115200, timeout=5)
            logging.info(f"打开串口: {detected_port}")
            ser.write(b'AT+CMGF=0\r')
            logging.info("发送: AT+CMGF=0")
            await asyncio.sleep(0.5)
            response = ser.read_all().decode(errors='ignore')
            logging.info(f"AT+CMGF=0 返回: {response}")
            if 'OK' not in response:
                ser.close()
                return 'AT+CMGF=0 未返回OK'
            ser.write(f"AT+CMGS={pdu_length}\r".encode())
            logging.info(f"发送: AT+CMGS={pdu_length}")
            data = b''
            for _ in range(30):
                await asyncio.sleep(0.1)
                chunk = ser.read_all()
                if chunk:
                    logging.info(f"收到串口数据: {chunk}")
                data += chunk
                if b'>' in data:
                    logging.info("收到 > 提示符，准备发送PDU数据")
                    break
            else:
                ser.close()
                logging.error("未收到 > 提示符，模块无响应")
                return "未收到 > 提示符，模块无响应"
            ser.write(pdu.encode() + b'\x1a')
            logging.info(f"发送PDU+Ctrl+Z: {pdu}")
            data = b''
            for _ in range(100):
                await asyncio.sleep(0.1)
                chunk = ser.read_all()
                if chunk:
                    logging.info(f"收到串口数据: {chunk}")
                data += chunk
                decoded_data = data.decode(errors='ignore')
                if '+CMGS:' in decoded_data:
                    logging.info(f"串口返回: {decoded_data}")
                    ser.close()
                    logging.info("短信发送成功")
                    return 'OK'
                elif '+CMS ERROR:' in decoded_data:
                    logging.info(f"串口返回: {decoded_data}")
                    ser.close()
                    logging.error(f"发送失败: {decoded_data}")
                    return f"SEND_FAIL: {decoded_data}"
            ser.close()
            logging.warning(f"未知返回: {decoded_data}")
            return f"ERROR: {decoded_data}"
    except Exception as e:
        logging.exception('串口异常')
        return f"串口异常: {e}"

# WebSocket处理器
async def websocket_handler(websocket, path=None):
    print('WebSocket处理器已加载', websocket, path)
    connected_clients.add(websocket)
    print(f"WebSocket客户端已连接: {websocket.remote_address}")
    try:
        async for message in websocket:
            command_id = None
            command = None
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    if isinstance(data, dict) and 'cmd' in data:
                        command = data['cmd']
                        command_id = data.get('id')
                    else:
                        command = message.strip()
                except Exception:
                    command = message.strip()
            else:
                await websocket.send(json.dumps({'error': '不支持二进制消息'}, ensure_ascii=False))
                continue

            if not command:
                continue

            if command.startswith('SEND_SMS'):
                parts = command.split(',', 3)
                result = await send_sms(parts)
                if command_id is not None:
                    response = {'id': command_id, 'result': result}
                    await websocket.send(json.dumps(response, ensure_ascii=False))
                else:
                    await websocket.send(result)
                continue

            if not command.endswith('\r') and not command.endswith('\n'):
                command += '\r'

            if serial_mode == 'direct':
                async with serial_lock:
                    try:
                        with serial.Serial(detected_port, 115200, timeout=5) as ser:
                            ser.reset_input_buffer()
                            ser.reset_output_buffer()
                            if not command.endswith('\r\n'):
                                command = command.rstrip('\r\n') + '\r\n'
                            ser.write(command.encode())
                            response_data = b''
                            for _ in range(50):
                                await asyncio.sleep(0.1)
                                chunk = ser.read_all()
                                if chunk:
                                    response_data += chunk
                                decoded_response = response_data.decode(errors='ignore').strip()
                                if 'OK' in decoded_response or 'ERROR' in decoded_response or 'BUSY' in decoded_response:
                                    break
                            decoded_response = response_data.decode(errors='ignore').strip()
                            logging.info(f"串口返回: {decoded_response}")
                            if command_id is not None:
                                response = {'id': command_id, 'result': decoded_response}
                                await websocket.send(json.dumps(response, ensure_ascii=False))
                            else:
                                await websocket.send(decoded_response)
                    except Exception as e:
                        logging.exception('串口命令异常')
                        if command_id is not None:
                            response = {'id': command_id, 'result': str(e)}
                            await websocket.send(json.dumps(response, ensure_ascii=False))
                        else:
                            await websocket.send(str(e))
                continue
            else:
                try:
                    logging.info(f"调用tom_modem参数: tom_modem {detected_port} -c '{command}'")
                    process = await asyncio.create_subprocess_exec(
                        tom_modem_tool, detected_port, '-c', command, '-u',
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    try:
                        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
                    except asyncio.TimeoutError:
                        logging.error('命令执行超时')
                        if command_id is not None:
                            response = {'id': command_id, 'result': '命令执行超时'}
                            await websocket.send(json.dumps(response, ensure_ascii=False))
                        else:
                            await websocket.send('命令执行超时')
                        process.kill()
                        continue
                    output = stdout.decode(errors='ignore').strip()
                    error_output = stderr.decode(errors='ignore').strip()
                    logging.info(f"tom_modem标准输出: {output}")
                    logging.info(f"tom_modem标准错误: {error_output}")
                    if output:
                        logging.info(f"推送到前端: {output}")
                        if command_id is not None:
                            response = {'id': command_id, 'result': output}
                            await websocket.send(json.dumps(response, ensure_ascii=False))
                        else:
                            await websocket.send(output)
                    elif error_output:
                        logging.info(f"推送到前端: {error_output}")
                        if command_id is not None:
                            response = {'id': command_id, 'result': error_output}
                            await websocket.send(json.dumps(response, ensure_ascii=False))
                        else:
                            await websocket.send(error_output)
                    else:
                        logging.info('推送到前端: 无返回')
                        if command_id is not None:
                            response = {'id': command_id, 'result': '无返回'}
                            await websocket.send(json.dumps(response, ensure_ascii=False))
                        else:
                            await websocket.send('无返回')
                except Exception as e:
                    logging.exception('执行tom_modem命令异常')
                    if command_id is not None:
                        response = {'id': command_id, 'result': str(e)}
                        await websocket.send(json.dumps(response, ensure_ascii=False))
                    else:
                        await websocket.send(str(e))
    except Exception as e:
        print(f"WebSocket客户端断开: {e}")
    finally:
        connected_clients.discard(websocket)

# HTTP服务器函数
def start_http_server():
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
    os.chdir(web_dir)
    port = config['HTTP']['PORT'] if 'HTTP' in config and 'PORT' in config['HTTP'] else 8001
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(('', port), handler)
    print(f"HTTP 服务器已启动: http://0.0.0.0:{port}/")
    httpd.serve_forever()

# 启动HTTP服务器线程
http_thread = threading.Thread(target=start_http_server, daemon=True)
http_thread.start()

# 启动WebSocket服务器
async def start_websocket_server():
    server = await websockets.serve(websocket_handler, config['WEBSOCKET']['HOST'], config['WEBSOCKET']['PORT'])
    print(f"WebSocket服务器已启动: ws://{config['WEBSOCKET']['HOST']}:{config['WEBSOCKET']['PORT']}")
    await server.wait_closed()

# 主程序
if __name__ == '__main__':
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        except Exception as e:
            loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(start_websocket_server())
        except KeyboardInterrupt:
            print('\n正在关闭服务...')
        finally:
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
    except KeyboardInterrupt:
        print('主动停止监听短信')
    except Exception as e:
        print(f"程序启动错误: {e}")