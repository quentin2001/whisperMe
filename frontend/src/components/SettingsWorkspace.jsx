import React from 'react';

export default function SettingsWorkspace({
  configSubTab,
  setConfigSubTab,
  configData,
  setConfigData,
  themeMode,
  setThemeMode,
  language,
  setLanguage,
  autoSaveEnabled,
  setAutoSaveEnabled,
  saveStatus,
  lightTheme,
  setLightTheme,
  darkTheme,
  setDarkTheme,
  lightPresetName,
  setLightPresetName,
  darkPresetName,
  setDarkPresetName,
  PRESETS,
  handleSaveConfig,
  t
}) {
  const handleInputChange = (field, val) => {
    setConfigData(prev => ({ ...prev, [field]: val }));
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-lg animate-fade-in relative z-10">
      <div className="mb-xl flex justify-between items-end">
        <div>
          <h2 className="font-display-lg text-display-lg text-primary uppercase">System Settings</h2>
          <p className="font-mono-data text-[12px] text-on-surface-variant mt-sm tracking-widest uppercase">CONFIGURATION OVERRIDE // SYSTEM v2.4.0-STABLE</p>
        </div>
        <div className="flex gap-md">
          <button onClick={handleSaveConfig} className="bg-primary hover:bg-[#b72216] px-lg py-sm font-label-caps text-[12px] text-on-primary active:scale-95 transition-all">SAVE CHANGES</button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
        {/* ASR Settings Module */}
        <section className="brutalist-card">
          <div className="brutalist-card-header flex justify-between items-center">
            <span className="font-label-caps text-on-primary">ASR SETTINGS</span>
            <span className="material-symbols-outlined text-[18px] text-on-primary">mic</span>
          </div>
          <div className="p-lg space-y-lg">
            <div className="space-y-xs">
              <label className="font-label-caps text-on-surface-variant">ENGINE MODE</label>
              <select value={configData.asr_mode} onChange={(e) => handleInputChange('asr_mode', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none">
                <option value="local">LOCAL OFFLINE (FASTER-WHISPER)</option>
                <option value="online">ONLINE API</option>
              </select>
            </div>
            
            {configData.asr_mode === 'local' && (
              <>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">LOCAL MODEL PATH</label>
                  <input type="text" value={configData.local_whisper_model_path || ''} onChange={(e) => handleInputChange('local_whisper_model_path', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">HF TOKEN (DIARIZATION)</label>
                  <input type="password" value={configData.hf_token || ''} onChange={(e) => handleInputChange('hf_token', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
              </>
            )}

            {configData.asr_mode === 'online' && (
              <>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">API BASE URL</label>
                  <input type="text" value={configData.online_base_url || ''} onChange={(e) => handleInputChange('online_base_url', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">MODEL ID</label>
                  <input type="text" value={configData.online_model || ''} onChange={(e) => handleInputChange('online_model', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">API KEY</label>
                  <input type="password" value={configData.online_api_key || ''} onChange={(e) => handleInputChange('online_api_key', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
              </>
            )}
          </div>
        </section>

        {/* LLM Summary Settings */}
        <section className="brutalist-card">
          <div className="brutalist-card-header flex justify-between items-center">
            <span className="font-label-caps text-on-primary">LLM SUMMARY SETTINGS</span>
            <span className="material-symbols-outlined text-[18px] text-on-primary">auto_awesome</span>
          </div>
          <div className="p-lg space-y-lg">
            <div className="space-y-xs">
              <label className="font-label-caps text-on-surface-variant">LLM MODE</label>
              <select value={configData.summary_mode} onChange={(e) => handleInputChange('summary_mode', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none">
                <option value="local">LOCAL (OLLAMA)</option>
                <option value="online">ONLINE API (OPENAI COMPATIBLE)</option>
              </select>
            </div>

            {configData.summary_mode === 'local' && (
              <>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">LOCAL API URL</label>
                  <input type="text" value={configData.ollama_url || ''} onChange={(e) => handleInputChange('ollama_url', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">MODEL ID</label>
                  <input type="text" value={configData.ollama_model || ''} onChange={(e) => handleInputChange('ollama_model', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
              </>
            )}

            {configData.summary_mode === 'online' && (
              <>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">ONLINE API BASE URL</label>
                  <input type="text" value={configData.online_summary_base_url || ''} onChange={(e) => handleInputChange('online_summary_base_url', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">ONLINE MODEL ID</label>
                  <input type="text" value={configData.online_summary_model || ''} onChange={(e) => handleInputChange('online_summary_model', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">API KEY</label>
                  <input type="password" value={configData.online_summary_api_key || ''} onChange={(e) => handleInputChange('online_summary_api_key', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
              </>
            )}
          </div>
        </section>

        {/* System Notifications */}
        <section className="brutalist-card">
          <div className="brutalist-card-header flex justify-between items-center">
            <span className="font-label-caps text-on-primary">SYSTEM NOTIFICATIONS</span>
            <span className="material-symbols-outlined text-[18px] text-on-primary">hub</span>
          </div>
          <div className="p-lg space-y-md">
            <div className="flex justify-between items-center p-sm border-b border-outline-variant/30">
              <div className="flex flex-col">
                <span className="font-body-lg text-body-lg text-on-surface">Windows Toast Notifications</span>
                <span className="text-[10px] font-mono-data text-on-surface-variant uppercase tracking-widest mt-1">Push notification on desktop</span>
              </div>
              <input type="checkbox" checked={configData.enable_win_notification} onChange={(e) => handleInputChange('enable_win_notification', e.target.checked)} className="tactical-toggle" />
            </div>
            <div className="flex justify-between items-center p-sm border-b border-outline-variant/30">
              <div className="flex flex-col">
                <span className="font-body-lg text-body-lg text-on-surface">Email Alerts</span>
                <span className="text-[10px] font-mono-data text-on-surface-variant uppercase tracking-widest mt-1">Send mail alerts (SMTP)</span>
              </div>
              <input type="checkbox" checked={configData.enable_email_notification} onChange={(e) => handleInputChange('enable_email_notification', e.target.checked)} className="tactical-toggle" />
            </div>

            {configData.enable_email_notification && (
              <div className="grid grid-cols-2 gap-md mt-4">
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">SMTP SERVER</label>
                  <input type="text" value={configData.smtp_server || ''} onChange={(e) => handleInputChange('smtp_server', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">PORT</label>
                  <input type="number" value={configData.smtp_port || 465} onChange={(e) => handleInputChange('smtp_port', Number(e.target.value))} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">USERNAME</label>
                  <input type="text" value={configData.smtp_username || ''} onChange={(e) => handleInputChange('smtp_username', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">PASSWORD</label>
                  <input type="password" value={configData.smtp_password || ''} onChange={(e) => handleInputChange('smtp_password', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">SENDER EMAIL</label>
                  <input type="text" value={configData.smtp_sender || ''} onChange={(e) => handleInputChange('smtp_sender', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-on-surface-variant">RECEIVER EMAIL</label>
                  <input type="text" value={configData.notification_email || ''} onChange={(e) => handleInputChange('notification_email', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Advanced Configs */}
        <section className="brutalist-card">
          <div className="brutalist-card-header flex justify-between items-center">
            <span className="font-label-caps text-on-primary">ADVANCED DEPENDENCIES</span>
            <span className="material-symbols-outlined text-[18px] text-on-primary">terminal</span>
          </div>
          <div className="p-lg space-y-lg">
            <div className="space-y-xs">
              <label className="font-label-caps text-on-surface-variant">FFMPEG EXECUTABLE PATH</label>
              <input type="text" value={configData.ffmpeg_path || ''} onChange={(e) => handleInputChange('ffmpeg_path', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
            </div>
            <div className="space-y-xs">
              <label className="font-label-caps text-on-surface-variant">FFMPEG BIN DIRECTORY</label>
              <input type="text" value={configData.ffmpeg_bin_dir || ''} onChange={(e) => handleInputChange('ffmpeg_bin_dir', e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none" />
            </div>
            <div className="space-y-xs">
              <label className="font-label-caps text-on-surface-variant">LANGUAGE PREFERENCE</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)} className="w-full bg-black border-b border-primary-container text-primary font-mono-data p-sm focus:border-primary outline-none">
                <option value="zh-CN">简体中文 (ZH-CN)</option>
                <option value="en">ENGLISH (EN-US)</option>
              </select>
            </div>
            <div className="flex justify-between items-center">
              <label className="font-label-caps text-on-surface-variant">AUTO-SAVE CHANGES</label>
              <input type="checkbox" checked={autoSaveEnabled} onChange={(e) => setAutoSaveEnabled(e.target.checked)} className="tactical-toggle" />
            </div>
          </div>
        </section>

        {/* Status Canvas */}
        <section className="md:col-span-2 brutalist-card h-48 relative overflow-hidden flex items-center justify-center">
          <div className="scanline"></div>
          <div className="relative z-10 text-center">
            <h3 className="font-headline-lg text-headline-lg text-primary uppercase font-black">System Ready</h3>
            <p className="font-mono-data text-mono-data tracking-widest text-on-surface mt-2 animate-pulse">{saveStatus === 'saving' ? 'WRITING OVERRIDE...' : saveStatus === 'saved' ? 'CONFIGURATION APPLIED' : saveStatus === 'unsaved' ? 'UNSAVED MODIFICATIONS DETECTED' : 'PENDING COMMAND INPUT...'}</p>
          </div>
        </section>
      </div>
    </div>
  );
}
