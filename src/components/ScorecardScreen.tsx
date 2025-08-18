import React from 'react';
import { BarChart3, RefreshCw, Settings, CheckCircle, AlertCircle, TrendingUp, Calendar, Users, Link } from 'lucide-react';
import { ScorecardResponse, MeetingConfig } from '../types';

interface ScorecardScreenProps {
  scorecardData: ScorecardResponse | null;
  config?: MeetingConfig;
  onRefresh: () => void;
  onTriggerAnalysis?: () => void;
  loading: boolean;
  error: string | null;
}

const ScorecardScreen: React.FC<ScorecardScreenProps> = ({
  scorecardData,
  config,
  onRefresh,
  onTriggerAnalysis,
  loading,
  error
}) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'text-green-600 bg-green-100';
      case 'negative':
        return 'text-red-600 bg-red-100';
      case 'neutral':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-blue-600 bg-blue-100';
    }
  };

  const getEngagementColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="w-full max-w-7xl mx-auto">
      <div className="bg-white rounded-lg p-8 shadow-lg border border-gray-200">
        {/* Header with Meeting Info */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-primary-600" />
            <div>
              <h2 className="text-2xl font-bold text-black">Meeting Report</h2>
              {scorecardData && (
                <p className="text-sm text-gray-500">
                  Meeting ID: {scorecardData.meeting_id} • 
                  Status: <span className="font-medium text-green-600">{scorecardData.status}</span>
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Configuration Card */}
        {config && (
          <div className="bg-gray-50 rounded-lg p-6 mb-6 border border-gray-200">
            <div className="flex items-center gap-3 mb-4">
              <Settings className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-black">Bot Configuration</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <Link className="w-4 h-4 text-gray-400" />
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Meeting URL</label>
                  <p className="text-sm text-black break-all">{config.meeting_url}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-gray-400" />
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Bot Name</label>
                  <p className="text-sm text-black">{config.bot_name}</p>
                </div>
              </div>
              {config.join_at && (
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <div>
                    <label className="block text-sm font-medium text-gray-600 mb-1">Join Time</label>
                    <p className="text-sm text-black">{formatDate(config.join_at)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
            <span className="ml-3 text-gray-600">Updating scorecard...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-5 h-5 text-red-600" />
              <h3 className="font-medium text-red-800">Error Loading Scorecard</h3>
            </div>
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {scorecardData && !loading && (
          <div className="space-y-6">
            {/* Status Message */}
            {scorecardData.message && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-blue-600" />
                  <p className="text-blue-700 text-sm">{scorecardData.message}</p>
                </div>
              </div>
            )}

            {/* Scorecard */}
            {scorecardData.scorecard && (
              <div className="space-y-6">
                {/* Scorecard Header */}
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-black">AI-Generated Scorecard</h3>
                  <div className="text-right">
                    <span className="text-sm text-gray-500">Generated on</span>
                    <p className="text-sm font-medium text-gray-700">
                      {scorecardData.created_at ? formatDate(scorecardData.created_at) : 'Unknown'}
                    </p>
                  </div>
                </div>

                {/* Scores Card - Full Width */}
                <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                  <h4 className="font-medium text-black mb-4">Meeting Metrics</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Overall Score */}
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <TrendingUp className="w-5 h-5 text-primary-600" />
                        <h5 className="font-medium text-black">Overall Score</h5>
                      </div>
                      <div className={`text-4xl font-bold ${getEngagementColor(scorecardData.scorecard.overall_score * 10)}`}>
                        {(scorecardData.scorecard.overall_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    {/* Engagement Score */}
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <TrendingUp className="w-5 h-5 text-primary-600" />
                        <h5 className="font-medium text-black">Engagement</h5>
                      </div>
                      <div className={`text-4xl font-bold ${getEngagementColor(scorecardData.scorecard.engagement_score * 10)}`}>
                        {(scorecardData.scorecard.engagement_score * 100).toFixed(0)}%
                      </div>
                    </div>

                    {/* Meeting Effectiveness */}
                    <div className="text-center">
                      <div className="flex items-center justify-center gap-2 mb-2">
                        <TrendingUp className="w-5 h-5 text-primary-600" />
                        <h5 className="font-medium text-black">Effectiveness</h5>
                      </div>
                      <div className={`text-4xl font-bold ${getEngagementColor(scorecardData.scorecard.meeting_effectiveness * 10)}`}>
                        {(scorecardData.scorecard.meeting_effectiveness * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Grid Layout for Other Sections */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 auto-rows-fr">
                  {/* Meeting Context Card */}
                  <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <h4 className="font-medium text-black mb-4">Meeting Context</h4>
                    
                    {/* Sentiment */}
                    <div className="mb-4">
                      <h5 className="font-medium text-black mb-2">Sentiment</h5>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSentimentColor(scorecardData.scorecard.sentiment)}`}>
                        {scorecardData.scorecard.sentiment}
                      </span>
                    </div>

                    {/* Participants */}
                    {scorecardData.scorecard.participants && scorecardData.scorecard.participants.length > 0 && (
                      <div>
                        <h5 className="font-medium text-black mb-2">Participants</h5>
                        <div className="flex flex-wrap gap-2">
                          {scorecardData.scorecard.participants.map((participant, idx) => (
                            <span key={idx} className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {participant}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Key Insights Card */}
                  {scorecardData.scorecard.insights && scorecardData.scorecard.insights.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                      <h4 className="font-medium text-black mb-4">Key Insights</h4>
                      <ul className="space-y-3">
                        {scorecardData.scorecard.insights.map((insight, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Meeting Summary Card */}
                  <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <h4 className="font-medium text-black mb-4">Meeting Summary</h4>
                    <p className="text-gray-700 leading-relaxed">{scorecardData.scorecard.summary}</p>
                  </div>

                  {/* Action Items Card */}
                  {scorecardData.scorecard.action_items && scorecardData.scorecard.action_items.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                      <h4 className="font-medium text-black mb-4">Action Items</h4>
                      <ul className="space-y-3">
                        {scorecardData.scorecard.action_items.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Key Topics Card */}
                  {scorecardData.scorecard.key_topics && scorecardData.scorecard.key_topics.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                      <h4 className="font-medium text-black mb-4">Key Topics</h4>
                      <div className="flex flex-wrap gap-2">
                        {scorecardData.scorecard.key_topics.map((topic, idx) => (
                          <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations Card */}
                  {scorecardData.scorecard.recommendations && scorecardData.scorecard.recommendations.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                      <h4 className="font-medium text-black mb-4">Recommendations</h4>
                      <ul className="space-y-3">
                        {scorecardData.scorecard.recommendations.map((recommendation, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-700">{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* No Scorecard Available */}
            {scorecardData && !scorecardData.scorecard && (
              <div className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                {scorecardData.status === 'processing_needed' ? (
                  <>
                    <p className="text-gray-600">Analysis needed to generate scorecard.</p>
                    <p className="text-sm text-gray-500">The meeting has completed with transcript data, but AI analysis is required to create the scorecard.</p>
                    <button
                      onClick={onTriggerAnalysis || onRefresh}
                      className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2 mx-auto"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Trigger Analysis
                    </button>
                  </>
                ) : scorecardData.status === 'no_data' ? (
                  <>
                    <p className="text-gray-600">No transcript data available.</p>
                    <p className="text-sm text-gray-500">The meeting completed but no transcript data was captured. Cannot generate scorecard.</p>
                  </>
                ) : (
                  <>
                    <p className="text-gray-600">No scorecard available yet.</p>
                    <p className="text-sm text-gray-500">Scorecards are generated after the meeting is completed and transcript data is available.</p>
                    <button
                      onClick={onRefresh}
                      className="mt-4 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2 mx-auto"
                    >
                      <RefreshCw className="w-4 h-4" />
                      Check for Scorecard
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {!scorecardData && !loading && !error && (
          <div className="text-center py-12">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No scorecard data available. Click refresh to fetch data.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScorecardScreen; 