import React from 'react';
import { BarChart3, RefreshCw, Settings, CheckCircle, AlertCircle, TrendingUp } from 'lucide-react';
import { ReportData, MeetingConfig } from '../types';

interface ScorecardScreenProps {
  reportData: ReportData | null;
  config?: MeetingConfig;
  onRefresh: () => void;
  loading: boolean;
  error: string | null;
}

const ScorecardScreen: React.FC<ScorecardScreenProps> = ({
  reportData,
  config,
  onRefresh,
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

  return (
    <div className="w-full max-w-7xl mx-auto">
      <div className="bg-white rounded-lg p-8 shadow-lg border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-primary-600" />
            <h2 className="text-2xl font-bold text-black">Meeting Report</h2>
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
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Meeting URL</label>
                <p className="text-sm text-black break-all">{config.meeting_url}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-600 mb-1">Bot Name</label>
                <p className="text-sm text-black">{config.bot_name}</p>
              </div>
              {config.join_at && (
                <div>
                  <label className="block text-sm font-medium text-gray-600 mb-1">Join Time</label>
                  <p className="text-sm text-black">{new Date(config.join_at).toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {reportData && !loading && (
          <div className="space-y-6">
            {/* Status Message */}
            {reportData.message && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-700 text-sm">{reportData.message}</p>
              </div>
            )}

            {/* Reports */}
            {reportData.reports && reportData.reports.length > 0 && (
              <div className="space-y-6">
                {reportData.reports.map((report, index) => (
                  <div key={report.id} className="space-y-6">
                    {/* Report Header */}
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-black">Report #{index + 1}</h3>
                      <span className="text-sm text-gray-500">
                        {new Date(report.created_at).toLocaleString()}
                      </span>
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
                          <div className={`text-4xl font-bold ${getEngagementColor(report.score.overall_score * 10)}`}>
                            {(report.score.overall_score * 100).toFixed(0)}%
                          </div>
                        </div>

                        {/* Engagement Score */}
                        <div className="text-center">
                          <div className="flex items-center justify-center gap-2 mb-2">
                            <TrendingUp className="w-5 h-5 text-primary-600" />
                            <h5 className="font-medium text-black">Engagement</h5>
                          </div>
                          <div className={`text-4xl font-bold ${getEngagementColor(report.score.engagement_score * 10)}`}>
                            {(report.score.engagement_score * 100).toFixed(0)}%
                          </div>
                        </div>

                        {/* Meeting Effectiveness */}
                        <div className="text-center">
                          <div className="flex items-center justify-center gap-2 mb-2">
                            <TrendingUp className="w-5 h-5 text-primary-600" />
                            <h5 className="font-medium text-black">Effectiveness</h5>
                          </div>
                          <div className={`text-4xl font-bold ${getEngagementColor(report.score.meeting_effectiveness * 10)}`}>
                            {(report.score.meeting_effectiveness * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Grid Layout for Other Sections */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Meeting Context Card */}
                      <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 h-64 flex flex-col">
                        <h4 className="font-medium text-black mb-4">Meeting Context</h4>
                        
                        {/* Sentiment */}
                        <div className="mb-4">
                          <h5 className="font-medium text-black mb-2">Sentiment</h5>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSentimentColor(report.score.sentiment)}`}>
                            {report.score.sentiment}
                          </span>
                        </div>

                        {/* Participants */}
                        {report.score.participants && report.score.participants.length > 0 && (
                          <div className="flex-1">
                            <h5 className="font-medium text-black mb-2">Participants</h5>
                            <div className="flex flex-wrap gap-2">
                              {report.score.participants.map((participant, idx) => (
                                <span key={idx} className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm">
                                  {participant}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Key Insights Card */}
                      {report.score.insights && report.score.insights.length > 0 && (
                        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 h-64 flex flex-col">
                          <h4 className="font-medium text-black mb-4">Key Insights</h4>
                          <ul className="space-y-3 flex-1 overflow-y-auto">
                            {report.score.insights.map((insight, idx) => (
                              <li key={idx} className="flex items-start gap-3">
                                <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-700">{insight}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Meeting Summary Card */}
                      <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 h-64 flex flex-col">
                        <h4 className="font-medium text-black mb-4">Meeting Summary</h4>
                        <div className="flex-1 overflow-y-auto">
                          <p className="text-gray-700 leading-relaxed">{report.score.summary}</p>
                        </div>
                      </div>

                      {/* Action Items Card */}
                      {report.score.action_items && report.score.action_items.length > 0 && (
                        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 h-64 flex flex-col">
                          <h4 className="font-medium text-black mb-4">Action Items</h4>
                          <ul className="space-y-3 flex-1 overflow-y-auto">
                            {report.score.action_items.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-orange-600 mt-0.5 flex-shrink-0" />
                                <span className="text-gray-700">{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Key Topics Card */}
                      {report.score.key_topics && report.score.key_topics.length > 0 && (
                        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 h-64 flex flex-col">
                          <h4 className="font-medium text-black mb-4">Key Topics</h4>
                          <div className="flex flex-wrap gap-2 flex-1 items-start">
                            {report.score.key_topics.map((topic, idx) => (
                              <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Recommendations Card */}
                      {report.score.recommendations && report.score.recommendations.length > 0 && (
                        <div className="bg-gray-50 rounded-lg p-6 border border-gray-200 h-64 flex flex-col">
                          <h4 className="font-medium text-black mb-4">Recommendations</h4>
                          <ul className="space-y-3 flex-1 overflow-y-auto">
                            {report.score.recommendations.map((recommendation, idx) => (
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
                ))}
              </div>
            )}

            {/* No Reports Available */}
            {(!reportData.reports || reportData.reports.length === 0) && !reportData.message && (
              <div className="text-center py-12">
                <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No reports available yet.</p>
                <p className="text-sm text-gray-500">Reports are generated after the meeting is completed.</p>
              </div>
            )}
          </div>
        )}

        {!reportData && !loading && !error && (
          <div className="text-center py-12">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No report data available. Click refresh to fetch data.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScorecardScreen; 