import React, { useEffect, useState } from 'react';
import { Layout, Card, Row, Col, Button, Table, Tag, Space, Modal, Form, Input, Select, message } from 'antd';
import {
  RobotOutlined,
  ThunderboltOutlined,
  DisconnectOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useRobotStore } from '../store/robotStore';
import { RobotType, RobotStatus, type RobotConfig } from '../types/robot';

const { Header, Content } = Layout;
const { Option } = Select;

const statusColors: Record<RobotStatus, string> = {
  [RobotStatus.DISCONNECTED]: 'default',
  [RobotStatus.CONNECTED]: 'processing',
  [RobotStatus.READY]: 'success',
  [RobotStatus.CALIBRATING]: 'warning',
  [RobotStatus.ERROR]: 'error',
};

const statusLabels: Record<RobotStatus, string> = {
  [RobotStatus.DISCONNECTED]: '未连接',
  [RobotStatus.CONNECTED]: '已连接',
  [RobotStatus.READY]: '就绪',
  [RobotStatus.CALIBRATING]: '校准中',
  [RobotStatus.ERROR]: '错误',
};

export const Dashboard: React.FC = () => {
  const { robots, fetchRobots, addRobot, connectRobot, disconnectRobot, deleteRobot } = useRobotStore();
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchRobots();
    const interval = setInterval(fetchRobots, 5000);
    return () => clearInterval(interval);
  }, [fetchRobots]);

  const handleAddRobot = async (values: RobotConfig) => {
    try {
      await addRobot(values);
      message.success('机械臂添加成功');
      setAddModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('添加失败');
    }
  };

  const handleConnect = async (robotId: string) => {
    try {
      await connectRobot(robotId);
      message.success('连接成功');
    } catch (error) {
      message.error('连接失败');
    }
  };

  const handleDisconnect = async (robotId: string) => {
    try {
      await disconnectRobot(robotId);
      message.success('已断开连接');
    } catch (error) {
      message.error('断开失败');
    }
  };

  const handleDelete = (robotId: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个机械臂吗？',
      onOk: async () => {
        try {
          await deleteRobot(robotId);
          message.success('删除成功');
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const robotList = Object.values(robots);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '昵称',
      dataIndex: 'nickname',
      key: 'nickname',
      render: (text: string, record: any) => text || record.id,
    },
    {
      title: '类型',
      dataIndex: 'robot_type',
      key: 'robot_type',
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: RobotStatus) => (
        <Tag color={statusColors[status]}>{statusLabels[status]}</Tag>
      ),
    },
    {
      title: '校准状态',
      dataIndex: 'is_calibrated',
      key: 'is_calibrated',
      render: (calibrated: boolean) => (
        <Tag color={calibrated ? 'green' : 'orange'}>
          {calibrated ? '已校准' : '未校准'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          {record.status === RobotStatus.DISCONNECTED ? (
            <Button
              type="primary"
              size="small"
              icon={<ThunderboltOutlined />}
              onClick={() => handleConnect(record.id)}
            >
              连接
            </Button>
          ) : (
            <Button
              size="small"
              icon={<DisconnectOutlined />}
              onClick={() => handleDisconnect(record.id)}
            >
              断开
            </Button>
          )}
          <Button
            size="small"
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 20px', display: 'flex', alignItems: 'center' }}>
        <RobotOutlined style={{ fontSize: 24, color: 'white', marginRight: 16 }} />
        <h1 style={{ color: 'white', margin: 0 }}>LeRobot 机械臂调试平台</h1>
      </Header>

      <Content style={{ padding: '24px' }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card
              title="机械臂列表"
              extra={
                <Space>
                  <Button icon={<ReloadOutlined />} onClick={() => fetchRobots()}>
                    刷新
                  </Button>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setAddModalVisible(true)}
                  >
                    添加机械臂
                  </Button>
                </Space>
              }
            >
              <Table
                dataSource={robotList}
                columns={columns}
                rowKey="id"
                pagination={false}
              />
            </Card>
          </Col>
        </Row>

        <Modal
          title="添加机械臂"
          open={addModalVisible}
          onCancel={() => setAddModalVisible(false)}
          footer={null}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleAddRobot}
          >
            <Form.Item
              label="机械臂 ID"
              name="id"
              rules={[{ required: true, message: '请输入机械臂 ID' }]}
            >
              <Input placeholder="例如: robot1" />
            </Form.Item>

            <Form.Item
              label="机械臂类型"
              name="robot_type"
              rules={[{ required: true, message: '请选择机械臂类型' }]}
            >
              <Select placeholder="选择类型">
                <Option value={RobotType.SO100_FOLLOWER}>SO100 Follower</Option>
                <Option value={RobotType.SO101_FOLLOWER}>SO101 Follower</Option>
                <Option value={RobotType.KOCH_FOLLOWER}>Koch Follower</Option>
                <Option value={RobotType.LEKIWI}>LeKiwi</Option>
              </Select>
            </Form.Item>

            <Form.Item
              label="串口"
              name="port"
              rules={[{ required: true, message: '请输入串口路径' }]}
            >
              <Input placeholder="例如: /dev/ttyUSB0" />
            </Form.Item>

            <Form.Item label="昵称（可选）" name="nickname">
              <Input placeholder="给机械臂起个名字" />
            </Form.Item>

            <Form.Item label="备注（可选）" name="notes">
              <Input.TextArea rows={3} placeholder="添加备注信息" />
            </Form.Item>

            <Form.Item>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button onClick={() => setAddModalVisible(false)}>取消</Button>
                <Button type="primary" htmlType="submit">
                  添加
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </Content>
    </Layout>
  );
};
