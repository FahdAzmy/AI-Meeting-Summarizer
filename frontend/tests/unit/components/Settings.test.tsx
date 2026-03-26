import React from 'react';
import { render, screen } from '@testing-library/react';
import { StorageToggle } from '../../../src/components/settings/StorageToggle';
import { STTSelector } from '../../../src/components/settings/STTSelector';

describe('Settings Components', () => {
  it('StorageToggle renders correctly', () => {
    render(<StorageToggle value="database" onChange={jest.fn()} />);
    expect(screen.getByText(/database/i)).toBeInTheDocument();
  });

  it('STTSelector renders options', () => {
    render(<STTSelector value="whisper" onChange={jest.fn()} />);
    expect(screen.getByDisplayValue(/whisper/i)).toBeInTheDocument();
  });
});
