import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg text-center">
        <h1 className="text-4xl font-bold mb-6 text-gray-800">Welcome to CodexWeb Agent</h1>
        <p className="text-gray-600 mb-8">
          Your intelligent assistant for web interactions
        </p>
        <Link href="/chat" passHref>
          <Button className="w-full py-6 text-lg">
            Start Chatting
          </Button>
        </Link>
      </div>
    </div>
  );
}
