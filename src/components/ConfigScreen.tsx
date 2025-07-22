import React from 'react';
import { Settings, Send, RefreshCw } from 'lucide-react';
import { MeetingConfig } from '../types';

interface ConfigScreenProps {
  config: MeetingConfig;
  setConfig: (config: MeetingConfig) => void;
  onSubmit: () => void;
  loading: boolean;
  error: string | null;
}

const ConfigScreen: React.FC<ConfigScreenProps> = ({
  config,
  setConfig,
  onSubmit,
  loading,
  error
}) => {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg p-8 shadow-lg border border-gray-200">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-6 h-6 text-primary-600" />
          <h2 className="text-2xl font-bold text-black">Bot Configuration</h2>
        </div>
        
        <div className="space-y-6">
          <div>
            <label htmlFor="meeting_url" className="block text-sm font-medium text-gray-700 mb-2">
              Meeting URL
            </label>
            <input
              type="url"
              id="meeting_url"
              value={config.meeting_url}
              onChange={(e) => setConfig({ ...config, meeting_url: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-black placeholder-gray-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none transition-colors"
              placeholder="https://meet.google.com/abc-def-ghi"
              required
            />
          </div>

          <div>
            <label htmlFor="bot_name" className="block text-sm font-medium text-gray-700 mb-2">
              Bot Name
            </label>
            <input
              type="text"
              id="bot_name"
              value={config.bot_name}
              onChange={(e) => setConfig({ ...config, bot_name: e.target.value })}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-black placeholder-gray-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none transition-colors"
              placeholder="My Meeting Bot"
              required
            />
          </div>

          <div>
            <label htmlFor="join_at" className="block text-sm font-medium text-gray-700 mb-2">
              Join At (Optional)
            </label>
            <input
              type="datetime-local"
              id="join_at"
              value={config.join_at || ''}
              onChange={(e) => setConfig({ ...config, join_at: e.target.value || undefined })}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-black placeholder-gray-500 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:outline-none transition-colors"
            />
            <p className="text-sm text-gray-500 mt-1">
              Leave empty to join immediately when created
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <button
            type="button"
            onClick={onSubmit}
            disabled={loading}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
          >
            {loading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            {loading ? 'Creating Bot...' : 'Create Bot'}
          </button>

          {loading && (
            <div className="text-center">
              <p className="text-sm text-gray-600">
                Bot creation takes 30-60 seconds. Please wait...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigScreen; 