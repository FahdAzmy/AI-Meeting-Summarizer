import React from 'react';
import { render, screen } from '@testing-library/react';
import { SummarySection } from '../../../src/components/detail/SummarySection';
import { ActionItemsTable } from '../../../src/components/detail/ActionItemsTable';

describe('DetailSections', () => {
  it('SummarySection renders correctly', () => {
    render(<SummarySection summary="This is a test summary." />);
    expect(screen.getByText('This is a test summary.')).toBeInTheDocument();
  });

  it('ActionItemsTable renders correctly', () => {
    const items = [{ assignee: 'Alice', task: 'Do this', deadline: null }];
    render(<ActionItemsTable actionItems={items} decisions={['We decided yes']} />);
    expect(screen.getByText(/Alice/i)).toBeInTheDocument();
    expect(screen.getByText(/Do this/i)).toBeInTheDocument();
    expect(screen.getByText(/We decided yes/i)).toBeInTheDocument();
  });
});
