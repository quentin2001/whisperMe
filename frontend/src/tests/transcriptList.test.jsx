import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TranscriptList from '../components/podcast/TranscriptList.jsx';
import { I18nProvider } from '../contexts/I18nContext.jsx';

const renderWithI18n = (ui) => {
  return render(
    <I18nProvider>
      {ui}
    </I18nProvider>
  );
};

describe('TranscriptList sentence rendering and highlighting', () => {
  const mockJumpToTimeSeconds = vi.fn();
  
  const paragraphs = [
    {
      id: 'p-0',
      speaker: 'Speaker 1',
      timeStart: '00:00',
      timeEnd: '00:10',
      text: 'Hello world. Welcome to the show.',
      start_time: 0.0,
      end_time: 10.0,
      sentences: [
        { start: 0.0, end: 5.0, text: 'Hello world.' },
        { start: 5.0, end: 10.0, text: 'Welcome to the show.' }
      ]
    }
  ];

  const defaultProps = {
    activeTask: { status: 'completed' },
    paragraphs,
    searchWord: '',
    currentTime: 2.0, // Should make sentence 0 ('Hello world.') active
    activeBubbleRef: React.createRef(),
    jumpToTimeSeconds: mockJumpToTimeSeconds
  };

  it('renders all sentences inline within spans', () => {
    renderWithI18n(<TranscriptList {...defaultProps} />);
    
    const sentence1 = screen.getByText('Hello world.');
    const sentence2 = screen.getByText('Welcome to the show.');
    
    expect(sentence1).toBeDefined();
    expect(sentence2).toBeDefined();
    expect(sentence1.tagName).toBe('SPAN');
    expect(sentence2.tagName).toBe('SPAN');
  });

  it('highlights the active sentence based on closest start time matching', () => {
    // Current time is 2.0.
    // Sentence 0 start is 0.0 (diff 2.0)
    // Sentence 1 start is 5.0 (diff 3.0)
    // So Sentence 0 is closer and should be highlighted as active.
    const { rerender } = renderWithI18n(<TranscriptList {...defaultProps} />);
    
    const sentence1 = screen.getByText('Hello world.');
    const sentence2 = screen.getByText('Welcome to the show.');
    
    expect(sentence1.className).toContain('bg-[var(--accent-red)]/20');
    expect(sentence1.className).toContain('text-[var(--text-primary)]');
    expect(sentence1.className).toContain('font-bold');
    
    expect(sentence2.className).toContain('text-[var(--text-secondary)]');
    expect(sentence2.className).not.toContain('bg-[var(--accent-red)]/20');

    // Change current time to 8.0, making sentence 1 (start 5.0, diff 3.0 vs sentence 0 diff 8.0) active
    rerender(
      <I18nProvider>
        <TranscriptList {...defaultProps} currentTime={8.0} />
      </I18nProvider>
    );

    const updatedSentence1 = screen.getByText('Hello world.');
    const updatedSentence2 = screen.getByText('Welcome to the show.');

    expect(updatedSentence2.className).toContain('bg-[var(--accent-red)]/20');
    expect(updatedSentence2.className).toContain('font-bold');
    expect(updatedSentence1.className).toContain('text-[var(--text-secondary)]');
  });

  it('calls jumpToTimeSeconds with sentence start time on sentence click', () => {
    mockJumpToTimeSeconds.mockClear();
    renderWithI18n(<TranscriptList {...defaultProps} />);
    
    const sentence2 = screen.getByText('Welcome to the show.');
    fireEvent.click(sentence2);
    
    expect(mockJumpToTimeSeconds).toHaveBeenCalledWith(5.0);
  });
});
