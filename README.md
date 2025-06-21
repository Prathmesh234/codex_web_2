# AI Browser Automation Chat Interface

A web application that combines a chat interface with browser automation capabilities using E2B sandbox environment.

## Project Structure

```
.
├── frontend/           # Next.js frontend application
│   ├── components/    # React components
│   ├── pages/         # Next.js pages
│   └── styles/        # CSS styles
├── backend/           # FastAPI backend server
│   ├── app/          # Application code
│   └── tests/        # Test files
└── README.md         # This file
```

## Technologies Used

### Frontend
- Next.js 14
- Chakra UI
- TypeScript
- Axios for API calls

### Backend
- FastAPI
- Python 3.9+
- E2B Desktop
- Browser automation tools

## Prerequisites

- Node.js 18+
- Python 3.9+
- npm or yarn
- pip

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

4. Set up environment variables:
Create `.env` files in both frontend and backend directories with the necessary API keys and configurations.

5. Start the backend server:
```bash
cd backend
uvicorn app.main:app --reload
```

6. Start the frontend development server:
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:3000`

## Environment Variables

### Backend Setup
1. Copy `env.example` to `.env` in the root directory
2. Fill in your API keys and configuration values

### Frontend Setup  
1. Copy `frontend/env.example` to `frontend/.env.local`
2. Fill in your Appwrite project ID and API URL

### Required Environment Variables

#### Backend (.env)
```
# AI/ML API Keys
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Browser Automation
ANCHOR_API_KEY=your_anchor_api_key_here

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
```

#### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APPWRITE_PROJECT_ID=your_appwrite_project_id_here
```

### Optional Environment Variables
```
# Azure AI Search (for memory features)
AZURE_AI_SEARCH_ENDPOINT=your_azure_search_endpoint_here
AZUREAI_SEARCH_API_KEY=your_azure_search_api_key_here

# E2B Sandbox (alternative to Anchor Browser)
E2B_API_KEY=your_e2b_api_key_here
```

## API Key Setup Instructions

### 1. OpenAI API Key
- Go to [OpenAI Platform](https://platform.openai.com/api-keys)
- Create a new API key
- Add to `OPENAI_API_KEY`

### 2. Google Gemini API Key  
- Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
- Create a new API key
- Add to `GEMINI_API_KEY`

### 3. Anchor Browser API Key
- Sign up at [Anchor Browser](https://anchor.browser.com)
- Get your API key from the dashboard
- Add to `ANCHOR_API_KEY`

### 4. GitHub OAuth Setup
1. Go to [GitHub Settings > Developer settings > OAuth Apps](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set **Homepage URL** to `http://localhost:3000`
4. Set **Authorization callback URL** to `http://localhost:8000/auth/github/callback`
5. Copy Client ID and Client Secret to `.env`

### 5. Appwrite Setup
1. Go to [Appwrite Cloud](https://cloud.appwrite.io/)
2. Create a new project
3. Go to Settings > General and copy the Project ID
4. Add to `NEXT_PUBLIC_APPWRITE_PROJECT_ID`
5. In Auth > Settings, add GitHub OAuth provider
6. Set callback URL to `http://localhost:3000/auth/success`

## Features

- Real-time chat interface
- Browser automation visualization
- Task history tracking
- Responsive design

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
