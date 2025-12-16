import { create } from 'zustand';
import type { RobotState, RobotConfig } from '../types/robot';
import { robotApi } from '../services/robotApi';

interface RobotStore {
  robots: Record<string, RobotState>;
  selectedRobotId: string | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchRobots: () => Promise<void>;
  addRobot: (config: RobotConfig) => Promise<void>;
  connectRobot: (robotId: string) => Promise<void>;
  disconnectRobot: (robotId: string) => Promise<void>;
  updateRobot: (robotId: string, data: Partial<RobotConfig>) => Promise<void>;
  deleteRobot: (robotId: string) => Promise<void>;
  selectRobot: (robotId: string) => void;
}

export const useRobotStore = create<RobotStore>((set, get) => ({
  robots: {},
  selectedRobotId: null,
  loading: false,
  error: null,

  fetchRobots: async () => {
    set({ loading: true, error: null });
    try {
      const robots = await robotApi.listRobots();
      set({
        robots: robots.reduce((acc, r) => ({ ...acc, [r.id]: r }), {}),
        loading: false
      });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  addRobot: async (config) => {
    set({ loading: true, error: null });
    try {
      const robot = await robotApi.createRobot(config);
      set(state => ({
        robots: { ...state.robots, [robot.id]: robot },
        loading: false
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  connectRobot: async (robotId) => {
    try {
      await robotApi.connectRobot(robotId);
      await get().fetchRobots();
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  disconnectRobot: async (robotId) => {
    try {
      await robotApi.disconnectRobot(robotId);
      await get().fetchRobots();
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  updateRobot: async (robotId, data) => {
    try {
      await robotApi.updateRobot(robotId, data);
      await get().fetchRobots();
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  deleteRobot: async (robotId) => {
    try {
      await robotApi.deleteRobot(robotId);
      set(state => {
        const newRobots = { ...state.robots };
        delete newRobots[robotId];
        return { robots: newRobots };
      });
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  selectRobot: (robotId) => set({ selectedRobotId: robotId })
}));
