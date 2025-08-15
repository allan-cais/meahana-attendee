import React from 'react';
import { Bot, Settings, BarChart3, Clock, CheckCircle, AlertCircle, Trash2, Users, Calendar, Link } from 'lucide-react';
import { MeetingBot } from '../types';

interface SidebarProps {
  bots: MeetingBot[];
  selectedBotId: number | null;
  onBotSelect: (botId: number) => void;
  onNewBot: () => void;
  onDeleteBot: (botId: number) => void;
  reportData: any;
  scorecardCache: Map<number, any>;
  isBotStuck: (bot: MeetingBot) => boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  bots,
  selectedBotId,
  onBotSelect,
  onNewBot,
  onDeleteBot,
  reportData,
  scorecardCache,
  isBotStuck
}) => {
  const getStatusIcon = (status: MeetingBot['status']) => {
    switch (status) {
      case 'PENDING':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'STARTED':
        return <Settings className="w-4 h-4 text-primary-600" />;
      case 'COMPLETED':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'FAILED':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Bot className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: MeetingBot['status']) => {
    switch (status) {
      case 'PENDING':
        return 'bg-yellow-100 text-yellow-800';
      case 'STARTED':
        return 'bg-primary-100 text-primary-800';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: MeetingBot['status']) => {
    switch (status) {
      case 'PENDING':
        return 'Creating...';
      case 'STARTED':
        return 'In Meeting';
      case 'COMPLETED':
        return 'Completed';
      case 'FAILED':
        return 'Failed';
      default:
        return status;
    }
  };

  const formatMeetingUrl = (url: string) => {
    try {
      const urlObj = new URL(url);
      return `${urlObj.hostname}${urlObj.pathname}`;
    } catch {
      return url.length > 30 ? url.substring(0, 30) + '...' : url;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return 'Today';
    } else if (diffDays === 2) {
      return 'Yesterday';
    } else if (diffDays <= 7) {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const handleDeleteClick = (e: React.MouseEvent, botId: number) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this bot? This action cannot be undone.')) {
      onDeleteBot(botId);
    }
  };

  return (
    <div className="w-80 bg-white border-r border-gray-200 h-screen overflow-y-auto">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <Bot className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-bold text-black">Meeting Bots</h2>
          <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">
            {bots.length}
          </span>
        </div>

        <button
          type="button"
          onClick={onNewBot}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 mb-6 cursor-pointer"
        >
          <Bot className="w-4 h-4" />
          New Bot
        </button>

        <div className="space-y-3">
          {bots.map((bot) => {
            const isSelected = selectedBotId === bot.id;
            const botScorecard = scorecardCache.get(bot.id);
            const hasReport = botScorecard && botScorecard.scorecard;
            const isStuck = isBotStuck(bot);
            
            return (
              <div
                key={bot.id}
                onClick={() => onBotSelect(bot.id)}
                className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? 'border-primary-500 bg-primary-50 shadow-md'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                } ${isStuck ? 'border-orange-300 bg-orange-50' : ''}`}
              >
                {/* Bot Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(bot.status)}
                    <h3 className="font-medium text-black truncate max-w-[120px]">
                      {bot.meeting_metadata.bot_name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
                      {getStatusText(bot.status)}
                    </span>
                    <button
                      onClick={(e) => handleDeleteClick(e, bot.id)}
                      className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors duration-200"
                      title="Delete bot"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                {/* Meeting Details */}
                <div className="space-y-2 text-sm text-gray-600">
                  {/* Meeting URL */}
                  <div className="flex items-center gap-2">
                    <Link className="w-3 h-3 text-gray-400" />
                    <p className="truncate text-xs font-mono">
                      {formatMeetingUrl(bot.meeting_url)}
                    </p>
                  </div>
                  
                  {/* Creation Date */}
                  <div className="flex items-center gap-2">
                    <Calendar className="w-3 h-3 text-gray-400" />
                    <p className="text-xs">
                      Created: {formatDate(bot.created_at)}
                    </p>
                  </div>
                  
                  {/* Join Time */}
                  {bot.meeting_metadata.join_at && (
                    <div className="flex items-center gap-2">
                      <Users className="w-3 h-3 text-gray-400" />
                      <p className="text-xs">
                        Joins: {new Date(bot.meeting_metadata.join_at).toLocaleTimeString()}
                      </p>
                    </div>
                  )}
                  
                  {/* Status-specific indicators */}
                  {bot.status === 'COMPLETED' && (
                    <div className="flex items-center gap-2 mt-2 p-2 bg-green-50 rounded border border-green-200">
                      <BarChart3 className="w-3 h-3 text-green-600" />
                      <span className="text-xs text-green-700 font-medium">
                        {hasReport ? '📊 Report Ready' : '⏳ Generating Report...'}
                      </span>
                    </div>
                  )}
                  
                  {bot.status === 'STARTED' && (
                    <div className="flex items-center gap-2 mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                      <Clock className="w-3 h-3 text-blue-600" />
                      <span className="text-xs text-blue-700 font-medium">
                        🎥 Recording in Progress
                      </span>
                    </div>
                  )}
                  
                  {bot.status === 'PENDING' && (
                    <div className="flex items-center gap-2 mt-2 p-2 bg-yellow-50 rounded border border-yellow-200">
                      <Clock className="w-3 h-3 text-yellow-600" />
                      <span className="text-xs text-yellow-700 font-medium">
                        ⏳ Bot is Joining...
                      </span>
                    </div>
                  )}
                  
                  {bot.status === 'FAILED' && (
                    <div className="flex items-center gap-2 mt-2 p-2 bg-red-50 rounded border border-red-200">
                      <Clock className="w-3 h-3 text-red-600" />
                      <span className="text-xs text-red-700 font-medium">
                        ❌ Failed to Join
                      </span>
                    </div>
                  )}
                  
                  {/* Stuck Status Warning */}
                  {isStuck && (
                    <div className="flex items-center gap-2 mt-2 p-2 bg-orange-50 rounded border border-orange-200">
                      <AlertCircle className="w-3 h-3 text-orange-600" />
                      <span className="text-xs text-orange-700 font-medium">
                        ⚠️ Status Stuck - Check Manually
                      </span>
                    </div>
                  )}
                </div>
                

              </div>
            );
          })}
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