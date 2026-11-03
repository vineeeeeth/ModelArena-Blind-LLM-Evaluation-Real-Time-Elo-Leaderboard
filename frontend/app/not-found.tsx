import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="container mx-auto flex min-h-[calc(100vh-16rem)] flex-col items-center justify-center text-center px-4">
      <h2 className="text-4xl font-extrabold tracking-tight">404 - Page Not Found</h2>
      <p className="mt-2 text-muted-foreground max-w-md">
        The page you are looking for doesn&apos;t exist or has been moved.
      </p>
      <Link href="/" className="mt-6">
        <Button>Return to Arena</Button>
      </Link>
    </div>
  );
}

