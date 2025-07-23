import React from 'react';
import { Bot, Settings, BarChart3, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { MeetingBot } from '../types';

interface SidebarProps {
  bots: MeetingBot[];
  selectedBotId: number | null;
  onBotSelect: (botId: number) => void;
  onNewBot: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  bots,
  selectedBotId,
  onBotSelect,
  onNewBot
}) => {
  const getStatusIcon = (status: MeetingBot['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'started':
        return <Settings className="w-4 h-4 text-primary-600" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Bot className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: MeetingBot['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'started':
        return 'bg-primary-100 text-primary-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: MeetingBot['status']) => {
    switch (status) {
      case 'pending':
        return 'Creating...';
      case 'started':
        return 'In Meeting';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return status;
    }
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 h-screen overflow-y-auto">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bot className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-bold text-black">Meeting Bots</h2>
        </div>

        <button
          type="button"
          onClick={onNewBot}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 mb-6 cursor-pointer"
        >
          <Bot className="w-4 h-4" />
          New Bot
        </button>

        <div className="space-y-2">
          {bots.map((bot) => (
            <div
              key={bot.id}
              onClick={() => onBotSelect(bot.id)}
              className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 ${
                selectedBotId === bot.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getStatusIcon(bot.status)}
                  <h3 className="font-medium text-black truncate">{bot.meeting_metadata.bot_name}</h3>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
                  {getStatusText(bot.status)}
                </span>
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <p>Created: {new Date(bot.created_at).toLocaleDateString()}</p>
                <p className="truncate text-xs">{bot.meeting_url}</p>
                {bot.meeting_metadata.join_at && (
                  <p className="text-xs">Joins: {new Date(bot.meeting_metadata.join_at).toLocaleString()}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        {bots.length === 0 && (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No meeting bots yet</p>
            <p className="text-sm text-gray-500">Create your first bot to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar; 