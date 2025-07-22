export interface MeetingConfig {
  meeting_url: string;
  bot_name: string;
  join_at?: string;
}

export interface MeetingBot {
  id: number;
  meeting_url: string;
  bot_id: string;
  status: 'pending' | 'started' | 'completed' | 'failed';
  meeting_metadata: {
    bot_name: string;
    join_at?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface TranscriptChunk {
  id: number;
  speaker: string;
  text: string;
  timestamp: string;
  confidence: string;
  created_at: string;
}

export interface TranscriptData {
  id: number;
  meeting_url: string;
  bot_id: string;
  status: string;
  transcript_chunks: TranscriptChunk[];
}

export interface ReportScore {
  summary: string;
  key_points: string[];
  action_items: string[];
  sentiment: string;
  engagement_score: number;
}

export interface Report {
  id: number;
  score: ReportScore;
  created_at: string;
}

export interface ReportData {
  meeting_id: number;
  status: string;
  reports: Report[];
  message: string | null;
}

export interface CreateBotRequest {
  meeting_url: string;
  bot_name: string;
  join_at?: string;
}

export interface CreateBotResponse {
  id: number;
  meeting_url: string;
  bot_id: string;
  status: string;
  meeting_metadata: {
    bot_name: string;
    join_at?: string;
  };
  created_at: string;
  updated_at: string;
} 