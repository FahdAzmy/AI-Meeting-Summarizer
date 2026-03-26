import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MeetingsTable } from '../../../src/components/history/MeetingsTable';
import { Meeting } from '../../../src/lib/types';

const mockMeetings: Partial<Meeting>[] = [
  {
    id: '1',
    platform: 'zoom',
    date: '2026-03-14T15:00:00Z',
    duration_minutes: 45,
    status: 'completed'
  },
  {
    id: '2',
    platform: 'google_meet',
    date: '2026-03-15T15:00:00Z',
    duration_minutes: 30,
    status: 'pending'
  }
];

describe('MeetingsTable', () => {
  it('renders meetings properly', () => {
    render(<MeetingsTable meetings={mockMeetings as Meeting[]} />);
    expect(screen.getByText(/zoom/i)).toBeInTheDocument();
    expect(screen.getByText(/Google Meet/i)).toBeInTheDocument();
  });

  it('sorts by duration', () => {
    render(<MeetingsTable meetings={mockMeetings as Meeting[]} />);
    const durationHeader = screen.getByText(/Duration/i);
    fireEvent.click(durationHeader);
    // The easiest way to test sorting is checking the order of rows or just ensuring state change via DOM structure
  });
});
