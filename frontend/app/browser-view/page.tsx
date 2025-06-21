"use client";

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ExternalLink, Monitor } from 'lucide-react';
import Link from 'next/link';

interface BrowserInfo {
  live_view_url: string;
  session_id: string;
  subtask: string;
}

export default function BrowserViewPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [browsers, setBrowsers] = useState<Record<string, BrowserInfo>>({});
  const [taskMessage, setTaskMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get browser data from URL parameters
    const browsersParam = searchParams?.get('browsers');
    const messageParam = searchParams?.get('message');
    
    if (browsersParam) {
      try {
        const browsersData = JSON.parse(decodeURIComponent(browsersParam));
        setBrowsers(browsersData);
        console.log('Browser data loaded:', browsersData);
      } catch (error) {
        console.error('Error parsing browser data:', error);
      }
    }
    
    if (messageParam) {
      setTaskMessage(decodeURIComponent(messageParam));
    }
    
    setLoading(false);
  }, [searchParams]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading browser view...</p>
        </div>
      </div>
    );
  }

  if (Object.keys(browsers).length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Monitor className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">No Browser Sessions</h2>
          <p className="text-gray-600 mb-4">No browser sessions found for this task.</p>
          <Link href="/chat">
            <Button>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Chat
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/chat">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Chat
                </Button>
              </Link>
              <div>
                <h1 className="text-xl font-semibold">Browser Sessions</h1>
                {taskMessage && (
                  <p className="text-sm text-gray-600 mt-1">{taskMessage}</p>
                )}
              </div>
            </div>
            <div className="text-sm text-gray-500">
              {Object.keys(browsers).length} browser{Object.keys(browsers).length > 1 ? 's' : ''} active
            </div>
          </div>
        </div>
      </div>

      {/* Browser Grid */}
      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.entries(browsers).map(([browserKey, browserInfo]) => (
            <Card key={browserKey} className="overflow-hidden">
              {/* Browser Header */}
              <div className="bg-gray-50 px-4 py-3 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Monitor className="w-4 h-4 text-gray-600" />
                    <span className="font-medium">{browserKey}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">
                      Session: {browserInfo.session_id.slice(0, 8)}...
                    </span>
                    <a
                      href={browserInfo.live_view_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </div>
                </div>
                <p className="text-xs text-gray-600 mt-1 truncate">
                  {browserInfo.subtask}
                </p>
              </div>

              {/* Browser Content */}
              <div className="h-96">
                {browserInfo.live_view_url.startsWith('https://mock-browser.com') ? (
                  <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                    <div className="text-center">
                      <Monitor className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">Mock Browser Session</p>
                      <p className="text-xs text-gray-500 mt-1">
                        Session ID: {browserInfo.session_id}
                      </p>
                      <p className="text-xs text-gray-500">
                        Documentation collection in progress...
                      </p>
                    </div>
                  </div>
                ) : (
                  <iframe
                    src={browserInfo.live_view_url}
                    className="w-full h-full border-0"
                    title={`${browserKey} Live View`}
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
                  />
                )}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
} 