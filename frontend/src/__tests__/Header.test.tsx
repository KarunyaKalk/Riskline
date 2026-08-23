import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from '../components/Header';
import { AuthProvider } from '../context/AuthContext';

class MockEventSource {
  onmessage: any = null;
  onopen: any = null;
  onerror: any = null;
  close = vi.fn();
}

global.EventSource = MockEventSource as any;

describe('Header Component', () => {
  it('renders Mission Control branding and AI Assistant toggle button', async () => {
    const handleToggleChat = vi.fn();

    await act(async () => {
      render(
        <AuthProvider>
          <Header onToggleChat={handleToggleChat} />
        </AuthProvider>
      );
    });

    expect(screen.getByText(/DevOps Risk Mission Control/i)).toBeDefined();
    expect(screen.getByText(/AI Risk Assistant/i)).toBeDefined();

    const chatButton = screen.getByRole('button', { name: /Toggle AI Risk Assistant Drawer/i });
    fireEvent.click(chatButton);
    expect(handleToggleChat).toHaveBeenCalledTimes(1);
  });
});
