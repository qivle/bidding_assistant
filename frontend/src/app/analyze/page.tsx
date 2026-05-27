"use client";

import { useState, useRef } from "react";
import { useAIConfig } from "@/hooks/use-ai-config";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Label } from "@/components/ui/label";

interface FatalFlawItem {
  description: string;
  page: string;
}

interface FatalFlawCategory {
  category: string;
  items: FatalFlawItem[];
}

interface AnalysisData {
  projectInfo: { name: string; number: string; budget: string };
  fatalFlaws: FatalFlawCategory[];
  volumes: {
    volume_name: string;
    items: { name: string; is_required: boolean; template_text?: string }[];
  }[];
}

export default function AnalyzePage() {
  const { config, isLoaded } = useAIConfig();
  const [file, setFile] = useState<File | null>(null);
  const [attachment, setAttachment] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisData | null>(null);
  
  // State for the Fatal Flaw Checklist
  const [checkedFlaws, setCheckedFlaws] = useState<{ [key: string]: boolean }>({});
  const [isSaved, setIsSaved] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      toast.error("请先选择一个招标文件 (PDF/DOCX)");
      return;
    }
    if (!config.apiKey) {
      toast.error("未配置 API Key，请先前往配置中心设置大模型参数");
      return;
    }

    setIsAnalyzing(true);
    setResult(null);
    setCheckedFlaws({});

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("config", JSON.stringify(config));

      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "解析请求失败");
      }

      const data = await res.json();
      setResult(data.data);
      toast.success("解析成功！", { description: "已成功提取实质性条款和文件要求。" });
    } catch (error: any) {
      console.error(error);
      toast.error("解析失败", { description: error.message });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateWord = async (volumeIndex: number, volumeName: string) => {
    if (!result) return;
    try {
      toast.info(`正在组装 ${volumeName} ...`, { description: "如果有附件或需要切割原文档，这可能需要几十秒的时间。" });
      
      const formData = new FormData();
      formData.append("data", JSON.stringify(result));
      formData.append("volume_index", volumeIndex.toString());
      if (attachment) {
        formData.append("attachment", attachment);
      }
      if (file) {
        formData.append("source_file", file);
      }

      const res = await fetch("http://localhost:8000/api/generate", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("生成失败，请检查后端服务");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${result.projectInfo?.name || '政企投标文件'}_${volumeName}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success(`${volumeName} 已成功下载！`, { description: "请打开 Word 进行二次编辑。" });
    } catch (err: any) {
      toast.error("生成失败", { description: err.message });
    }
  };

  const saveProject = async () => {
    if (!result) return;
    try {
      const res = await fetch("http://localhost:8000/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(result)
      });
      if (!res.ok) throw new Error();
      setIsSaved(true);
      toast.success("已存入历史项目库", { description: "您现在可以前往项目库查看" });
    } catch (e) {
      toast.error("保存失败");
    }
  };

  const allFlawsChecked = result 
    ? result.fatalFlaws.length === 0 || result.fatalFlaws.every((cat, cIdx) => cat.items.every((_, iIdx) => checkedFlaws[`${cIdx}-${iIdx}`]))
    : false;

  if (!isLoaded) return null;

  return (
    <div className="container mx-auto p-4 md:p-8 space-y-8 max-w-6xl">
      <div className="grid md:grid-cols-12 gap-8">
        
        {/* Left Column: Upload & Actions */}
        <div className="md:col-span-4 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>新建解析任务</CardTitle>
              <CardDescription>上传招标文件原件 (PDF 或 Word)，系统将自动调用大模型进行拆解。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>选择文件</Label>
                <Input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
              </div>
              <Button 
                onClick={handleAnalyze} 
                disabled={isAnalyzing || !file} 
                className="w-full"
                size="lg"
              >
                {isAnalyzing ? "正在智能拆解中..." : "开始解析"}
              </Button>
            </CardContent>
          </Card>

                <div className="space-y-2">
                  <Label className="text-xs text-slate-500">上传资质/证明文件 (可选 PDF)</Label>
                  <Input type="file" accept=".pdf" onChange={(e) => setAttachment(e.target.files?.[0] || null)} />
                  <p className="text-[10px] text-slate-400">系统会在生成的特定分册中自动将 PDF 转为多张高清图片并按顺序插入。</p>
                </div>
                {!allFlawsChecked && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                    请先在右侧自查列表中确认所有致命风险条款，再进行下载。
                  </div>
                )}
        </div>

        {/* Right Column: Results Dashboard */}
        <div className="md:col-span-8">
          {!result && !isAnalyzing && (
            <div className="h-full min-h-[400px] flex items-center justify-center border-2 border-dashed rounded-xl text-slate-400 p-8 text-center">
              请在左侧上传招标文件并点击解析。
              <br/>注意：长文档可能需要 15-30 秒的 AI 处理时间。
            </div>
          )}

          {isAnalyzing && (
            <div className="h-full min-h-[400px] flex flex-col items-center justify-center space-y-4 rounded-xl bg-slate-50 border p-8 animate-pulse">
              <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
              <p className="text-slate-600 font-medium">多模态引擎正在深度阅读文档...</p>
              <p className="text-sm text-slate-400">正在定位评标办法与实质性响应条款 (★/▲)</p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Project Info */}
              <Card>
                <CardHeader className="pb-4 border-b">
                  <CardTitle>项目基础信息</CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4 pt-4">
                  <div>
                    <span className="text-sm text-slate-500">项目名称</span>
                    <p className="font-medium">{result.projectInfo.name || "未找到"}</p>
                  </div>
                  <div>
                    <span className="text-sm text-slate-500">项目编号</span>
                    <p className="font-medium">{result.projectInfo.number || "未找到"}</p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-sm text-slate-500">项目预算</span>
                    <p className="font-medium text-orange-600">{result.projectInfo.budget || "未找到"}</p>
                  </div>
                </CardContent>
              </Card>

              {/* Fatal Flaws Checklist */}
              <Card className="border-red-200 shadow-sm">
                <CardHeader className="bg-red-50/50 pb-4 border-b border-red-100">
                  <CardTitle className="text-red-600 flex items-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                    致命风险雷达 (必须全部确认)
                  </CardTitle>
                  <CardDescription className="text-red-800/80">以下条款带有★或▲符号，未响应将直接废标！</CardDescription>
                </CardHeader>
                <CardContent className="pt-4 space-y-3">
                  {result.fatalFlaws.length === 0 ? (
                    <p className="text-sm text-slate-500">太棒了，本次扫描未发现明确的带星号强制废标条款。</p>
                  ) : (
                    result.fatalFlaws.map((cat, cIdx) => (
                      <div key={cIdx} className="space-y-2 mb-4">
                        <h4 className="font-semibold text-slate-800 text-sm border-l-4 border-red-500 pl-2">{cat.category}</h4>
                        <div className="space-y-2 pl-3">
                          {cat.items.map((item, iIdx) => {
                            const flawKey = `${cIdx}-${iIdx}`;
                            return (
                              <div key={iIdx} className="flex items-start gap-3 p-3 rounded-lg border bg-white hover:bg-slate-50 transition-colors">
                                <input 
                                  type="checkbox" 
                                  id={`flaw-${flawKey}`}
                                  className="mt-1 w-5 h-5 accent-red-600 cursor-pointer flex-shrink-0"
                                  checked={checkedFlaws[flawKey] || false}
                                  onChange={(e) => setCheckedFlaws({...checkedFlaws, [flawKey]: e.target.checked})}
                                />
                                <label htmlFor={`flaw-${flawKey}`} className={`text-sm cursor-pointer ${checkedFlaws[flawKey] ? 'text-slate-400 line-through' : 'text-slate-700 font-medium'} flex-grow`}>
                                  {item.description}
                                </label>
                                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded whitespace-nowrap">
                                  {item.page}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-blue-800 text-lg">投标文件多重分册结构</CardTitle>
                  <CardDescription>由多智能体深度解析提取，并自动检索模板</CardDescription>
                </div>
                <Button variant={isSaved ? "secondary" : "default"} onClick={saveProject} disabled={isSaved}>
                  {isSaved ? "已存入项目库" : "存入历史项目库"}
                </Button>
              </CardHeader>
              <CardContent className="space-y-6">
                {result.volumes?.map((vol, vidx) => (
                  <div key={vidx} className="space-y-3 border p-4 rounded-xl bg-slate-50/50">
                    <div className="flex items-center justify-between bg-slate-100 p-3 rounded-lg">
                      <h3 className="font-bold text-slate-800">{vol.volume_name}</h3>
                      <Button 
                        size="sm" 
                        disabled={!allFlawsChecked}
                        onClick={() => handleGenerateWord(vidx, vol.volume_name)}
                        className={allFlawsChecked ? "bg-blue-600 hover:bg-blue-700" : ""}
                      >
                        下载此分册 (Word)
                      </Button>
                    </div>
                    <ul className="grid gap-2 pl-2">
                      {vol.items.map((item, iidx) => (
                        <li key={iidx} className="flex flex-col text-sm bg-white border p-3 rounded-md shadow-sm">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-slate-700">{item.name}</span>
                            {item.is_required && <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded">必须提供</span>}
                          </div>
                          {item.template_text && (
                            <div className="mt-2 text-xs text-green-700 bg-green-50 p-2 rounded">
                              <span className="font-bold">✓ 找到模板特征词：</span>
                              <span className="ml-1 italic">{item.template_text}</span>
                              <p className="text-slate-400 mt-1">生成 Word 时将尝试去原文档中自动切割克隆其格式排版。</p>
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
          )}
        </div>
      </div>
    </div>
  );
}
