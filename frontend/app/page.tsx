import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Github } from "lucide-react";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg text-center">
        <h1 className="text-4xl font-bold mb-6 text-gray-800">Welcome to CodexWeb Agent</h1>
        <p className="text-gray-600 mb-8">
          Your intelligent assistant for web interactions
        </p>
        <Link href={`${apiUrl}/auth/github/login`} passHref>
          <Button className="w-full py-6 text-lg flex items-center justify-center gap-2">
            <Github className="h-5 w-5" /> Connect to GitHub
          </Button>
        </Link>
      </div>
    </div>
  );
}
