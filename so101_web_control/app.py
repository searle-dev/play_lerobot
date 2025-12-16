#!/usr/bin/env python3
"""
SO101 机械臂网页控制服务器
基于 Flask + Socket.IO 实现实时控制
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'so101-web-control-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
robot = None
robot_connected = False
current_port = "/dev/tty.usbmodem5A7C1163141"  # 默认端口

# 目标位置（用于 P 控制）
target_positions = {
    'shoulder_pan': 0.0,
    'shoulder_lift': 0.0,
    'elbow_flex': 0.0,
    'wrist_flex': 0.0,
    'wrist_roll': 0.0,
    'gripper': 50.0  # 夹爪默认中间位置
}

# 控制参数
control_params = {
    'step_size': 5.0,  # 每次按键移动的角度
    'gripper_step': 10.0,  # 夹爪步进
    'control_freq': 50,  # 控制频率 Hz
    'kp': 0.5  # 比例增益
}

def init_robot():
    """初始化机器人连接"""
    global robot, robot_connected
    try:
        from lerobot.robots.so100_follower import SO100Follower, SO100FollowerConfig
        
        logger.info(f"连接机器人，端口: {current_port}")
        robot_config = SO100FollowerConfig(port=current_port)
        robot = SO100Follower(robot_config)
        robot.connect()
        robot_connected = True
        
        # 读取初始位置
        obs = robot.get_observation()
        for key, value in obs.items():
            if key.endswith('.pos'):
                motor_name = key.replace('.pos', '')
                if motor_name in target_positions:
                    target_positions[motor_name] = float(value)
        
        logger.info("✅ 机器人连接成功")
        return True
    except Exception as e:
        logger.error(f"❌ 机器人连接失败: {e}")
        robot_connected = False
        return False

def control_loop():
    """P 控制循环"""
    global robot, robot_connected, target_positions
    
    control_period = 1.0 / control_params['control_freq']
    
    while True:
        if robot_connected and robot:
            try:
                # 获取当前位置
                current_obs = robot.get_observation()
                current_positions = {}
                for key, value in current_obs.items():
                    if key.endswith('.pos'):
                        motor_name = key.replace('.pos', '')
                        current_positions[motor_name] = float(value)
                
                # P 控制计算
                robot_action = {}
                for joint_name, target_pos in target_positions.items():
                    if joint_name in current_positions:
                        current_pos = current_positions[joint_name]
                        error = target_pos - current_pos
                        
                        # P 控制
                        control_output = control_params['kp'] * error
                        new_position = current_pos + control_output
                        robot_action[f"{joint_name}.pos"] = new_position
                
                # 发送动作
                if robot_action:
                    robot.send_action(robot_action)
                
                # 发送状态更新到客户端
                socketio.emit('robot_state', {
                    'current': current_positions,
                    'target': target_positions,
                    'connected': True
                })
                
            except Exception as e:
                logger.error(f"控制循环错误: {e}")
                robot_connected = False
                socketio.emit('robot_state', {
                    'connected': False,
                    'error': str(e)
                })
        
        time.sleep(control_period)

# 启动控制线程
control_thread = threading.Thread(target=control_loop, daemon=True)
control_thread.start()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """获取机器人状态"""
    return jsonify({
        'connected': robot_connected,
        'port': current_port,
        'target_positions': target_positions,
        'control_params': control_params
    })

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info('客户端已连接')
    emit('connection_response', {
        'status': 'connected',
        'robot_connected': robot_connected
    })

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开"""
    logger.info('客户端已断开')

@socketio.on('connect_robot')
def handle_connect_robot(data):
    """连接机器人"""
    global current_port
    port = data.get('port', current_port)
    current_port = port
    
    success = init_robot()
    emit('robot_connection_result', {
        'success': success,
        'port': current_port,
        'connected': robot_connected
    })

@socketio.on('disconnect_robot')
def handle_disconnect_robot():
    """断开机器人"""
    global robot, robot_connected
    if robot:
        try:
            robot.disconnect()
            robot_connected = False
            emit('robot_connection_result', {
                'success': True,
                'connected': False
            })
        except Exception as e:
            emit('error', {'message': str(e)})

@socketio.on('key_press')
def handle_key_press(data):
    """处理按键"""
    key = data.get('key', '').lower()
    
    if not robot_connected:
        emit('error', {'message': '机器人未连接'})
        return
    
    step = control_params['step_size']
    gripper_step = control_params['gripper_step']
    
    # 按键映射
    key_mapping = {
        'q': ('shoulder_pan', -step),
        'a': ('shoulder_pan', step),
        'w': ('shoulder_lift', -step),
        's': ('shoulder_lift', step),
        'e': ('elbow_flex', -step),
        'd': ('elbow_flex', step),
        'r': ('wrist_flex', -step),
        'f': ('wrist_flex', step),
        't': ('wrist_roll', -step),
        'g': ('wrist_roll', step),
        'y': ('gripper', -gripper_step),
        'h': ('gripper', gripper_step),
    }
    
    if key in key_mapping:
        joint_name, delta = key_mapping[key]
        if joint_name in target_positions:
            old_pos = target_positions[joint_name]
            new_pos = old_pos + delta
            
            # 限制范围
            if joint_name == 'gripper':
                new_pos = max(0, min(100, new_pos))
            else:
                new_pos = max(-180, min(180, new_pos))
            
            target_positions[joint_name] = new_pos
            
            emit('position_update', {
                'joint': joint_name,
                'old': old_pos,
                'new': new_pos
            })
            
            logger.info(f"按键 {key}: {joint_name} {old_pos:.1f} -> {new_pos:.1f}")

@socketio.on('set_position')
def handle_set_position(data):
    """直接设置关节位置"""
    joint = data.get('joint')
    position = data.get('position')
    
    if joint in target_positions:
        target_positions[joint] = float(position)
        emit('position_update', {
            'joint': joint,
            'new': position
        })

@socketio.on('set_control_param')
def handle_set_control_param(data):
    """设置控制参数"""
    param = data.get('param')
    value = data.get('value')
    
    if param in control_params:
        control_params[param] = float(value)
        emit('param_update', {
            'param': param,
            'value': value
        })

@socketio.on('reset_positions')
def handle_reset_positions():
    """重置所有位置到零"""
    global target_positions
    for key in target_positions:
        if key == 'gripper':
            target_positions[key] = 50.0
        else:
            target_positions[key] = 0.0
    
    emit('positions_reset', {'positions': target_positions})

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("SO101 机械臂网页控制服务器")
    logger.info("="*60)
    logger.info("访问地址: http://localhost:5000")
    logger.info("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
