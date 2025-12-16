import { api } from './api';
import type { RobotConfig, RobotState, PortInfo, ScanResult } from '../types/robot';

export const robotApi = {
  // 端口扫描
  listPorts: async (): Promise<PortInfo[]> => {
    return api.get('/api/ports');
  },

  scanPort: async (port: string): Promise<ScanResult[]> => {
    return api.post('/api/ports/scan', null, { params: { port } });
  },

  // 机械臂管理
  listRobots: async (): Promise<RobotState[]> => {
    return api.get('/api/robots');
  },

  createRobot: async (config: RobotConfig): Promise<RobotState> => {
    return api.post('/api/robots', config);
  },

  getRobot: async (robotId: string): Promise<RobotState> => {
    return api.get(`/api/robots/${robotId}`);
  },

  updateRobot: async (robotId: string, data: Partial<RobotConfig>) => {
    return api.put(`/api/robots/${robotId}`, null, { params: data });
  },

  connectRobot: async (robotId: string, calibrate: boolean = false) => {
    return api.post(`/api/robots/${robotId}/connect`, null, { params: { calibrate } });
  },

  disconnectRobot: async (robotId: string) => {
    return api.post(`/api/robots/${robotId}/disconnect`);
  },

  getObservation: async (robotId: string) => {
    return api.get(`/api/robots/${robotId}/observation`);
  },

  deleteRobot: async (robotId: string) => {
    return api.delete(`/api/robots/${robotId}`);
  },
};
