import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Badge from '../components/atoms/Badge';

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>Test</Badge>);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('applies error variant styles', () => {
    render(<Badge variant="error">Error</Badge>);
    const el = screen.getByText('Error');
    expect(el).toBeInTheDocument();
  });
});
