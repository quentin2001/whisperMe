import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SettingsView from '../views/SettingsView.jsx';
import { I18nProvider } from '../contexts/I18nContext.jsx';
import { useConfigStore } from '../store/configStore.js';

// Helper to render with i18n
const renderWithI18n = (ui) => {
  return render(
    <I18nProvider>
      {ui}
    </I18nProvider>
  );
};

// Mock global fetch
const mockTemplates = {
  "standard": {
    "name": "Standard Analysis",
    "name_en": "Standard Analysis",
    "description": "Built-in standard prompt template",
    "description_en": "Built-in standard prompt template",
    "is_builtin": true
  },
  "custom_123": {
    "name": "My Custom Template",
    "name_en": "My Custom Template",
    "description": "My custom prompt template description",
    "description_en": "My custom prompt template description",
    "is_builtin": false
  }
};

global.fetch = vi.fn((url, options) => {
  if (url.includes('/api/prompt/templates')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockTemplates)
    });
  }
  if (url.includes('/api/prompt/template/standard')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ id: "standard", prompt: "Standard content" })
    });
  }
  if (url.includes('/api/prompt/template/custom_123')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ id: "custom_123", prompt: "Custom content" })
    });
  }
  if (url.includes('/api/dependencies')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ ffmpeg: { available: true } })
    });
  }
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve({})
  });
});

describe('SettingsView UI implementation', () => {
  const defaultProps = {
    handleConfigChange: vi.fn(),
    handleSaveConfig: vi.fn(),
    onResetData: vi.fn(),
    handleSavePrompt: vi.fn(),
    handleResetPrompt: vi.fn(),
    onCheckVersion: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    useConfigStore.setState({
      configData: {
        language: "zh",
        local_whisper_model_path: "models/funasr",
        ollama_url: "http://localhost:11434",
        ollama_model: "qwen2.5:7b-instruct",
        asr_mode: "local",
        summary_mode: "local"
      },
      promptData: {
        prompt: "Standard content"
      }
    });
  });

  it('renders settings title and config sections', async () => {
    renderWithI18n(<SettingsView {...defaultProps} />);
    
    // Check titles
    expect(screen.getByText('ASR 引擎设置')).toBeDefined();
    expect(screen.getByText('LLM 总结大模型配置')).toBeDefined();
    expect(screen.getByText('AI 总结 Prompt 模板管理')).toBeDefined();
  });

  it('does NOT contain old recommendations buttons or registry loaders', async () => {
    renderWithI18n(<SettingsView {...defaultProps} />);

    // Old buttons
    const viewAsrRecBtn = screen.queryByText(/查看推荐本地 ASR/);
    const viewLlmRecBtn = screen.queryByText(/查看推荐本地 Ollama/);

    expect(viewAsrRecBtn).toBeNull();
    expect(viewLlmRecBtn).toBeNull();
  });

  it('opens Agent Setup Prompt modal for ASR and Ollama when clicking info buttons', async () => {
    renderWithI18n(<SettingsView {...defaultProps} />);

    // Find the help buttons
    const helpButtons = screen.getAllByTitle(/获取配置 AI Agent 提示词/);
    expect(helpButtons.length).toBe(2);

    // Click ASR help button
    fireEvent.click(helpButtons[0]);
    expect(screen.getByText('配置本地 ASR 的 AI Agent 提示词')).toBeDefined();
    expect(screen.getAllByText(/E:\/Projects\/whisperMe\/models\/funasr/).length).toBeGreaterThan(0);

    // Close modal
    const closeBtn = screen.getByText('关闭');
    fireEvent.click(closeBtn);
    expect(screen.queryByText('配置本地 ASR 的 AI Agent 提示词')).toBeNull();

    // Click LLM help button
    fireEvent.click(helpButtons[1]);
    expect(screen.getByText('配置本地 LLM 的 AI Agent 提示词')).toBeDefined();
    expect(screen.getAllByText(/http:\/\/localhost:11434/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/qwen2.5:7b-instruct/).length).toBeGreaterThan(0);
  });

  it('loads and lists templates in the sidebar', async () => {
    renderWithI18n(<SettingsView {...defaultProps} />);

    // Wait for templates to load
    await waitFor(() => {
      expect(screen.getByText('Standard Analysis')).toBeDefined();
      expect(screen.getByText('My Custom Template')).toBeDefined();
    });
  });
});
