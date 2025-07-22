# Meeting Bot Dashboard

A clean, modern React application for configuring and monitoring meeting bots with a beautiful white/black/blue UI theme.

## Features

- **Clean UI Design**: White background with black text and blue accents
- **Meeting Bot Management**: Create and manage multiple meeting bots
- **Configuration Screen**: Set up meeting URL, bot name, and start time
- **Score Card Display**: View meeting results and analytics
- **Dynamic Navigation**: Right sidebar with bot list and status indicators
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **React Router** for navigation

## Project Structure

```
src/
├── components/
│   ├── ConfigScreen.tsx      # Bot configuration form
│   ├── ScorecardScreen.tsx   # Score display component
│   └── Sidebar.tsx          # Bot list sidebar
├── types/
│   └── index.ts             # TypeScript interfaces
├── App.tsx                  # Main application component
├── index.tsx               # React entry point
└── index.css               # Global styles
```

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd meeting-bot-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm run build` - Builds the app for production
- `npm test` - Launches the test runner
- `npm run eject` - Ejects from Create React App (one-way operation)

## API Integration

The application is fully integrated with the Meeting Bot Service API. The following endpoints are used:

### Create Bot
```
POST /api/v1/bots/
Content-Type: application/json

{
  "meeting_url": "string",
  "bot_name": "string",
  "join_at": "string" (optional)
}
```

### Get Meeting Transcripts
```
GET /meeting/{meeting_id}/transcripts
```

### Get Meeting Report
```
GET /meeting/{meeting_id}/report
```

### Environment Configuration

Set the API base URL in your environment:

```bash
# Development
REACT_APP_API_URL=http://localhost:8000

# Production
REACT_APP_API_URL=https://your-api-domain.com
```

### API Features

- **Real-time Status Updates**: Automatically polls for bot status changes
- **Report Polling**: Uses exponential backoff to wait for report generation
- **Error Handling**: Comprehensive error states and retry logic
- **Loading States**: Shows progress during bot creation (30-60 seconds)

## Usage

1. **Create a New Bot**: Click the "New Bot" button in the sidebar
2. **Configure Bot**: Fill in the meeting URL, bot name, and start time
3. **View Results**: Once configured and completed, view the score card
4. **Manage Multiple Bots**: Use the sidebar to switch between different bots

## Design System

### Colors
- **Primary**: Blue (#3B82F6) for accents and interactive elements
- **Background**: White (#FFFFFF) for main content areas
- **Text**: Black (#000000) for primary text
- **Borders**: Gray (#E5E7EB) for subtle separators

### Status Indicators
- **Configured**: Blue - Bot is set up but not running
- **Running**: Yellow - Bot is currently active
- **Completed**: Green - Bot has finished and results are available
- **Error**: Red - Bot encountered an error

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 