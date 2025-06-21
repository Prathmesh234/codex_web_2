'use client'
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function AuthFailurePage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <h1 style={{ fontWeight: 'bold', fontSize: 28, color: '#d32f2f', marginBottom: 10 }}>Login Unsuccessful</h1>
      <p style={{ fontSize: 18, color: '#555', marginBottom: 24 }}>We could not log you in with GitHub. Please try again.</p>
      <Link href="/">
        <Button variant="destructive" className="font-bold animate-pulse">
          Back to Login
        </Button>
      </Link>
    </div>
  );
} 