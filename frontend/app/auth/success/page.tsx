'use client'
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
// @ts-ignore
import { Client, Account, Models } from 'appwrite';

const client = new Client()
  .setEndpoint(process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT)
  .setProject(process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID);
const account = new Account(client);

export default function AuthSuccessPage() {
  const router = useRouter();

  useEffect(() => {
    account.getSession('current')
      .then((session: Models.Session) => {
        if (session && session.provider === 'github') {
          router.replace('/chat');
        } else {
          router.replace('/auth/failure');
        }
      })
      .catch(() => {
        router.replace('/auth/failure');
      });
  }, [router]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <div style={{ fontWeight: 'bold', fontSize: 22, marginBottom: 12, letterSpacing: 1 }}>
        Checking authentication...
        <span className="animate-pulse" style={{ marginLeft: 8 }}>|</span>
      </div>
      <div style={{ color: '#888', fontSize: 16 }}>Please wait while we verify your login.</div>
    </div>
  );
} 