import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-4">Meeting Not Found</h2>
      <p className="text-gray-600 mb-8">
        The meeting you are looking for does not exist or has been removed.
      </p>
      <Link href="/history">
        <Button>Return to History</Button>
      </Link>
    </div>
  );
}
