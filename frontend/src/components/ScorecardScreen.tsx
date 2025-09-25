import React from 'react';
import { BarChart3, TrendingUp, Users } from 'lucide-react';
import { ScorecardResponse, MeetingConfig } from '../types';

interface ScorecardScreenProps {
  scorecardData: ScorecardResponse;
  config: MeetingConfig;
  loading: boolean;
  error: string | null;
}

const ScorecardScreen: React.FC<ScorecardScreenProps> = ({
  scorecardData,
  config,
  loading,
  error
}) => {
  if (!scorecardData?.scorecard) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-600 mb-2">Scorecard Not Available</h2>
          <p className="text-gray-500 mb-4">{scorecardData?.message || 'No scorecard data available'}</p>
        </div>
      </div>
    );
  }

  const { scorecard } = scorecardData;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Meeting Scorecard</h1>
            <p className="text-gray-600">{config.bot_name} • {config.meeting_url}</p>
          </div>
        </div>
        
        {/* Overall Score */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Overall Score</h2>
              <p className="text-gray-600">Meeting effectiveness and engagement</p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold text-blue-600">{scorecard.overall_score}/10</div>
              <div className="text-sm text-gray-600">out of 10</div>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Engagement Score */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Engagement</h3>
              <p className="text-sm text-gray-600">Participant involvement</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-green-600">{scorecard.engagement_score}/10</div>
        </div>

        {/* Meeting Effectiveness */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Effectiveness</h3>
              <p className="text-sm text-gray-600">Goal achievement</p>
            </div>
          </div>
          <div className="text-3xl font-bold text-blue-600">{scorecard.meeting_effectiveness}/10</div>
        </div>

        {/* Sentiment */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Sentiment</h3>
              <p className="text-sm text-gray-600">Overall mood</p>
            </div>
          </div>
          <div className="text-lg font-semibold text-purple-600 capitalize">{scorecard.sentiment}</div>
        </div>
      </div>

      {/* Content Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Summary */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Summary</h3>
          <p className="text-gray-700 leading-relaxed">{scorecard.summary}</p>
        </div>

        {/* Participants */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Participants</h3>
          <div className="space-y-2">
            {scorecard.participants.map((participant, index) => (
              <div key={index} className="flex items-center gap-2 text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                {participant}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Lists Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Key Topics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Topics</h3>
          <div className="space-y-2">
            {scorecard.key_topics.map((topic, index) => (
              <div key={index} className="bg-gray-50 px-3 py-2 rounded-lg text-gray-700 text-sm">
                {topic}
              </div>
            ))}
          </div>
        </div>

        {/* Action Items */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Action Items</h3>
          <div className="space-y-2">
            {scorecard.action_items.map((item, index) => (
              <div key={index} className="flex items-start gap-2 text-gray-700">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-sm">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Insights */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Insights</h3>
          <div className="space-y-2">
            {scorecard.insights.map((insight, index) => (
              <div key={index} className="flex items-start gap-2 text-gray-700">
                <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-sm">{insight}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {scorecard.recommendations.map((recommendation, index) => (
            <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-blue-600 text-sm font-medium">{index + 1}</span>
                </div>
                <p className="text-gray-700 text-sm">{recommendation}</p>
              </div>
            </div>
          ))}
        </div>
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
    </div>
  );
};

export default ScorecardScreen; 