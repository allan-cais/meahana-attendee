import React, { useState, useEffect } from 'react';
import { Bot } from 'lucide-react';
import { MeetingConfig, MeetingBot, ReportData } from './types';
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
    join_at: undefined
  });
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const selectedBot = bots.find(bot => bot.id === selectedBotId);

  // Create new bot
  const handleNewBot = () => {
    setSelectedBotId(null);
    setIsCreatingNewBot(true);
    setConfig({ meeting_url: '', bot_name: '', join_at: undefined });
    setReportData(null);
    setError(null);
  };

  // Handle bot creation
  const handleConfigSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('Creating bot with config:', config);
      const result = await apiService.createBot(config);
      console.log('Bot created successfully:', result);
      
      // Add the new bot to the list
      const newBot: MeetingBot = {
        id: result.id,
        meeting_url: result.meeting_url,
        bot_id: result.bot_id,
        status: result.status as MeetingBot['status'],
        meeting_metadata: result.meeting_metadata,
        created_at: result.created_at,
        updated_at: result.updated_at
      };
      
      setBots(prev => [...prev, newBot]);
      setSelectedBotId(result.id);
      setIsCreatingNewBot(false);
      
      // If bot is completed, fetch report data immediately
      if (result.status === 'completed') {
        console.log('Bot is completed, fetching report data...');
        fetchReportData();
      }
      // Start polling for status updates if bot is pending
      else if (result.status === 'pending') {
        startStatusPolling(result.id);
      }
      
    } catch (err) {
      console.log('Error in handleConfigSubmit:', err);
      setError(err instanceof Error ? err.message : 'Bot creation failed');
    } finally {
      setLoading(false);
    }
  };

  // Poll for bot status updates
  const startStatusPolling = (botId: number) => {
    const interval = setInterval(async () => {
      try {
        // Check if bot status has changed to 'completed'
        const report = await apiService.getReport(botId);
        if (report.status === 'completed') {
          clearInterval(interval);
          setPollingInterval(null);
          
          // Update bot status
          setBots(prev => prev.map(bot => 
            bot.id === botId 
              ? { ...bot, status: 'completed', updated_at: new Date().toISOString() }
              : bot
          ));
          
          // If report is available, set it
          if (report.reports && report.reports.length > 0) {
            setReportData(report);
          }
        }
      } catch (error) {
        console.error('Status polling error:', error);
      }
    }, 5000); // Poll every 5 seconds

    setPollingInterval(interval);
  };

  // Fetch report data
  const fetchReportData = async () => {
    if (!selectedBotId) return;
    
    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getReport(selectedBotId);
      setReportData(data);
      
      // If bot is completed but we don't have reports yet, start polling
      if (data.status === 'completed' && (!data.reports || data.reports.length === 0)) {
        const polledData = await apiService.pollForReport(selectedBotId);
        setReportData(polledData);
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report data');
    } finally {
      setLoading(false);
    }
  };

  // Handle bot selection
  const handleBotSelect = (botId: number) => {
    setSelectedBotId(botId);
    setIsCreatingNewBot(false);
    const bot = bots.find(b => b.id === botId);
    if (bot) {
      // Set config from bot metadata
      setConfig({
        meeting_url: bot.meeting_url,
        bot_name: bot.meeting_metadata.bot_name,
        join_at: bot.meeting_metadata.join_at
      });
      
      // Clear any existing report data
      setReportData(null);
    }
  };

  // Auto-fetch report data when bot is completed
  useEffect(() => {
    if (selectedBot && selectedBot.status === 'completed') {
      fetchReportData();
    }
  }, [selectedBotId]);

  // Cleanup polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Determine which screen to show
  const shouldShowReport = selectedBot && selectedBot.status === 'completed';
  const shouldShowConfig = selectedBot && selectedBot.status !== 'completed';

  return (
    <div className="min-h-screen bg-gray-50 text-black">
      <div className="flex h-screen">
        {/* Sidebar */}
        <Sidebar
          bots={bots}
          selectedBotId={selectedBotId}
          onBotSelect={handleBotSelect}
          onNewBot={handleNewBot}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center gap-3">
              <Bot className="w-6 h-6 text-primary-600" />
              <h1 className="text-xl font-bold text-black">Meeting Bot Dashboard</h1>
              {selectedBot && (
                <span className="text-gray-600">• {selectedBot.meeting_metadata.bot_name}</span>
              )}
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
                reportData={reportData}
                config={config}
                onRefresh={fetchReportData}
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