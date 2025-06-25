"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';

interface BrowserDoc {
  documentation?: {
    response: string;
    timestamp: string;
  };
  status?: string;
  error?: string;
}

interface DocumentationDisplayProps {
  sessionId: string;
  browsers: Record<string, BrowserDoc>;
  taskCompleted: boolean;
}

export default function DocumentationDisplay({ sessionId, browsers, taskCompleted }: DocumentationDisplayProps) {
  const [expanded, setExpanded] = useState(false);
  const [sessionData, setSessionData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Check if any browser has completed documentation
  const hasCompletedDocs = Object.values(browsers).some(browser => 
    browser.status === 'completed' && browser.documentation
  );

  const completedCount = Object.values(browsers).filter(browser => 
    browser.status === 'completed'
  ).length;

  const totalCount = Object.keys(browsers).length;

  // Fetch session data when expanding
  const fetchSessionData = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/browser-session/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setSessionData(data);
      }
    } catch (error) {
      console.error('Error fetching session data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (expanded && !sessionData) {
      fetchSessionData();
    }
  }, [expanded, sessionId]);

  // Don't show until at least one browser is completed
  if (!hasCompletedDocs && !taskCompleted) {
    return null;
  }

  const getStatusIcon = () => {
    if (completedCount === totalCount) {
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    } else if (completedCount > 0) {
      return <Clock className="w-5 h-5 text-yellow-600" />;
    } else {
      return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    if (completedCount === totalCount) {
      return "Task Finished";
    } else if (completedCount > 0) {
      return `In Progress (${completedCount}/${totalCount} complete)`;
    } else {
      return "Starting...";
    }
  };

  return (
    <div className="container mx-auto px-4 pb-6">
      <Card className="border-2 border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/50">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <CardTitle className="text-xl font-bold text-blue-900 dark:text-blue-100">
                {getStatusText()}
              </CardTitle>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-2 text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100"
            >
              <FileText className="w-4 h-4" />
              View Documentation
              {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
          {completedCount < totalCount && (
            <div className="text-sm text-blue-700 dark:text-blue-300 mt-2">
              Documentation collection is {completedCount === totalCount ? 'complete' : 'in progress'}...
            </div>
          )}
        </CardHeader>
        
        {expanded && (
          <CardContent className="pt-0">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-blue-700 dark:text-blue-300">Loading documentation...</span>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(browsers).map(([browserKey, browserInfo]) => {
                  const docs = browserInfo.documentation || sessionData?.browsers?.[browserKey]?.documentation;
                  const status = browserInfo.status || sessionData?.browsers?.[browserKey]?.status;
                  
                  return (
                    <div key={browserKey} className="border border-blue-200 dark:border-blue-700 rounded-lg p-4 bg-white dark:bg-gray-800">
                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">{browserKey}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          status === 'completed' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                            : status === 'failed'
                            ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
                            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                        }`}>
                          {status || 'pending'}
                        </span>
                      </div>
                      
                      {docs ? (
                        <div className="space-y-2">
                          <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                            <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono">
                              {docs.response}
                            </pre>
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            Completed at: {new Date(docs.timestamp).toLocaleString()}
                          </div>
                        </div>
                      ) : browserInfo.error ? (
                        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
                          <p className="text-sm text-red-800 dark:text-red-300">
                            Error: {browserInfo.error}
                          </p>
                        </div>
                      ) : (
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                          <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                            Documentation collection in progress...
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
                
                {sessionData?.task && (
                  <div className="border-t border-blue-200 dark:border-blue-700 pt-4 mt-4">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Original Task</h3>
                    <p className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                      {sessionData.task}
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        )}
      </Card>
    </div>
  );
}