import React, { useState, useEffect, useCallback } from 'react';
import { Bot, Plus, Trash2 } from 'lucide-react';
import { MeetingConfig, MeetingBot, ScorecardResponse } from './types';
import Sidebar from './components/Sidebar';
import ConfigScreen from './components/ConfigScreen';
import ScorecardScreen from './components/ScorecardScreen';
import apiService from './services/api';

const App: React.FC = () => {
  const [bots, setBots] = useState<MeetingBot[]>([]);
  const [selectedBotId, setSelectedBotId] = useState<number | null>(null);
  const [isCreatingNewBot, setIsCreatingNewBot] = useState(false);
  const [config, setConfig] = useState<MeetingConfig>({
    meeting_url: '',
    bot_name: '',
    join_at: undefined,
    webhook_base_url: '' // No hardcoded default - user must input this
  });
  
  const [scorecardCache, setScorecardCache] = useState<Map<number, ScorecardResponse>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedBot = bots.find(bot => bot.id === selectedBotId);
  const currentScorecardData = selectedBotId ? scorecardCache.get(selectedBotId) : null;

  // Load bots on mount
  useEffect(() => {
    loadBots();
  }, []);

  const loadBots = async () => {
    try {
      const botsData = await apiService.getBots();
      setBots(botsData.items || botsData);
      
      // Auto-select most recent bot
      if (botsData.items?.length > 0 && !selectedBotId) {
        const mostRecentBot = botsData.items[0];
        handleBotSelect(mostRecentBot.id);
      }
    } catch (error) {
      setError('Failed to load bots. Please refresh the page.');
    }
  };

  const handleNewBot = () => {
    setSelectedBotId(null);
    setIsCreatingNewBot(true);
    // Set default webhook URL to point to our backend
    setConfig({ 
      meeting_url: '', 
      bot_name: '', 
      join_at: undefined, 
      webhook_base_url: 'http://localhost:8000' 
    });
    setError(null);
  };

  const handleConfigSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiService.createBot(config);
      
      const newBot: MeetingBot = {
        id: result.id,
        meeting_url: result.meeting_url,
        bot_id: result.bot_id,
        status: result.status as MeetingBot['status'],
        meeting_metadata: result.meeting_metadata,
        created_at: result.created_at,
        updated_at: result.updated_at
      };
      
      setBots(prev => [newBot, ...prev]);
      setSelectedBotId(result.id);
      setIsCreatingNewBot(false);
      
      // Start polling for status updates
      if (result.status === 'PENDING' || result.status === 'STARTED') {
        startStatusPolling(result.id);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bot creation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleBotSelect = useCallback((botId: number) => {
    setSelectedBotId(botId);
    setIsCreatingNewBot(false);
    
    const bot = bots.find(b => b.id === botId);
    if (bot) {
      setConfig({
        meeting_url: bot.meeting_url,
        bot_name: bot.meeting_metadata.bot_name,
        join_at: bot.meeting_metadata.join_at,
        webhook_base_url: bot.meeting_metadata.webhook_base_url // Only set if it exists, no hardcoded fallback
      });
      
      // Fetch scorecard if completed
      if (bot.status === 'COMPLETED') {
        fetchScorecardData(botId);
      }
    }
  }, [bots]);

  const handleDeleteBot = async (botId: number) => {
    try {
      await apiService.deleteBot(botId);
      setBots(prev => prev.filter(bot => bot.id !== botId));
      
      if (selectedBotId === botId) {
        setSelectedBotId(null);
        setConfig({ meeting_url: '', bot_name: '', join_at: undefined, webhook_base_url: '' });
      }
    } catch (error) {
      alert(`Failed to delete bot: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const startStatusPolling = useCallback((botId: number) => {
    const pollStatus = async () => {
      try {
        const statusResult = await apiService.pollBotStatus(botId);
        
        if (statusResult.status_updated) {
          setBots(prev => prev.map(bot => 
            bot.id === botId 
              ? { ...bot, status: statusResult.new_status as MeetingBot['status'], updated_at: new Date().toISOString() }
              : bot
          ));
          
          if (statusResult.new_status === 'COMPLETED') {
            setTimeout(() => fetchScorecardData(botId), 2000);
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    };

    // Poll every 10 seconds
    const interval = setInterval(pollStatus, 10000);
    
    // Cleanup interval after 5 minutes or when bot completes
    setTimeout(() => clearInterval(interval), 300000);
  }, []);

  const fetchScorecardData = async (meetingId: number) => {
    try {
      const data = await apiService.getMeetingScorecard(meetingId);
      setScorecardCache(prev => new Map(prev).set(meetingId, data));
      
      if (data.status === 'processing') {
        setTimeout(() => fetchScorecardData(meetingId), 5000);
      }
    } catch (err) {
      console.error('Failed to fetch scorecard:', err);
    }
  };

  const shouldShowReport = selectedBot && selectedBot.status === 'COMPLETED' && currentScorecardData?.scorecard;
  const shouldShowConfig = selectedBot && selectedBot.status !== 'COMPLETED';
  // Allow multiple bots to be created regardless of status
  const isBotInMeeting = false;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          bots={bots}
          selectedBotId={selectedBotId}
          onBotSelect={handleBotSelect}
          onNewBot={handleNewBot}
          onDeleteBot={handleDeleteBot}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bot className="w-6 h-6 text-blue-600" />
                <h1 className="text-xl font-bold text-gray-900">Meahana Attendee</h1>
                {selectedBot && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">• {selectedBot.meeting_metadata.bot_name}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      selectedBot.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                      selectedBot.status === 'STARTED' ? 'bg-blue-100 text-blue-800' :
                      selectedBot.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {selectedBot.status === 'COMPLETED' ? 'Completed' :
                       selectedBot.status === 'STARTED' ? 'In Meeting' :
                       selectedBot.status === 'PENDING' ? 'Creating...' :
                       'Failed'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </header>

          {/* Content Area */}
          <main className="flex-1 p-6 overflow-y-auto">
            {isCreatingNewBot ? (
              <ConfigScreen
                config={config}
                setConfig={setConfig}
                onSubmit={handleConfigSubmit}
                loading={loading}
                error={error}
                isBotInMeeting={isBotInMeeting}
              />
            ) : !selectedBotId ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-600 mb-2">No Bot Selected</h2>
                  <p className="text-gray-500">Select a bot from the sidebar or create a new one</p>
                </div>
              </div>
            ) : shouldShowReport ? (
              <ScorecardScreen
                scorecardData={currentScorecardData}
                config={config}
                loading={loading}
                error={error}
              />
            ) : shouldShowConfig ? (
              <ConfigScreen
                config={config}
                setConfig={setConfig}
                onSubmit={handleConfigSubmit}
                loading={loading}
                error={error}
                isBotInMeeting={isBotInMeeting}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h2 className="text-xl font-semibold text-gray-600 mb-2">Bot Ready</h2>
                  <p className="text-gray-500">Configure your bot to get started</p>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default App; 