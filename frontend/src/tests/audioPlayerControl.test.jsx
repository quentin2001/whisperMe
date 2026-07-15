import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AudioPlayerControl from '../components/podcast/AudioPlayerControl.jsx';
import { I18nProvider } from '../contexts/I18nContext.jsx';

// Simple mock/wrapper for I18n if needed, or wrap in real I18nProvider
const renderWithI18n = (ui) => {
  return render(
    <I18nProvider>
      {ui}
    </I18nProvider>
  );
};

describe('AudioPlayerControl speed and jump controls', () => {
  const defaultProps = {
    activeTask: {
      title: 'Test Podcast',
      audio_url: '/audio/test.mp3',
    },
    isPlaying: false,
    togglePlay: vi.fn(),
    currentTime: 100,
    duration: 300,
    playbackRate: 1.0,
    handleProgressChange: vi.fn(),
    handleJump: vi.fn(),
    handleSpeedChange: vi.fn(),
    isMuted: false,
    volume: 0.8,
    handleVolumeInput: vi.fn(),
    toggleMute: vi.fn(),
    formatTime: (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`,
    isTriggeringRestore: false,
    handleRedownloadAudio: vi.fn(),
  };

  it('renders a speed dropdown button showing the current speed', () => {
    renderWithI18n(<AudioPlayerControl {...defaultProps} />);
    
    const dropdownButton = screen.getByText('1.0x');
    expect(dropdownButton).toBeDefined();
  });

  it('opens speed choices popover when clicked and calls handleSpeedChange on choice click', () => {
    const handleSpeedChange = vi.fn();
    renderWithI18n(<AudioPlayerControl {...defaultProps} handleSpeedChange={handleSpeedChange} />);
    
    const dropdownButton = screen.getByText('1.0x');
    fireEvent.click(dropdownButton);
    
    const speedOption = screen.getByText('1.5x');
    expect(speedOption).toBeDefined();
    
    fireEvent.click(speedOption);
    expect(handleSpeedChange).toHaveBeenCalledWith(1.5);
  });

  it('renders four jump buttons with correct labels and icons', () => {
    renderWithI18n(<AudioPlayerControl {...defaultProps} />);
    
    // Jump buttons should be: -15s, -5s, +10s, +30s
    const btn15sBack = screen.getByText('-15s');
    const btn5sBack = screen.getByText('-5s');
    const btn10sForward = screen.getByText('+10s');
    const btn30sForward = screen.getByText('+30s');

    expect(btn15sBack).toBeDefined();
    expect(btn5sBack).toBeDefined();
    expect(btn10sForward).toBeDefined();
    expect(btn30sForward).toBeDefined();
  });

  it('calls handleJump with correct delta when jump buttons are clicked', () => {
    const handleJump = vi.fn();
    renderWithI18n(<AudioPlayerControl {...defaultProps} handleJump={handleJump} />);
    
    fireEvent.click(screen.getByText('-15s'));
    expect(handleJump).toHaveBeenLastCalledWith(-15);

    fireEvent.click(screen.getByText('-5s'));
    expect(handleJump).toHaveBeenLastCalledWith(-5);

    fireEvent.click(screen.getByText('+10s'));
    expect(handleJump).toHaveBeenLastCalledWith(10);

    fireEvent.click(screen.getByText('+30s'));
    expect(handleJump).toHaveBeenLastCalledWith(30);
  });
});
