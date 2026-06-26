import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MeetingForm } from '../../../src/components/dashboard/MeetingForm';
import { api } from '../../../src/lib/api';

describe('MeetingForm', () => {
  beforeEach(() => {
    jest.spyOn(api, 'getTeams').mockResolvedValue([]);
    jest.spyOn(api, 'getMembers').mockResolvedValue([]);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders input fields and submit button', async () => {
    render(<MeetingForm onSubmit={jest.fn()} />);
    expect(screen.getByPlaceholderText(/https:\/\/meet\.google\.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Sprint Planning/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start session/i })).toBeInTheDocument();
    await waitFor(() => expect(api.getTeams).toHaveBeenCalledTimes(1));
  });

  it('disables submit on empty and validates invalid url submissions', async () => {
    const handleSubmit = jest.fn();
    render(<MeetingForm onSubmit={handleSubmit} />);
    
    // Empty link disables button
    expect(screen.getByRole('button', { name: /Start session/i })).toBeDisabled();
    
    // Type an invalid link
    fireEvent.change(screen.getByPlaceholderText(/https:\/\/meet\.google\.com/i), { target: { value: 'not-a-link' } });
    
    // Button should be enabled now
    expect(screen.getByRole('button', { name: /Start session/i })).toBeEnabled();
    
    // Click submit
    fireEvent.submit(screen.getByRole('button', { name: /Start session/i }).closest('form')!);
    
    expect(await screen.findByText(/Valid meeting link is required/i)).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
    await waitFor(() => expect(api.getMembers).toHaveBeenCalledTimes(1));
  });

  it('loads teams and members once when the parent re-renders', async () => {
    const { rerender } = render(<MeetingForm onSubmit={jest.fn()} />);

    await waitFor(() => {
      expect(api.getTeams).toHaveBeenCalledTimes(1);
      expect(api.getMembers).toHaveBeenCalledTimes(1);
    });

    rerender(<MeetingForm onSubmit={jest.fn()} />);

    expect(api.getTeams).toHaveBeenCalledTimes(1);
    expect(api.getMembers).toHaveBeenCalledTimes(1);
  });
});
