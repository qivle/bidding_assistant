"use client";

import { useState, useRef, useEffect } from "react";
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
  const [isHistoryMode, setIsHistoryMode] = useState(false);
  const [isStreamingMode, setIsStreamingMode] = useState(true);
  const [streamLogs, setStreamLogs] = useState<string[]>([]);
  const [streamStatus, setStreamStatus] = useState<string>("准备就绪");
  const [activeAgent, setActiveAgent] = useState<string>("none");
  const [parseStats, setParseStats] = useState<{ start: Date; end: Date; duration: number } | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [streamLogs]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const projectId = params.get("projectId");
      if (projectId) {
        setIsHistoryMode(true);
        setIsSaved(true); // Since it's from history, it's already saved
        fetch(`http://localhost:8000/api/projects/${projectId}`)
          .then(res => {
            if (!res.ok) throw new Error();
            return res.json();
          })
          .then(data => {
             if(data.data && data.data.analysis_data) {
                setResult(data.data.analysis_data);
                toast.success("已恢复历史项目数据");
             }
          })
          .catch(() => toast.error("恢复历史项目失败"));
      }
    }
  }, []);

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
    setStreamLogs([]);
    setStreamStatus("启动解析引擎...");
    setActiveAgent("none");
    setParseStats(null);

    const startTime = new Date();

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("config", JSON.stringify(config));

      // Always use stream backend to drive agent progress visualization
      const res = await fetch("http://localhost:8000/api/analyze/stream", {
        method: "POST",
        body: formData,
      });

      if (!res.ok || !res.body) throw new Error("流式解析请求失败");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (!line.trim()) continue;
          let parsed;
          try {
            parsed = JSON.parse(line);
          } catch (e) {
             console.error("JSON parse error on stream chunk:", line);
             continue;
          }
          
          if (parsed.status === "info" || parsed.status === "agent1" || parsed.status === "agent2" || parsed.status === "agent3") {
            setStreamStatus(parsed.message);
            setStreamLogs(prev => [...prev, `\n[INFO] ${parsed.message}\n`]);
            if (parsed.status.startsWith("agent")) {
               setActiveAgent(parsed.status);
            }
          } else if (parsed.status === "chunk1" || parsed.status === "chunk2" || parsed.status === "chunk3") {
            setStreamLogs(prev => {
               const newLogs = [...prev];
               if (newLogs.length === 0) {
                   newLogs.push(parsed.text);
               } else {
                   newLogs[newLogs.length - 1] += parsed.text;
               }
               return newLogs;
            });
          } else if (parsed.status === "error") {
            throw new Error(parsed.message);
          } else if (parsed.status === "done") {
            const endTime = new Date();
            setParseStats({
              start: startTime,
              end: endTime,
              duration: (endTime.getTime() - startTime.getTime()) / 1000
            });
            setResult(parsed.data);
            setActiveAgent("done");
            toast.success("解析成功！", { description: "已成功提取实质性条款和文件要求。" });
          }
        }
      }
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
              {isHistoryMode && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                  <strong>提示：当前为历史展示模式。</strong><br />
                  您可直接查看右侧分析结果。若需生成带原格式的 Word 分册或重新解析，请重新选择原始标书文件。
                </div>
              )}
              <div className="space-y-2">
                <Label>选择文件 {isHistoryMode && "(关联源文件)"}</Label>
                <Input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
              </div>
                            <div className="flex items-center justify-between space-x-2 py-2">
                <Label htmlFor="streaming-mode" className="text-sm text-slate-600 font-normal">开启实时流式解析反馈 (开发者模式)</Label>
                <input type="checkbox" id="streaming-mode" checked={isStreamingMode} onChange={(e) => setIsStreamingMode(e.target.checked)} disabled={isAnalyzing} className="w-4 h-4 cursor-pointer accent-primary" />
              </div>
              <Button 
                onClick={handleAnalyze} 
                disabled={isAnalyzing || !file} 
                className="w-full"
                size="lg"
                variant={isHistoryMode ? "secondary" : "default"}
              >
                {isAnalyzing ? "正在智能拆解中..." : (isHistoryMode ? "重新解析覆盖当前项目" : "开始解析")}
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
            <div className="h-full min-max-h-[400px] flex items-center justify-center border-2 border-dashed rounded-xl text-slate-400 p-8 text-center">
              请在左侧上传招标文件并点击解析。
              <br/>注意：长文档可能需要 15-30 秒的 AI 处理时间。
            </div>
          )}

          {isAnalyzing && (
            <div className="h-full min-max-h-[400px] flex flex-col rounded-xl bg-slate-50 border overflow-hidden">
              <div className="p-6 border-b bg-white flex items-center space-x-4">
                <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                <div>
                  <h3 className="font-medium text-slate-800">正在进行智能拆解...</h3>
                  <p className="text-sm text-primary animate-pulse">{streamStatus}</p>
                </div>
              </div>
              {isStreamingMode ? (
                <div className="flex-1 p-4 bg-slate-900 text-green-400 font-mono text-xs overflow-y-auto whitespace-pre-wrap leading-relaxed max-h-[400px]">
                  {streamLogs.map((log, idx) => (
                    <span key={idx}>{log}</span>
                  ))}
                  <span className="animate-pulse">_</span>
                  <div ref={logsEndRef} />
                </div>
              ) : (
                <div className="flex-1 p-8 bg-slate-50 flex flex-col items-center justify-center min-h-[300px]">
                  <div className="flex items-center justify-between w-full max-w-2xl relative">
                    <div className="absolute top-1/2 left-10 right-10 h-1 bg-slate-200 -z-10 -translate-y-1/2 rounded-full"></div>
                    
                    <div className={`flex flex-col items-center space-y-3 bg-white p-6 rounded-2xl shadow-sm border-2 transition-all duration-500 w-1/3 mx-2 ${activeAgent === 'agent1' ? 'border-blue-500 scale-105 shadow-blue-100' : (activeAgent === 'agent3' || activeAgent === 'agent2' || activeAgent === 'done' ? 'border-blue-200' : 'border-slate-100')}`}>
                      <div className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold transition-colors duration-500 ${activeAgent === 'agent1' ? 'bg-blue-500 text-white animate-bounce shadow-lg shadow-blue-200' : (activeAgent === 'agent3' || activeAgent === 'agent2' || activeAgent === 'done' ? 'bg-blue-100 text-blue-500' : 'bg-slate-100 text-slate-400')}`}>
                        1
                      </div>
                      <h4 className="font-bold text-sm text-slate-700 text-center">结构与风险分析</h4>
                      <p className={`text-xs text-center h-4 ${activeAgent === 'agent1' ? 'text-blue-500 font-medium' : 'text-slate-400 opacity-0'}`}>
                        {activeAgent === 'agent1' && "正在阅读全文..."}
                      </p>
                    </div>

                    <div className={`flex flex-col items-center space-y-3 bg-white p-6 rounded-2xl shadow-sm border-2 transition-all duration-500 w-1/3 mx-2 ${activeAgent === 'agent3' ? 'border-purple-500 scale-105 shadow-purple-100' : (activeAgent === 'agent2' || activeAgent === 'done' ? 'border-purple-200' : 'border-slate-100')}`}>
                      <div className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold transition-colors duration-500 ${activeAgent === 'agent3' ? 'bg-purple-500 text-white animate-bounce shadow-lg shadow-purple-200' : (activeAgent === 'agent2' || activeAgent === 'done' ? 'bg-purple-100 text-purple-500' : 'bg-slate-100 text-slate-400')}`}>
                        2
                      </div>
                      <h4 className="font-bold text-sm text-slate-700 text-center">严格质检核验</h4>
                      <p className={`text-xs text-center h-4 ${activeAgent === 'agent3' ? 'text-purple-500 font-medium' : 'text-slate-400 opacity-0'}`}>
                        {activeAgent === 'agent3' && "合并与纠偏..."}
                      </p>
                    </div>

                    <div className={`flex flex-col items-center space-y-3 bg-white p-6 rounded-2xl shadow-sm border-2 transition-all duration-500 w-1/3 mx-2 ${activeAgent === 'agent2' ? 'border-green-500 scale-105 shadow-green-100' : (activeAgent === 'done' ? 'border-green-200' : 'border-slate-100')}`}>
                      <div className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold transition-colors duration-500 ${activeAgent === 'agent2' ? 'bg-green-500 text-white animate-bounce shadow-lg shadow-green-200' : (activeAgent === 'done' ? 'bg-green-100 text-green-500' : 'bg-slate-100 text-slate-400')}`}>
                        3
                      </div>
                      <h4 className="font-bold text-sm text-slate-700 text-center">模板特征词提取</h4>
                      <p className={`text-xs text-center h-4 ${activeAgent === 'agent2' ? 'text-green-500 font-medium' : 'text-slate-400 opacity-0'}`}>
                        {activeAgent === 'agent2' && "寻找模板文本..."}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Parse Stats */}
              {parseStats && (
                <div className="flex items-center justify-between bg-green-50 text-green-700 text-sm px-4 py-2 rounded-lg border border-green-200">
                  <div className="flex space-x-4">
                    <span>开始: {parseStats.start.toLocaleTimeString()}</span>
                    <span>结束: {parseStats.end.toLocaleTimeString()}</span>
                  </div>
                  <div className="font-semibold">
                    总耗时: {parseStats.duration.toFixed(1)} 秒
                  </div>
                </div>
              )}

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
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-red-600 flex items-center gap-2">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
                      致命风险雷达 (必须全部确认)
                    </CardTitle>
                    {result.fatalFlaws.length > 0 && (
                      <button 
                        onClick={() => {
                          const newCheckedState: { [key: string]: boolean } = {};
                          result.fatalFlaws.forEach((cat, cIdx) => {
                            cat.items.forEach((_, iIdx) => {
                              newCheckedState[`${cIdx}-${iIdx}`] = true;
                            });
                          });
                          setCheckedFlaws(newCheckedState);
                        }}
                        className="text-xs bg-red-100 hover:bg-red-200 text-red-700 px-3 py-1.5 rounded-md transition-colors"
                      >
                        一键全选
                      </button>
                    )}
                  </div>
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
                        disabled={!allFlawsChecked || (isHistoryMode && !file && vol.items.some(i => i.template_text))}
                        onClick={() => handleGenerateWord(vidx, vol.volume_name)}
                        className={allFlawsChecked ? "bg-blue-600 hover:bg-blue-700" : ""}
                      >
                        {isHistoryMode && !file && vol.items.some(i => i.template_text) ? "需要关联源文件才能下载" : "下载此分册 (Word)"}
                      </Button>
                    </div>
                    <ul className="grid gap-2 pl-2">
                      {vol.items?.map((item, iidx) => {
                        const isHeading = (item as any).type === "heading";
                        if (isHeading) {
                          return (
                            <li key={iidx} className="flex flex-col text-sm bg-slate-100 border-l-4 border-primary p-3 mt-2 rounded-r-md shadow-sm">
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-slate-900 text-base">{item.name}</span>
                              </div>
                            </li>
                          );
                        }
                        return (
                          <li key={iidx} className="flex flex-col text-sm bg-white border p-3 rounded-md shadow-sm ml-4">
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-slate-700">{item.name}</span>
                              {item.is_required && <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded">必须提供</span>}
                            </div>
                            {item.template_text && item.template_text !== "null" && (
                              <div className="mt-2 text-xs text-green-700 bg-green-50 p-2 rounded">
                                <span className="font-bold">✓ 找到模板特征词：</span>
                                <span className="ml-1 italic">{item.template_text}</span>
                                <p className="text-slate-400 mt-1">生成 Word 时将尝试去原文档中自动切割克隆其格式排版。</p>
                              </div>
                            )}
                          </li>
                        );
                      })}
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
