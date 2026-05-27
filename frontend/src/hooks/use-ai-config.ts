import { useState, useEffect } from 'react';

export interface AIConfig {
  baseUrl: string;
  apiKey: string;
  model: string;
  model_flash: string;
}

const DEFAULT_CONFIG: AIConfig = {
  baseUrl: 'https://api.deepseek.com/v1',
  apiKey: '',
  model: 'deepseek-chat',
  model_flash: 'deepseek-chat',
};

export function useAIConfig() {
  const [config, setConfig] = useState<AIConfig>(DEFAULT_CONFIG);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('bidding_assistant_ai_config');
    if (stored) {
      try {
        setConfig(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse AI config', e);
      }
    }
    setIsLoaded(true);
  }, []);

  const saveConfig = (newConfig: AIConfig) => {
    setConfig(newConfig);
    localStorage.setItem('bidding_assistant_ai_config', JSON.stringify(newConfig));
  };

  return { config, saveConfig, isLoaded };
}
