import React from 'react';
import { Bot, Plus, Trash2, Clock, Play, CheckCircle, XCircle } from 'lucide-react';
import { MeetingBot } from '../types';

interface SidebarProps {
  bots: MeetingBot[];
  selectedBotId: number | null;
  onBotSelect: (botId: number) => void;
  onNewBot: () => void;
  onDeleteBot: (botId: number) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  bots,
  selectedBotId,
  onBotSelect,
  onNewBot,
  onDeleteBot
}) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'STARTED':
        return <Play className="w-4 h-4 text-blue-500" />;
      case 'COMPLETED':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Bot className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING':
        return 'border-yellow-200 bg-yellow-50';
      case 'STARTED':
        return 'border-blue-200 bg-blue-50';
      case 'COMPLETED':
        return 'border-green-200 bg-green-50';
      case 'FAILED':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Bots</h2>
          <button
            onClick={onNewBot}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
            title="Create new bot"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
        <p className="text-sm text-gray-600">
          Manage your meeting bots
        </p>
      </div>

      {/* Bot List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {bots.length === 0 ? (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">No bots yet</p>
            <button
              onClick={onNewBot}
              className="mt-3 text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              Create your first bot
            </button>
          </div>
        ) : (
          bots.map((bot) => (
            <div
              key={bot.id}
              className={`relative group cursor-pointer rounded-lg border p-4 transition-all duration-200 hover:shadow-md ${
                selectedBotId === bot.id
                  ? 'ring-2 ring-blue-500 border-blue-300 bg-blue-50'
                  : getStatusColor(bot.status)
              }`}
              onClick={() => onBotSelect(bot.id)}
            >
              {/* Status Icon */}
              <div className="flex items-start justify-between mb-2">
                {getStatusIcon(bot.status)}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteBot(bot.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-all duration-200"
                  title="Delete bot"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Bot Info */}
              <div className="space-y-1">
                <h3 className="font-medium text-gray-900 truncate">
                  {bot.meeting_metadata.bot_name}
                </h3>
                <p className="text-xs text-gray-600 truncate">
                  {bot.meeting_url}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span className="capitalize">
                    {bot.status.toLowerCase()}
                  </span>
                  <span>
                    {new Date(bot.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-center">
          <p className="text-xs text-gray-500">
            {bots.length} bot{bots.length !== 1 ? 's' : ''} total
          </p>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 