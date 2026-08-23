import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Navigation } from '../components/Navigation';
import { AuthProvider } from '../context/AuthContext';

describe('Navigation Component', () => {
  it('renders standard navigation tabs and handles tab change', () => {
    const handleTabChange = vi.fn();
    render(
      <AuthProvider>
        <Navigation activeTab="dashboard" onTabChange={handleTabChange} />
      </AuthProvider>
    );

    expect(screen.getByText('Overview')).toBeDefined();
    expect(screen.getByText('Changes & Risk')).toBeDefined();
    expect(screen.getByText('Notes & Ideas')).toBeDefined();
    expect(screen.getByText('Team Roster')).toBeDefined();

    const changesBtn = screen.getByText('Changes & Risk');
    fireEvent.click(changesBtn);
    expect(handleTabChange).toHaveBeenCalledWith('changes');
  });
});
