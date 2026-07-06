'use client'
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Client, Account, Models, OAuthProvider } from 'appwrite';
import { Button } from "@/components/ui/button";
import { Github } from "lucide-react";

const client = new Client()
  .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT ?? 'https://fra.cloud.appwrite.io/v1')
  .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID ?? '');
const account = new Account(client);

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    account.getSession('current')
      .then((session: Models.Session) => {
        if (session && session.provider === 'github') {
          router.replace('/chat');
        }
      })
      .catch(() => {
        // Suppress 401 errors from Appwrite after logout
        // No need to log or surface this error
      });
  }, [router]);

  const handleGithubLogin = () => {
    account.createOAuth2Session(
      OAuthProvider.Github,
      'http://localhost:3001/auth/success',
      'http://localhost:3001/auth/failure',
      ['user:email', 'repo']
    );
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg text-center">
        <h1 className="text-4xl font-bold mb-6 text-gray-800">Welcome to CodexWeb Agent</h1>
        <p className="text-gray-600 mb-8">
          Your intelligent assistant for web interactions
        </p>
        <Button className="w-full py-6 text-lg flex items-center justify-center gap-2" onClick={handleGithubLogin}>
          <Github className="h-15 w-15" /> Connect to GitHub
        </Button>
      </div>
    </div>
  );
}
