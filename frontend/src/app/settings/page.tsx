"use client";

import { useState, useEffect } from "react";
import { useAIConfig } from "@/hooks/use-ai-config";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function SettingsPage() {
  const { config, saveConfig, isLoaded } = useAIConfig();
  const [formData, setFormData] = useState(config);

  useEffect(() => {
    if (isLoaded) {
      setFormData(config);
    }
  }, [config, isLoaded]);

  const handleSave = () => {
    saveConfig(formData);
    toast.success("AI 模型配置已保存", {
      description: "系统后续处理将使用新的模型配置进行接口调用。",
    });
  };

  if (!isLoaded) return null; // Avoid hydration mismatch

  return (
    <div className="container mx-auto p-8 max-w-2xl">
      <Card className="shadow-lg border-t-4 border-t-primary">
        <CardHeader>
          <CardTitle className="text-2xl">AI 模型配置中心</CardTitle>
          <CardDescription>
            您可以动态配置兼容 OpenAI 协议的大模型接口。例如 DeepSeek、Kimi 月之暗面、通义千问等。无需修改代码，立即生效。
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="baseUrl">接口地址 (Base URL)</Label>
            <Input 
              id="baseUrl" 
              placeholder="https://api.deepseek.com/v1" 
              value={formData.baseUrl}
              onChange={(e) => setFormData({...formData, baseUrl: e.target.value})}
            />
            <p className="text-xs text-muted-foreground">如果您使用的是聚合代理，请确保包含 /v1 后缀。</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="apiKey">API 秘钥 (API Key)</Label>
            <Input 
              id="apiKey" 
              type="password"
              placeholder="sk-..." 
              value={formData.apiKey}
              onChange={(e) => setFormData({...formData, apiKey: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="model">调用模型名称 (Model Name)</Label>
            <Input 
              id="model" 
              placeholder="deepseek-chat 或 moonshot-v1-8k" 
              value={formData.model}
              onChange={(e) => setFormData({...formData, model: e.target.value})}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end bg-muted/50 p-6 rounded-b-xl">
          <Button onClick={handleSave} size="lg">
            保存配置
          </Button>
        </CardFooter>
      </Card>
      
      <div className="mt-8 space-y-4">
        <h3 className="text-lg font-medium">常用模型推荐配置：</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="p-4">
              <CardTitle className="text-base text-blue-600">DeepSeek (性价比极高)</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 text-sm space-y-1">
              <p>Base URL: <code>https://api.deepseek.com/v1</code></p>
              <p>Model: <code>deepseek-chat</code></p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="p-4">
              <CardTitle className="text-base text-purple-600">Kimi (月之暗面 长文本)</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 text-sm space-y-1">
              <p>Base URL: <code>https://api.moonshot.cn/v1</code></p>
              <p>Model: <code>moonshot-v1-32k</code></p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
