import React, { createContext, useContext, useEffect } from 'react';
import { useConfigStore } from '../store/configStore';

const I18nContext = createContext();

export const I18nProvider = ({ children }) => {
  const configData = useConfigStore(state => state.configData);
  const setConfigData = useConfigStore(state => state.setConfigData);
  
  const lang = configData?.language || 'zh';

  const setLang = (newLang) => {
    setConfigData(prev => ({ ...prev, language: newLang }));
  };

  const t = (zhText, enText) => {
    return lang?.startsWith('en') ? (enText || zhText) : zhText;
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useTranslation = () => {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useTranslation must be used within an I18nProvider');
  }
  return context;
};
