import { api } from './api';
import type { RecordingMetadata } from '../types/recording';

export const recordingApi = {
  startRecording: async (robotId: string) => {
    return api.post(`/api/recording/${robotId}/start`);
  },

  stopRecording: async (recordingId: string, name: string) => {
    return api.post(`/api/recording/${recordingId}/stop`, null, { params: { name } });
  },

  listRecordings: async (robotId: string): Promise<RecordingMetadata[]> => {
    return api.get(`/api/recording/${robotId}`);
  },

  playback: async (recordingId: string, speed: number = 1.0) => {
    return api.post(`/api/recording/${recordingId}/playback`, null, { params: { speed } });
  },
};
