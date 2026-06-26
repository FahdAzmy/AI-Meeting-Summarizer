import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <h2 className="mb-4 text-2xl font-bold text-[var(--text-primary)]">Meeting Not Found</h2>
      <p className="mb-8 text-[var(--text-secondary)]">
        The meeting you are looking for does not exist or has been removed.
      </p>
      <Link href="/history">
        <Button>Return to History</Button>
      </Link>
    </div>
  );
}
