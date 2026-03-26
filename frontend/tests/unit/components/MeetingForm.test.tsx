import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MeetingForm } from '../../../src/components/dashboard/MeetingForm';

describe('MeetingForm', () => {
  it('renders input fields and submit button', () => {
    render(<MeetingForm onSubmit={jest.fn()} />);
    expect(screen.getByPlaceholderText(/https:\/\/meet\.google\.com/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Separated by commas/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Join Meeting/i })).toBeInTheDocument();
  });

  it('disables submit on empty and validates invalid url submissions', async () => {
    const handleSubmit = jest.fn();
    render(<MeetingForm onSubmit={handleSubmit} />);
    
    // Empty link disables button
    expect(screen.getByRole('button', { name: /Join Meeting/i })).toBeDisabled();
    
    // Type an invalid link
    fireEvent.change(screen.getByPlaceholderText(/https:\/\/meet\.google\.com/i), { target: { value: 'not-a-link' } });
    
    // Button should be enabled now
    expect(screen.getByRole('button', { name: /Join Meeting/i })).toBeEnabled();
    
    // Click submit
    // Using submit on form avoids internal browser prevention of type="url" submissions
    fireEvent.submit(screen.getByRole('button', { name: /Join Meeting/i }).closest('form')!);
    
    expect(await screen.findByText(/Valid meeting link is required/i)).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
  });
});
