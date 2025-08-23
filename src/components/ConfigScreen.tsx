import React from 'react';
import { Bot, Calendar, Clock, Link } from 'lucide-react';
import { MeetingConfig } from '../types';
import DateTimePicker from './DateTimePicker';

interface ConfigScreenProps {
  config: MeetingConfig;
  setConfig: (config: MeetingConfig) => void;
  onSubmit: () => void;
  loading: boolean;
  error: string | null;
  isBotInMeeting?: boolean; // New prop to disable button when bot is in meeting
}

const ConfigScreen: React.FC<ConfigScreenProps> = ({
  config,
  setConfig,
  onSubmit,
  loading,
  error,
  isBotInMeeting = false
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (config.meeting_url && config.bot_name) {
      onSubmit();
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <Bot className="w-8 h-8 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Create New Bot</h2>
          <p className="text-gray-600">
            Configure your meeting bot to join and record meetings
          </p>
        </div>



        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Meeting URL */}
          <div>
            <label htmlFor="meeting_url" className="block text-sm font-medium text-gray-700 mb-2">
              Meeting URL
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Link className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="url"
                id="meeting_url"
                value={config.meeting_url}
                onChange={(e) => setConfig({ ...config, meeting_url: e.target.value })}
                placeholder="https://zoom.us/j/123456789"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter the meeting URL you want the bot to join
            </p>
          </div>

          {/* Bot Name */}
          <div>
            <label htmlFor="bot_name" className="block text-sm font-medium text-gray-700 mb-2">
              Bot Name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Bot className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                id="bot_name"
                value={config.bot_name}
                onChange={(e) => setConfig({ ...config, bot_name: e.target.value })}
                placeholder="Meeting Assistant"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Choose a name for your bot (will appear in meeting participants)
            </p>
          </div>

          {/* Webhook Base URL - CRITICAL FOR DEMO */}
          <div>
            <label htmlFor="webhook_base_url" className="block text-sm font-medium text-gray-700 mb-2">
              Webhook Base URL <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded font-bold">CRITICAL</span>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Link className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="url"
                id="webhook_base_url"
                value={config.webhook_base_url || ''}
                onChange={(e) => setConfig({ ...config, webhook_base_url: e.target.value })}
                placeholder="https://your-ngrok-url.ngrok-free.app"
                className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
            <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700 font-medium">
                ⚠️ <strong>CRITICAL:</strong> This field is required for the demo to work!
              </p>
              <p className="text-sm text-red-600 mt-1">
                Without webhooks, we cannot receive bot status updates from Attendee. 
                Use <code className="bg-red-100 px-1 rounded">https://your-ngrok-url.ngrok-free.app</code> as an example.
              </p>
            </div>
          </div>

          {/* Join Time */}
          <div>
            <label htmlFor="join_time" className="block text-sm font-medium text-gray-700 mb-2">
              Join Time (Optional)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Clock className="h-5 w-5 text-gray-400" />
              </div>
              <DateTimePicker
                value={config.join_at}
                onChange={(date) => setConfig({ ...config, join_at: date })}
                placeholder="Select join time (optional)"
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              When should the bot join the meeting? Leave empty to join immediately
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="pt-4">
            <button
              type="submit"
              disabled={loading || !config.meeting_url || !config.bot_name || !config.webhook_base_url}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Creating Bot...
                </>
              ) : (
                <>
                  <Bot className="w-4 h-4" />
                  Create Bot
                </>
              )}
            </button>
          </div>
        </form>

        {/* Help Text */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-900 mb-2">How it works</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• The bot will join your meeting at the specified time</li>
            <li>• It will record audio and generate transcripts</li>
            <li>• After the meeting, you'll get AI-powered insights and analysis</li>
            <li>• You can view real-time status updates in the dashboard</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ConfigScreen; 